import pytest
from kiln_ai.datamodel.json_schema import JsonObjectSchema, schema_from_json_str
from pydantic import BaseModel


class ExampleModel(BaseModel):
    x_schema: JsonObjectSchema | None = None


json_joke_schema = """{
  "type": "object",
  "properties": {
    "setup": {
      "description": "The setup of the joke",
      "title": "Setup",
      "type": "string"
    },
    "punchline": {
      "description": "The punchline to the joke",
      "title": "Punchline",
      "type": "string"
    },
    "rating": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "How funny the joke is, from 1 to 10",
      "title": "Rating"
    }
  },
  "required": [
    "setup",
    "punchline"
  ]
}
"""


def test_json_schema():
    o = ExampleModel(x_schema=json_joke_schema)
    parsed_schema = schema_from_json_str(o.x_schema)
    assert parsed_schema is not None
    assert parsed_schema["type"] == "object"
    assert parsed_schema["required"] == ["setup", "punchline"]
    assert parsed_schema["properties"]["setup"]["type"] == "string"
    assert parsed_schema["properties"]["punchline"]["type"] == "string"
    assert parsed_schema["properties"]["rating"] is not None

    # Not json schema
    with pytest.raises(ValueError):
        o = ExampleModel(x_schema="hello")
    with pytest.raises(ValueError):
        o = ExampleModel(x_schema="{'asdf':{}}")
    with pytest.raises(ValueError):
        o = ExampleModel(x_schema="{asdf")
