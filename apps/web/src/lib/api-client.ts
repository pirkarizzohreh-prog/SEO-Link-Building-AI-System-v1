"use client";

// Thin fetch wrapper: attaches the access token, retries exactly once
// through a refresh on 401, and throws ApiError otherwise so callers
// (React Query) can render a real error state.
//
// Tokens live in localStorage. That's a known, documented trade-off for
// an internal-tool MVP (see apps/web/README.md) — an XSS bug could
// exfiltrate them, whereas httpOnly cookies set by a backend-for-frontend
// would not be readable by injected script. Revisit before this app is
// ever exposed to less-trusted users/content.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "seo_lba_access_token";
const REFRESH_TOKEN_KEY = "seo_lba_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  // Coalesce concurrent 401s into a single refresh call.
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (res) => {
        if (!res.ok) return false;
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  /** Skip attaching the Authorization header (login only). */
  unauthenticated?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, unauthenticated = false } = options;

  const doFetch = async (): Promise<Response> => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (!unauthenticated) {
      const token = getAccessToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }
    return fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let response = await doFetch();

  if (response.status === 401 && !unauthenticated) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      response = await doFetch();
    } else {
      clearTokens();
      // A hard redirect, not router.push(): this plain module (not a React
      // component) has no access to Next's router, and any in-flight React
      // Query state for the expired session should be discarded by a full
      // reload rather than kept around post-navigation.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- see comment above
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new ApiError(401, "Session expired");
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    throw new ApiError(response.status, payload?.detail ?? payload ?? response.statusText);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "PUT", body }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
};
