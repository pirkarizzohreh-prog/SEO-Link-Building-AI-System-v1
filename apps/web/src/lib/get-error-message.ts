import { ApiError } from "@/lib/api-client";

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    if (Array.isArray(error.detail)) {
      // FastAPI/pydantic validation error format.
      return error.detail
        .map((e: { msg?: string; loc?: unknown[] }) => e.msg ?? JSON.stringify(e))
        .join("، ");
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "خطای غیرمنتظره‌ای رخ داد.";
}
