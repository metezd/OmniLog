import axios from "axios";

// Axios istemcisini doğrudan buraya kuruyoruz ki import hatası hiç yaşanmasın
const api = axios.create({
  baseURL: "http://localhost:8000", // Backend adresin
  headers: {
    "Content-Type": "application/json",
  },
});

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export async function login(data: LoginPayload) {
  const formData = new URLSearchParams();
  formData.append("username", data.username);
  formData.append("password", data.password);

  const response = await api.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

export async function register(data: RegisterPayload) {
  const response = await api.post("/auth/register", data);
  return response.data;
}