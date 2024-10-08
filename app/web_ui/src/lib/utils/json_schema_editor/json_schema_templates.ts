import { KilnError } from "../error_handlers"

export type JsonSchema = {
  type: "object"
  properties: Record<string, JsonSchemaProperty>
  required: string[]
}

export type JsonSchemaProperty = {
  title: string
  description: string
  type: "number" | "string" | "integer" | "boolean"
}

// We have our own model type.
// Actual JSON schema is too hard to work with in Svelte. It uses dicts, so order would keep moving around as keys change.
export type SchemaModelProperty = {
  title: string
  description: string
  type: "number" | "string" | "integer" | "boolean"
  required: boolean
}
export type SchemaModel = {
  properties: SchemaModelProperty[]
}

export function model_from_schema(s: JsonSchema): SchemaModel {
  return {
    properties: Object.entries(s.properties).map(([name, options]) => ({
      title: name,
      description: options.description,
      type: options.type,
      required: !!s.required.includes(name),
    })),
  }
}

export function title_to_name(title: string): string {
  return title
    .trim()
    .toLowerCase()
    .replace(/ /g, "_")
    .replace(/[^a-z0-9_.]/g, "")
}

export function schema_from_model(m: SchemaModel): JsonSchema {
  for (let i = 0; i < m.properties.length; i++) {
    const title = m.properties[i].title
    if (!title) {
      throw new KilnError("Property is empty. Please provide a name.", null)
    }
    const safe_name = title_to_name(m.properties[i].title)
    if (!safe_name) {
      throw new KilnError(
        "Property name only contains special characters. Must be alphanumeric. Provided name with issues: " +
          m.properties[i].title,
        null,
      )
    }
  }
  return {
    type: "object",
    properties: Object.fromEntries(
      m.properties.map((p) => [
        title_to_name(p.title),
        {
          title: p.title, // Yes we use name and title as the same.
          type: p.type,
          description: p.description,
        },
      ]),
    ),
    required: m.properties
      .filter((p) => p.required)
      .map((p) => title_to_name(p.title)),
  }
}

export const empty_schema_model: SchemaModel = {
  properties: [],
}

export const empty_schema: JsonSchema = schema_from_model(empty_schema_model)
