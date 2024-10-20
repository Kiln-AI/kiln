import createClient from "openapi-fetch"
import type { paths } from "./api_schema"

export const client = createClient<paths>({
  baseUrl: "http://localhost:8757",
})
