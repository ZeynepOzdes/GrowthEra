const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
export const TOKEN_STORAGE_KEY = "growthera_access_token";

type ApiRequestOptions = RequestInit & {
  skipAuth?: boolean;
};

function buildValidationMessage(detail: unknown): string {
  if (!Array.isArray(detail)) {
    return "Validation failed.";
  }

  return detail
    .map((item) => {
      if (
        typeof item === "object" &&
        item !== null &&
        "loc" in item &&
        "msg" in item
      ) {
        const errorItem = item as {
          loc: string[];
          msg: string;
        };

        const fieldName = errorItem.loc[errorItem.loc.length - 1];

        return `${fieldName}: ${errorItem.msg}`;
      }

      return "Validation error.";
    })
    .join(" ");
}

export async function apiRequest<T>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);

  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !options.skipAuth) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Request failed.";

    try {
      const errorData = await response.json();

      if (response.status === 422 && errorData.detail) {
        message = buildValidationMessage(errorData.detail);
      } else if (typeof errorData.detail === "string") {
        message = errorData.detail;
      } else if (errorData.detail) {
        message = JSON.stringify(errorData.detail);
      }
    } catch {
      message = response.statusText || message;
    }

    if (response.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);

      if (
        window.location.pathname !== "/login" &&
        window.location.pathname !== "/register"
      ) {
        window.location.href = "/login";
      }
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}