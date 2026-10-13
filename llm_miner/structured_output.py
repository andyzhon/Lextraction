"""Parse structured model replies without treating Markdown labels as data."""

import ast
import json
import re
from typing import Any

from llm_miner.error import StructuredFormatError, TokenLimitError


def parse_structured_output(output: str) -> Any:
    """Accept JSON or legacy Python literals, optionally wrapped in a code fence.

    Only remove wrappers at the edges; backticks and labels inside values must
    survive. An unfinished fenced reply is reported separately from bad data.
    """
    payload = re.sub(r"\A\s*(?:List|Output|JSON)\s*:\s*", "", output,
                     flags=re.IGNORECASE).strip()
    opening = re.match(r"\A(?P<fence>`{3,}|~{3,})[ \t]*(?:json|python)?[ \t]*\r?\n",
                       payload, flags=re.IGNORECASE)
    if opening:
        fence = opening.group("fence")
        body = payload[opening.end():]
        closing = re.search(r"^" + re.escape(fence) + r"[ \t]*$", body,
                            flags=re.MULTILINE)
        if closing is None:
            raise TokenLimitError("Structured response has no closing code fence", output)
        if body[closing.end():].strip():
            raise StructuredFormatError("Unexpected text after structured response", output)
        payload = body[:closing.start()].strip()

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        # Original prompts also use single quotes and Python's None/True/False.
        try:
            return ast.literal_eval(payload)
        except (ValueError, SyntaxError) as error:
            raise StructuredFormatError(error, payload) from error
