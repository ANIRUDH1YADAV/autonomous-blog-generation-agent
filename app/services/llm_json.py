import json
import re
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def parse_json_to_model(raw: str, model_cls: type[T]) -> T:
    """
    Extract the first JSON object from a model response and validate it
    against the provided Pydantic model.
    """
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("No JSON object found in model response")

    data = json.loads(match.group())
    return model_cls.model_validate(data)
