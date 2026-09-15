"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/", label: "داشبورد" },
  { href: "/projects", label: "پروژه‌ها" },
  { href: "/campaigns", label: "کمپین‌ها" },
  { href: "/blog-platforms", label: "وبلاگ‌های انتشار" },
  { href: "/content-templates", label: "تمپلیت‌های محتوا" },
  { href: "/competitors", label: "رقبا" },
  { href: "/internal-links", label: "لینک‌های داخلی" },
  { href: "/jobs", label: "AI Jobs" },
  { href: "/reports", label: "گزارش‌ها" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-l border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-5 py-4">
        <p className="text-sm font-bold text-slate-900">SEO Link Building AI</p>
        <p className="text-xs text-slate-400">پنل مدیریت</p>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              )}
            >
              {item.label}
            </Link>
          );
        })}
        {user?.role === "admin" && (
          <Link
            href="/users"
            className={cn(
              "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
              pathname.startsWith("/users") ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
            )}
          >
            کاربران
          </Link>
        )}
      </nav>
    </aside>
  );
}
