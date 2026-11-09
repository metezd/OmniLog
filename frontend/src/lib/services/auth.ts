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

function parseErrorMessage(errorData: any, fallback: string): string {
  const detail = errorData?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    const field = first.loc ? first.loc[first.loc.length - 1] : "";
    return field ? `${field}: ${first.msg}` : first.msg;
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

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(parseErrorMessage(result, "Invalid credentials"));
  }

  // Token'ı hem localStorage hem de cookie'ye kaydediyoruz (middleware/proxy ve client erişimi için)
  if (typeof window !== "undefined" && result.access_token) {
    localStorage.setItem("access_token", result.access_token);
    localStorage.setItem("token", result.access_token);
    document.cookie = `access_token=${result.access_token}; path=/; max-age=604800; SameSite=Lax`;
  }

  return result;
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

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(parseErrorMessage(result, "Registration failed"));
  }

  return result;
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
  return response.json();
}