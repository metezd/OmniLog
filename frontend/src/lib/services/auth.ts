const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  username: string;
  created_at: string;
}

interface ValidationErrorItem {
  loc?: Array<string | number>;
  msg?: string;
}

interface ErrorResponseData {
  detail?: string | ValidationErrorItem[] | Record<string, unknown>;
}

function parseErrorMessage(errorData: ErrorResponseData, fallback: string): string {
  const detail = errorData?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    const field = first.loc && first.loc.length > 0 ? String(first.loc[first.loc.length - 1]) : "";
    const msg = first.msg || fallback;
    return field ? `${field}: ${msg}` : msg;
  }
  return JSON.stringify(detail);
}

export async function login(data: LoginPayload): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: data.username,
      password: data.password,
    }),
  });

  const result = (await response.json().catch(() => ({}))) as Partial<TokenResponse> & ErrorResponseData;

  if (!response.ok || !result.access_token) {
    throw new Error(parseErrorMessage(result, "Invalid credentials"));
  }

  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", result.access_token);
    localStorage.setItem("token", result.access_token);
    document.cookie = `access_token=${result.access_token}; path=/; max-age=604800; SameSite=Lax`;
  }

  return {
    access_token: result.access_token,
    token_type: result.token_type || "bearer",
  };
}

export async function register(data: RegisterPayload): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: data.username,
      email: data.email,
      password: data.password,
    }),
  });

  const result = (await response.json().catch(() => ({}))) as Partial<UserResponse> & ErrorResponseData;

  if (!response.ok || !result.id) {
    throw new Error(parseErrorMessage(result, "Registration failed"));
  }

  return result as UserResponse;
}

export async function getCurrentUser(): Promise<UserResponse | null> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (!token) return null;

  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) return null;
  return (await response.json()) as UserResponse;
}