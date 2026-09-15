import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type Tone = "slate" | "green" | "yellow" | "red" | "blue" | "purple";

const toneClasses: Record<Tone, string> = {
  slate: "bg-slate-100 text-slate-700",
  green: "bg-emerald-100 text-emerald-700",
  yellow: "bg-amber-100 text-amber-800",
  red: "bg-red-100 text-red-700",
  blue: "bg-blue-100 text-blue-700",
  purple: "bg-purple-100 text-purple-700",
};

export function Badge({ tone = "slate", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", toneClasses[tone])}>
      {children}
    </span>
  );
}

const ARTICLE_STATUS_TONE: Record<string, Tone> = {
  draft: "slate",
  in_audit: "blue",
  reviewed: "purple",
  needs_human_review: "yellow",
  approved: "green",
  published: "green",
  rejected: "red",
};

const ARTICLE_STATUS_LABEL: Record<string, string> = {
  draft: "پیش‌نویس",
  in_audit: "در حال ممیزی",
  reviewed: "بررسی‌شده",
  needs_human_review: "نیازمند بررسی انسانی",
  approved: "تأییدشده",
  published: "منتشرشده",
  rejected: "ردشده",
};

export function ArticleStatusBadge({ status }: { status: string }) {
  return <Badge tone={ARTICLE_STATUS_TONE[status] ?? "slate"}>{ARTICLE_STATUS_LABEL[status] ?? status}</Badge>;
}

const TOPIC_STATUS_LABEL: Record<string, string> = {
  suggested: "پیشنهادشده",
  selected: "انتخاب‌شده",
  rejected: "ردشده",
};
const TOPIC_STATUS_TONE: Record<string, Tone> = { suggested: "slate", selected: "green", rejected: "red" };

export function TopicStatusBadge({ status }: { status: string }) {
  return <Badge tone={TOPIC_STATUS_TONE[status] ?? "slate"}>{TOPIC_STATUS_LABEL[status] ?? status}</Badge>;
}

const GENERIC_STATUS_LABEL: Record<string, string> = {
  active: "فعال",
  inactive: "غیرفعال",
  planning: "برنامه‌ریزی",
  in_progress: "در حال اجرا",
  completed: "تکمیل‌شده",
  paused: "متوقف‌شده",
  draft: "پیش‌نویس",
  approved: "تأییدشده",
  new: "جدید",
  used_in_topic: "استفاده‌شده",
  ignored: "نادیده‌گرفته‌شده",
  suggested: "پیشنهادشده",
  applied: "اعمال‌شده",
  dismissed: "ردشده",
  success: "موفق",
  failed: "ناموفق",
};
const GENERIC_STATUS_TONE: Record<string, Tone> = {
  active: "green",
  inactive: "slate",
  planning: "slate",
  in_progress: "blue",
  completed: "green",
  paused: "yellow",
  draft: "slate",
  approved: "green",
  new: "blue",
  used_in_topic: "green",
  ignored: "slate",
  suggested: "slate",
  applied: "green",
  dismissed: "slate",
  success: "green",
  failed: "red",
};

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={GENERIC_STATUS_TONE[status] ?? "slate"}>{GENERIC_STATUS_LABEL[status] ?? status}</Badge>;
}
