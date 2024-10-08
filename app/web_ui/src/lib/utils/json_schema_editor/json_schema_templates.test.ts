import {
  title_to_name,
  schema_from_model,
  model_from_schema,
} from "./json_schema_templates"
import type { SchemaModel, JsonSchema } from "./json_schema_templates"
import { describe, it, expect } from "vitest"

describe("title_to_name", () => {
  it("converts spaces to underscores", () => {
    expect(title_to_name("Hello World")).toBe("hello_world")
  })

  it("converts to lowercase", () => {
    expect(title_to_name("UPPERCASE")).toBe("uppercase")
  })

  it("removes special characters", () => {
    expect(title_to_name("Special@#$Characters!")).toBe("specialcharacters")
  })

  it("keeps alphanumeric characters, underscores, and dots", () => {
    expect(title_to_name("alpha123_numeric.test")).toBe("alpha123_numeric.test")
  })

  it("handles empty string", () => {
    expect(title_to_name("")).toBe("")
  })

  it("handles string with only special characters", () => {
    expect(title_to_name("@#$%^&*")).toBe("")
  })

  it("handles mixed case and special characters", () => {
    expect(title_to_name("User Name (Display)")).toBe("user_name_display")
  })

  it("handles leading and trailing spaces", () => {
    expect(title_to_name("  Trim Me  ")).toBe("trim_me")
  })
})

describe("schema_from_model", () => {
  it("converts a simple SchemaModel to JsonSchema", () => {
    const model: SchemaModel = {
      properties: [
        {
          title: "User Name",
          description: "The user's full name",
          type: "string",
          required: true,
        },
        {
          title: "Age",
          description: "User's age in years",
          type: "integer",
          required: false,
        },
      ],
    }

    const expected: JsonSchema = {
      type: "object",
      properties: {
        user_name: {
          title: "User Name",
          type: "string",
          description: "The user's full name",
        },
        age: {
          title: "Age",
          type: "integer",
          description: "User's age in years",
        },
      },
      required: ["user_name"],
    }

    expect(schema_from_model(model)).toEqual(expected)
  })

  it("handles empty SchemaModel", () => {
    const model: SchemaModel = {
      properties: [],
    }

    const expected: JsonSchema = {
      type: "object",
      properties: {},
      required: [],
    }

    expect(schema_from_model(model)).toEqual(expected)
  })

  it("correctly handles required fields", () => {
    const model: SchemaModel = {
      properties: [
        {
          title: "Field1",
          description: "Description 1",
          type: "string",
          required: true,
        },
        {
          title: "Field2",
          description: "Description 2",
          type: "number",
          required: false,
        },
        {
          title: "Field3",
          description: "Description 3",
          type: "boolean",
          required: true,
        },
      ],
    }

    const result = schema_from_model(model)
    expect(result.required).toEqual(["field1", "field3"])
  })

  it("correctly converts property titles to names", () => {
    const model: SchemaModel = {
      properties: [
        {
          title: "User Name",
          description: "Full name",
          type: "string",
          required: true,
        },
        {
          title: "Email Address",
          description: "Contact email",
          type: "string",
          required: true,
        },
      ],
    }

    const result = schema_from_model(model)
    expect(Object.keys(result.properties)).toEqual([
      "user_name",
      "email_address",
    ])
  })
})

describe("model_from_schema", () => {
  it("converts a simple JsonSchema to SchemaModel", () => {
    const schema: JsonSchema = {
      type: "object",
      properties: {
        user_name: {
          title: "User Name",
          type: "string",
          description: "The user's full name",
        },
        age: {
          title: "Age",
          type: "integer",
          description: "User's age in years",
        },
      },
      required: ["user_name"],
    }

    const expected: SchemaModel = {
      properties: [
        {
          title: "user_name",
          description: "The user's full name",
          type: "string",
          required: true,
        },
        {
          title: "age",
          description: "User's age in years",
          type: "integer",
          required: false,
        },
      ],
    }

    expect(model_from_schema(schema)).toEqual(expected)
  })

  it("handles empty JsonSchema", () => {
    const schema: JsonSchema = {
      type: "object",
      properties: {},
      required: [],
    }

    const expected: SchemaModel = {
      properties: [],
    }

    expect(model_from_schema(schema)).toEqual(expected)
  })

  it("correctly handles required fields", () => {
    const schema: JsonSchema = {
      type: "object",
      properties: {
        field1: {
          title: "Field1",
          type: "string",
          description: "Description 1",
        },
        field2: {
          title: "Field2",
          type: "number",
          description: "Description 2",
        },
        field3: {
          title: "Field3",
          type: "boolean",
          description: "Description 3",
        },
      },
      required: ["field1", "field3"],
    }

    const result = model_from_schema(schema)
    expect(
      result.properties.filter((p) => p.required).map((p) => p.title),
    ).toEqual(["field1", "field3"])
  })

  it("uses property name as title when title is not provided", () => {
    const schema: JsonSchema = {
      type: "object",
      properties: {
        // @ts-expect-error -- title is missing to test this case
        user_name: {
          type: "string",
          description: "The user's name",
        },
      },
      required: [],
    }

    const result = model_from_schema(schema)
    expect(result.properties[0].title).toBe("user_name")
  })
})
