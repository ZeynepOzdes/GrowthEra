import { apiRequest, TOKEN_STORAGE_KEY } from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
} from "../types/auth";

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export async function registerUser(
  data: RegisterRequest
): Promise<UserResponse> {
  return apiRequest<UserResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
    auth: false,
  });
}

export async function loginUser(data: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
    auth: false,
  });
}

export async function getCurrentUser(): Promise<UserResponse> {
  return apiRequest<UserResponse>("/users/me");
}