"use client";

import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { useCampaigns, useProjects } from "@/lib/hooks";

export default function DashboardHomePage() {
  const { user } = useAuth();
  const { data: projects } = useProjects();
  const { data: campaigns } = useCampaigns();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">خوش آمدید، {user?.name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          خلاصه‌ی وضعیت فعلی. Sprint 3 (AI Agents)، Sprint 4 (SEO Audit + گزارش‌ها) و Sprint 5
          (اتوماسیون) هنوز پیاده‌سازی نشده‌اند — فعلاً همه‌چیز به‌صورت دستی مدیریت می‌شود.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>پروژه‌ها</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-slate-900">{projects?.length ?? "—"}</p>
            <Link href="/projects" className="mt-2 inline-block text-sm text-slate-600 hover:underline">
              مشاهده همه ←
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>کمپین‌ها</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-slate-900">{campaigns?.length ?? "—"}</p>
            <Link href="/campaigns" className="mt-2 inline-block text-sm text-slate-600 hover:underline">
              مشاهده همه ←
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>وضعیت شما</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">{user?.email}</p>
            <p className="text-sm text-slate-400">نقش: {user?.role === "admin" ? "مدیر" : "ویرایشگر"}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
