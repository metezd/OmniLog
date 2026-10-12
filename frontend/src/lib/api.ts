import axios, { AxiosError } from "axios";

// Shared Axios client for all requests to the FastAPI backend.
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

// Extracts a readable message from an unknown error thrown by a request.
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}