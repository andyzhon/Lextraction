"""Read paper Markdown into the same elements used by XML/HTML readers."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from llm_miner.parser.base import BaseParser, Metadata
from llm_miner.schema import Paragraph


@dataclass
class MarkdownDocument:
    body: str
    front_matter: Dict[str, Any]
    tokens: List[Any]


class MarkdownParser(BaseParser):
    suffix = ".md"
    parser = "markdown"
    para_tags = []
    table_tags = []
    figure_tags = []

    @staticmethod
    def _engine():
        # Import on demand so existing XML/HTML readers need no new dependencies.
        from markdown_it import MarkdownIt
        from mdit_py_plugins.dollarmath import dollarmath_plugin

        return (MarkdownIt("commonmark", {"html": True})
                .enable(["table", "strikethrough"])
                .use(dollarmath_plugin))

    @classmethod
    def open_file(cls, filepath):
        import yaml

        text = Path(filepath).read_text(encoding="utf-8-sig")
        lines = text.splitlines(keepends=True)
        metadata = {}
        if lines and lines[0].strip() == "---":
            end = next((i for i in range(1, len(lines))
                        if lines[i].strip() in {"---", "..."}), None)
            if end is not None:
                metadata = yaml.safe_load("".join(lines[1:end])) or {}
                if not isinstance(metadata, dict):
                    raise ValueError("Markdown front matter must be a YAML mapping")
                text = "".join(lines[end + 1:])
            elif len(lines) > 1 and re.match(r"\s*[\w -]+:", lines[1]):
                raise ValueError("Markdown YAML front matter has no closing delimiter")
        return MarkdownDocument(text, metadata, cls._engine().parse(text))

    @classmethod
    def _inline_text(cls, children, include_images=True):
        parts = []
        for token in children or []:
            if token.type in {"text", "code_inline"}:
                parts.append(token.content)
            elif token.type in {"softbreak", "hardbreak"}:
                parts.append("\n")
            elif token.type == "math_inline":
                parts.append("$" + token.content + "$")
            elif token.type == "image" and include_images:
                parts.append(cls._inline_text(token.children) or token.content)
            elif token.type == "html_inline":
                if re.match(r"<br\b", token.content, re.I):
                    parts.append("\n")
                elif re.match(r"<img\b", token.content, re.I):
                    if include_images:
                        image = BeautifulSoup(token.content, "html.parser").find("img")
                        parts.append(image.get("alt", ""))
                else:
                    parts.append(BeautifulSoup(token.content, "html.parser").get_text())
        return "".join(parts).strip()

    @staticmethod
    def _caption(text, kind):
        labels = r"(?:Table|表)" if kind == "table" else r"(?:Fig(?:ure)?\.?|图)"
        match = re.match(r"^" + labels + r"\s*(?:S?\d+|[一二三四五六七八九十]+)(?:\s*\([a-z]\))?", text, re.I)
        if not match:
            return False
        # A reference introducing a discussion paragraph is not a caption.
        rest = text[match.end():].lstrip(" .:：")
        return not re.match(
            r"(?:shows?|illustrates?|reveals?|demonstrates?|presents?|compares?|"
            r"indicates?|depicts?|summari[sz]es?|suggests?|displays?|provides?|"
            r"is\s+(?:shown|presented)|给出|显示|表明|说明|展示)\b", rest, re.I)

    @classmethod
    def parsing(cls, document):
        elements = []
        lines = document.body.splitlines(keepends=True)
        tokens = document.tokens

        def add(kind, source, text, table_format=None):
            text = text.strip()
            if kind == "text" and not text:
                return
            # Keep neighbouring prose available for table identity and routing.
            context = {}
            if kind == "table" and elements and elements[-1].type == "text":
                context = {"context_before": elements[-1].clean_text,
                           "context_before_idx": str(elements[-1].idx)}
            # Attach a labelled caption immediately before/after a table or image.
            if kind in {"table", "figure"} and elements:
                previous = elements[-1]
                if previous.type == "text" and cls._caption(previous.clean_text, kind):
                    elements.pop()
                    source = previous.content + "\n\n" + source
                    if table_format == "html":
                        text = ""  # HTML tables still need the existing converter.
                    else:
                        text = previous.clean_text + "\n\n" + text
            elif kind == "text" and elements:
                previous = elements[-1]
                if previous.type in {"table", "figure"} and cls._caption(text, previous.type):
                    previous.content += "\n\n" + source
                    if previous.intermediate_step.get("table_format") != "html":
                        previous.clean_text = (previous.clean_text + "\n\n" + text).strip()
                    return
            steps = {"table_format": table_format} if table_format else {}
            steps.update(context)
            element = Paragraph(idx=len(elements) + 1, type=kind,
                                content=source.strip(), clean_text=text,
                                intermediate_step=steps)
            elements.append(element)
            return element

        i = 0
        while i < len(tokens):
            token = tokens[i]
            source = ("".join(lines[token.map[0]:token.map[1]])
                      if token.map else token.content)
            if token.type == "table_open":
                end = i + 1
                while end < len(tokens) and tokens[end].type != "table_close":
                    end += 1
                add("table", source, source, "markdown")
                i = end + 1
                continue
            if token.type in {"heading_open", "paragraph_open"}:
                inline = tokens[i + 1]
                text = cls._inline_text(inline.children)
                images = [c for c in inline.children or [] if c.type == "image"]
                html_images = [BeautifulSoup(c.content, "html.parser").find("img")
                               for c in inline.children or []
                               if c.type == "html_inline" and re.match(r"<img\b", c.content, re.I)]
                non_image_text = cls._inline_text(inline.children, include_images=False)
                sources = ([image.attrGet("src") for image in images]
                           + [image.get("src") for image in html_images])
                if sources and non_image_text and not cls._caption(non_image_text, "figure"):
                    # Mixed prose/image paragraphs need two independent routes.
                    add("text", source, non_image_text)
                    element = add("figure", "\n\n".join(
                        f"![image]({src})" for src in sources), "image")
                    element.intermediate_step["image_sources"] = sources
                    i += 3
                    continue
                kind = "figure" if sources else "text"
                element = add(kind, source, text)
                if kind == "figure":
                    element.intermediate_step["image_sources"] = sources
                i += 3
                continue
            if token.type in {"fence", "code_block", "math_block", "math_block_label"}:
                # Keep literal code and LaTeX; never reinterpret their tables/headings.
                add("text", source, source if token.type.startswith("math_") else token.content)
            elif token.type == "html_block":
                cls._html_elements(source, add)
            i += 1
        return elements

    @classmethod
    def _html_elements(cls, source, add):
        soup = BeautifulSoup(source, "html.parser")
        for unwanted in soup(["script", "style", "noscript"]):
            unwanted.decompose()
        found = False
        blocks = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li",
                  "table", "figure", "img"]
        for node in soup.find_all(blocks):
            if node.find_parent(blocks):
                continue
            found = True
            if node.name == "table":
                add("table", str(node), "", "html")
            elif node.name == "figure":
                caption = node.find("figcaption")
                element = add("figure", str(node), caption.get_text() if caption else "")
                element.intermediate_step["image_sources"] = [image.get("src") for image in node.find_all("img")]
            elif node.name == "img":
                element = add("figure", str(node), node.get("alt", ""))
                element.intermediate_step["image_sources"] = [node.get("src")]
            else:
                for br in node.find_all("br"):
                    br.replace_with("\n")
                add("text", str(node), node.get_text().strip())
        if not found:
            add("text", source, soup.get_text().strip())

    @classmethod
    def get_metadata(cls, document):
        values = {str(key).lower(): value for key, value in document.front_matter.items()}
        aliases = {"标题": "title", "期刊": "journal", "日期": "date",
                   "作者": "authors", "publication_date": "date", "journal_title": "journal"}
        for key, destination in aliases.items():
            if key in values and destination not in values:
                values[destination] = values[key]

        # Read explicit metadata labels only from the document header. Do not
        # mistake a cited DOI in the bibliography for this paper's DOI.
        title = next((cls._inline_text(document.tokens[i + 1].children)
                      for i, token in enumerate(document.tokens)
                      if token.type == "heading_open" and token.tag == "h1"), None)
        header = []
        names = "doi|title|journal|date|authors?|标题|期刊|日期|作者"
        label_pattern = r"^\s*(" + names + r")\s*[:：]\s*(.+)$"
        for position, token in enumerate(document.tokens):
            if token.type in {"fence", "code_block", "table_open"}:
                break
            if token.type == "heading_open" and token.tag != "h1":
                break
            if token.type == "inline":
                if position and document.tokens[position - 1].type == "heading_open":
                    continue
                text_lines = cls._inline_text(token.children).splitlines()
                if not any(re.match(label_pattern, line, re.I) for line in text_lines):
                    break  # The first prose paragraph marks the end of metadata.
                header.extend((line, token.content) for line in text_lines)
            if len(header) >= 50:
                break
        for line, source in header:
            match = re.match(label_pattern, line, re.I)
            if match:
                key = match.group(1).lower()
                key = aliases.get(key, key)
                if key == "author":
                    key = "authors"
                if not values.get(key):
                    value = match.group(2)
                    if key == "doi":
                        identifier = re.search(r"10\.\d{4,9}/[^\s<>\]\"]+", source)
                        if identifier:
                            value = identifier.group(0).rstrip(".,;")
                            while value.endswith(")") and value.count(")") > value.count("("):
                                value = value[:-1]
                    values[key] = value
        if not values.get("title"):
            values["title"] = title

        def string(value):
            return str(value).strip() if value is not None else None

        doi = string(values.get("doi"))
        if doi:
            doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)", "", doi, flags=re.I)
        authors = values.get("author_list", values.get("authors", values.get("author")))
        if isinstance(authors, str):
            authors = [item.strip() for item in re.split(r"[;；]", authors) if item.strip()]
        elif authors is not None:
            if not isinstance(authors, list):
                authors = [authors]
            authors = [string(item.get("name")) if isinstance(item, dict) else string(item)
                       for item in authors]
            authors = [item for item in authors if item]
        return Metadata(doi=doi, title=string(values.get("title")),
                        journal=string(values.get("journal")), date=string(values.get("date")),
                        author_list=authors)
