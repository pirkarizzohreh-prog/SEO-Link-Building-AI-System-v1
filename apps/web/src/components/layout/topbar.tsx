"use client";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

const ROLE_LABEL: Record<string, string> = { admin: "مدیر", editor: "ویرایشگر" };

export function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div />
      <div className="flex items-center gap-3">
        {user && (
          <span className="text-sm text-slate-600">
            {user.name} <span className="text-slate-400">({ROLE_LABEL[user.role] ?? user.role})</span>
          </span>
        )}
        <Button variant="ghost" size="sm" onClick={logout}>
          خروج
        </Button>
      </div>
    </header>
  );
}
