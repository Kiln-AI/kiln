import json
from typing import Annotated, Dict

import jsonschema
import jsonschema.exceptions
from pydantic import AfterValidator

JsonObjectSchema = Annotated[
    str,
    AfterValidator(lambda v: _check_json_schema(v)),
]


def _check_json_schema(v: str) -> str:
    # parsing returns needed errors
    schema_from_json_str(v)
    return v


def schema_from_json_str(v: str | None) -> Dict | None:
    if v is None:
        # Allowing None for now, may make this required later
        return None
    try:
        parsed = json.loads(v)
        jsonschema.Draft202012Validator.check_schema(parsed)
        if not isinstance(parsed, dict):
            raise ValueError(f"JSON schema must be a dict, not {type(parsed)}")
        if (
            "type" not in parsed
            or parsed["type"] != "object"
            or "properties" not in parsed
        ):
            raise ValueError(f"JSON schema must be an object with properties: {v}")
        return parsed
    except jsonschema.exceptions.SchemaError as e:
        raise ValueError(f"Invalid JSON schema: {v} \n{e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {v}\n {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error parsing JSON schema: {v}\n {e}")
