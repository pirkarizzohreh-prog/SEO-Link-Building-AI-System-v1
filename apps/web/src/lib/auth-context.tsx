"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { apiFetch, clearTokens, getAccessToken, setTokens } from "@/lib/api-client";
import type { User } from "@/lib/types";

const ME_QUERY_KEY = ["auth", "me"] as const;

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  // Whether we *think* we're logged in (a token exists in localStorage).
  // Read lazily so this works with SSR (no window on the server).
  const [hasToken, setHasToken] = useState(() => !!getAccessToken());

  const meQuery = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: () => apiFetch<User>("/auth/me"),
    enabled: hasToken,
    retry: false,
  });

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        body: { email, password },
        unauthenticated: true,
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      setHasToken(true);
      const me = await apiFetch<User>("/auth/me");
      queryClient.setQueryData(ME_QUERY_KEY, me);
    },
    [queryClient]
  );

  const logout = useCallback(() => {
    clearTokens();
    setHasToken(false);
    queryClient.removeQueries({ queryKey: ME_QUERY_KEY });
    router.push("/login");
  }, [queryClient, router]);

  // If /auth/me ever comes back an error (expired/invalid token that a
  // refresh couldn't save — see api-client.ts), treat it as logged out
  // rather than staying stuck in a loading state.
  const user = meQuery.isError ? null : (meQuery.data ?? null);
  const isLoading = hasToken && meQuery.isPending;

  return <AuthContext.Provider value={{ user, isLoading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
