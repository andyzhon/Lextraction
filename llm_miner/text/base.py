import regex
from typing import Any, Dict, List, Optional

from langchain.base_language import BaseLanguageModel
from langchain.chains.base import Chain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from llm_miner.text.prompt import PROMPT_TYPE, PROMPT_EXT, FT_TYPE, FT_HUMAN
from llm_miner.schema import Paragraph
from llm_miner.format import Formatter
from llm_miner.error import LangchainError
from llm_miner.pricing import TokenChecker, update_token_checker
from llm_miner.structured_output import parse_structured_output
from llm_miner.validation import normalize_measurements


class TextMiningAgent(Chain):
    type_chain: LLMChain # 属性类型识别
    extract_chain: LLMChain # 具体数据提取
    input_key: str = "element"
    output_key: str = "output"

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]
    
    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]
    
    def _write_log(self, text: str, run_manager):
        run_manager.on_text(f"\n[Property Mining] ", verbose=self.verbose)
        run_manager.on_text(text, verbose=self.verbose, color="yellow")

    def _parse_output(self, output: str) -> Dict[str, str]:
        if regex.search(r"[Ii] do not know", output):
            return [output]
        return parse_structured_output(output)
    
    def _call(
            self,
            inputs: Dict[str, Any],
            run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()

        explanation = self._add_explanation()
        element: Paragraph = inputs[self.input_key]
        token_checker: TokenChecker = inputs.get('token_checker')
        paragraph: str = element.clean_text   # change content -> clean_text

        llm_kwargs = {
            'explanation': explanation,
            'paragraph': paragraph,
        }
        try:
            llm_output = self.type_chain.run( # self.type_chain是一个LLMChain对象，内部绑定了LLM和Prompt
                **llm_kwargs,
                callbacks=callbacks,
                stop=["Paragraph:"]
            )
        except Exception as e:
            element.add_intermediate_step('text-property-type', str(e))
            raise LangchainError(e)
        else:
            element.add_intermediate_step('text-property-type', llm_output)

        if token_checker:
            update_token_checker(
                name_step='text-property-type',
                chain=self.type_chain,
                token_checker=token_checker, 
                llm_kwargs=llm_kwargs, 
                llm_output=llm_output
            )


        property_type = self._parse_output(llm_output)
        self._write_log(str(property_type), _run_manager)

        # 判断第一阶段是否已经输出完整的属性记录
        if (
            isinstance(property_type, list)
            and property_type
            and all(
                isinstance(p, dict)
                and isinstance(p.get("property"), str)
                for p in property_type
            )
        ):
            # 按样品名称组织提取结果
            grouped = {}

            for item in property_type:
                sample = str(item.get("sample") or "unknown")
                prop = item["property"]

                if sample not in grouped:
                    grouped[sample] = {
                        "meta": {
                            "name": sample,
                            "symbol": "",
                            "chemical formula": ""
                        }
                    }

                # 保留数值、单位、测试条件、原文证据
                record = {
                    k: v
                    for k, v in item.items()
                    if k not in ("property", "sample")
                }

                grouped[sample].setdefault(prop, []).append(record)

            # 保存识别出的属性类别
            property_names = list(dict.fromkeys(
                p["property"] for p in property_type
            ))

            element.set_include_properties(property_names)

            # 保存符合 L2M3 数据结构的结果
            output = list(grouped.values())
            element.set_data(output)

            return {"output": output}

        # 保留原来的两阶段处理逻辑
        element.set_include_properties(property_type)
        
        
        if not property_type:
            element.set_data([])
            return {"output": []}

        st_data_string = Formatter.structured_data["meta"] + "\n"
        info_string = ""
        example_string = ""
        prop_string = ""

        for prop in property_type: # 动态生成提取规则
            try:
                st_data = Formatter.structured_data[prop]
                info = Formatter.information.data.get(prop, "")
                example = Formatter.example_text.data.get(prop, "")
            except KeyError:
                self._write_log(f"There are no format for {prop}", _run_manager)
                continue

            st_data_string += f"- {st_data}\n"
            info_string += f"- {info}\n"
            example_string += f"- {example}\n"
            prop_string += f"{prop}, "

        llm_kwargs={
            'prop': prop_string,
            'structured_data': st_data_string,
            'information': info_string,
            'example': example_string,
            'paragraph': paragraph,
        }
        try:
          llm_output = self.extract_chain.run( # 提取具体数据
              **llm_kwargs,
              callbacks=callbacks,
              stop=["Paragraph:"]
          )
        except Exception as e:
            element.add_intermediate_step('text-property-extract', str(e))
            raise LangchainError(e)
        else:
            element.add_intermediate_step('text-property-extract', llm_output)
            
        if token_checker:
            update_token_checker(
                name_step='text-property-extract',
                chain=self.extract_chain,
                token_checker=token_checker, 
                llm_kwargs=llm_kwargs, 
                llm_output=llm_output
            )

        st_output = normalize_measurements(self._parse_output(llm_output))
        self._write_log(f"{st_output}", _run_manager)

        element.set_data([st_output])
        return {"output": st_output}
    
    def _add_explanation(self,) -> str:
        erase_list = [
            "cell_volume",
            "conversion",
            "reaction_yield",
            "chemical_formula",
        ]
        formatter = Formatter
        target_items = list(formatter.explanation.keys())
        target_items = [item for item in target_items if item not in erase_list]
        explained_props = ""
        for item in target_items:
            explained_props += "\n" + f"- {item}: " + formatter.explanation[item].strip()
        return explained_props.strip()

    @classmethod
    def from_llm(
        cls,
        type_llm: BaseLanguageModel,
        extract_llm: BaseLanguageModel,
        *,
        prompt_type: str = PROMPT_TYPE,
        prompt_extract: str = PROMPT_EXT,
        ft_type: str = FT_TYPE,
        ft_human: str = FT_HUMAN,
        **kwargs,
    ) -> Chain:
        
        if type_llm.model_name.startswith('ft:'): # fine-tuned model
            system_prompt = SystemMessagePromptTemplate.from_template(ft_type)
            human_prompt = HumanMessagePromptTemplate.from_template(ft_human)
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_prompt, human_prompt]
            )
            type_chain = LLMChain(
                llm=type_llm,
                prompt=chat_prompt,
            )
        else:
            template_type = PromptTemplate(
                template=prompt_type,
                input_variables=["explanation", "paragraph"],
            )
            type_chain = LLMChain(llm=type_llm, prompt=template_type)

        if extract_llm.model_name.startswith('ft:'): # fine-tuned model
            raise NotImplementedError('Fine-tuning model for extract is not implemented.')
        else:
            template_extract = PromptTemplate(
                template=prompt_extract,
                input_variables=["prop", "structured_data", "information", "example", "paragraph"],
            )
            extract_chain = LLMChain(llm=extract_llm, prompt=template_extract)

        return cls(
            type_chain=type_chain,
            extract_chain=extract_chain,
            **kwargs
        )
