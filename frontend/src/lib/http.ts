import type { ApiErrorBody, TokenResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "signos_access_token";
const REFRESH_TOKEN_KEY = "signos_refresh_token";

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// "Remember me" decides WHERE tokens live: localStorage survives browser
// restarts, sessionStorage is cleared when the tab/browser closes. Reads
// check sessionStorage first (the common case for an unremembered session)
// then fall back to localStorage.
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY) ?? window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    window.sessionStorage.getItem(REFRESH_TOKEN_KEY) ?? window.localStorage.getItem(REFRESH_TOKEN_KEY)
  );
}

export function setTokens(tokens: TokenResponse, remember: boolean = true): void {
  const storage = remember ? window.localStorage : window.sessionStorage;
  const other = remember ? window.sessionStorage : window.localStorage;
  storage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  storage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  other.removeItem(ACCESS_TOKEN_KEY);
  other.removeItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Fired when we give up on auth entirely (no/expired refresh token) so the
// auth context can redirect to /login without this module importing React.
type UnauthorizedListener = () => void;
let unauthorizedListener: UnauthorizedListener | null = null;
export function onUnauthorized(listener: UnauthorizedListener): void {
  unauthorizedListener = listener;
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  // Preserve whichever storage the refresh token actually came from, so a
  // refresh never silently "upgrades" an unremembered session to persistent.
  const remembered = window.localStorage.getItem(REFRESH_TOKEN_KEY) !== null;

  const resp = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!resp.ok) {
    clearTokens();
    return null;
  }
  const tokens: TokenResponse = await resp.json();
  setTokens(tokens, remembered);
  return tokens.access_token;
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  // `object` (unlike any Record<string, X>) has no index-signature
  // requirement, so call sites can pass their own named param types
  // (Pagination, etc.) without TS rejecting the assignment or needing a cast.
  params?: object;
  skipAuth?: boolean;
}

function buildUrl(path: string, params?: RequestOptions["params"]): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params as Record<string, unknown>)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function doFetch(path: string, options: RequestOptions, token: string | null) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token && !options.skipAuth) {
    headers.Authorization = `Bearer ${token}`;
  }
  return fetch(buildUrl(path, options.params), {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let token = options.skipAuth ? null : getAccessToken();
  let resp = await doFetch(path, options, token);

  if (resp.status === 401 && !options.skipAuth) {
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }
    token = await refreshPromise;
    if (token) {
      resp = await doFetch(path, options, token);
    } else {
      unauthorizedListener?.();
      throw new ApiError(401, "unauthorized", "Session expired", {});
    }
  }

  if (resp.status === 204) {
    return undefined as T;
  }

  const contentType = resp.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await resp.json() : null;

  if (!resp.ok) {
    const errBody = payload as ApiErrorBody | null;
    const code = errBody?.error?.code ?? "unknown_error";
    const message = errBody?.error?.message ?? resp.statusText;
    const details = errBody?.error?.details ?? {};
    throw new ApiError(resp.status, code, message, details);
  }

  return payload as T;
}
