import type { LoginPayload, RegisterPayload, User } from "@/types/user";

const MOCK_DELAY_MS = 600;

const wait = (ms: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms));

// Mock implementation used until the backend auth endpoints exist.
// Replace each body with an Axios call, e.g. api.post<User>("/auth/login", payload).
export async function login(payload: LoginPayload): Promise<User> {
  await wait(MOCK_DELAY_MS);
  return {
    id: 1,
    email: payload.email,
    username: payload.email.split("@")[0],
    createdAt: new Date().toISOString(),
  };
}

export async function register(payload: RegisterPayload): Promise<User> {
  await wait(MOCK_DELAY_MS);
  return {
    id: 1,
    email: payload.email,
    username: payload.username,
    createdAt: new Date().toISOString(),
  };
}