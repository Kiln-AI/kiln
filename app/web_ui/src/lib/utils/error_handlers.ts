export class KilnError extends Error {
  private error_messages: string[] | null

  constructor(message: string | null, error_messages: string[] | null) {
    super(message || "Unknown error")
    this.name = "KilnError"
    this.error_messages = error_messages
  }

  getMessage(): string {
    if (this.error_messages && this.error_messages.length > 0) {
      return this.error_messages.join(".\n")
    }
    return this.message
  }

  getErrorMessages(): string[] {
    if (this.error_messages && this.error_messages.length > 0) {
      return this.error_messages
    }
    return [this.getMessage()]
  }
}

export function createKilnError(e: unknown): KilnError {
  if (e instanceof KilnError) {
    return e
  }
  if (
    e &&
    typeof e === "object" &&
    "message" in e &&
    typeof e.message === "string"
  ) {
    return new KilnError("Unexpected error: " + e.message, null)
  }
  if (
    e &&
    typeof e === "object" &&
    "details" in e &&
    typeof e.details === "string"
  ) {
    return new KilnError("Unexpected error: " + e.details, null)
  }
  return new KilnError("Unknown error", null)
}

/**
 * Handles errors from POST requests.
 * @param response The Response object from the fetch request.
 * @throws {KilnError} Throws a KilnError with appropriate error messages.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function api_error_handler(response: Response, json: any) {
  if (response.status == 200) {
    return
  }

  if (json instanceof Object) {
    if (json["message"] == "The string did not match the expected pattern.") {
      throw new KilnError(json.message, [
        "Unexpected response from server: format invalid",
      ])
    }

    if (
      json["message"] ||
      (json["error_messages"] && json["error_messages"].length > 0)
    ) {
      throw new KilnError(json["message"], json["error_messages"])
    }
  }

  throw new KilnError("Unknown error. Status: " + response.status, null)
}
