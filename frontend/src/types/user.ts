// Draft user types. Align with the FastAPI user schemas once confirmed.

export interface User {
  id: number;
  email: string;
  username: string;
  createdAt: string; // ISO 8601
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
}