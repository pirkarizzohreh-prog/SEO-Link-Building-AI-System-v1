"use client";

import { use, useState, type FormEvent } from "react";

import { ArticleStatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/get-error-message";
import {
  useApproveArticle,
  useArticle,
  useArticleStatusHistory,
  useBlogPlatforms,
  usePublications,
  usePublishArticle,
  usePublishPackage,
  useRejectArticle,
  useRunAudit,
  useRunAutomatedPublish,
  useSeoAuditResults,
} from "@/lib/hooks";

const STAGE_LABEL: Record<string, string> = {
  idea: "Idea",
  brief: "Brief",
  writing: "Writing",
  audit: "Audit",
  human_review: "Human Review",
  published: "Published",
  rejected: "Rejected",
};

export default function ArticleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const articleId = Number(id);

  const { data: article, isLoading, error } = useArticle(articleId);
  const isAuditing = article?.status === "in_audit";
  const { data: auditResults } = useSeoAuditResults(articleId, isAuditing);
  const { data: publications } = usePublications(articleId);
  const { data: statusHistory } = useArticleStatusHistory(articleId);
  const approve = useApproveArticle(articleId);
  const reject = useRejectArticle(articleId);
  const runAudit = useRunAudit(articleId);
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!article) return null;

  const canDecide = article.status === "reviewed" || article.status === "needs_human_review" || article.status === "draft";
  const canAudit = article.status === "draft" || article.status === "needs_human_review";

  async function handleApprove() {
    setActionError(null);
    try {
      await approve.mutateAsync(undefined);
    } catch (err) {
      setActionError(getErrorMessage(err));
    }
  }

  async function handleReject() {
    setActionError(null);
    try {
      await reject.mutateAsync(undefined);
    } catch (err) {
      setActionError(getErrorMessage(err));
    }
  }

  async function handleRunAudit() {
    setActionError(null);
    try {
      await runAudit.mutateAsync();
    } catch (err) {
      setActionError(getErrorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900">{article.title}</h1>
          <div className="mt-1 flex items-center gap-2">
            <ArticleStatusBadge status={article.status} />
            {article.audit_retry_count > 0 && (
              <span className="text-xs text-slate-400">
                (بازنویسی شده توسط SEO Auditor: {article.audit_retry_count} بار)
              </span>
            )}
            {article.human_approved && (
              <span className="text-xs font-medium text-emerald-600">✅ تأیید انسانی ثبت شده</span>
            )}
          </div>
        </div>

        <div className="flex shrink-0 gap-2">
          {canAudit && (
            <Button size="sm" variant="secondary" onClick={handleRunAudit} isLoading={runAudit.isPending}>
              اجرای ممیزی SEO
            </Button>
          )}
          {canDecide && !article.human_approved && (
            <>
              <Button size="sm" onClick={handleApprove} isLoading={approve.isPending}>
                تأیید (Human Approval)
              </Button>
              <Button size="sm" variant="danger" onClick={handleReject} isLoading={reject.isPending}>
                رد
              </Button>
            </>
          )}
        </div>
      </div>
      {actionError && <ErrorBanner message={actionError} />}

      <Card>
        <CardHeader>
          <CardTitle>محتوا</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">
            {article.content || "بدون محتوا"}
          </p>
          {article.word_count != null && (
            <p className="mt-3 text-xs text-slate-400">تعداد کلمات: {article.word_count}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>نتایج ممیزی SEO</CardTitle>
        </CardHeader>
        <CardContent>
          {isAuditing ? (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Spinner /> در حال اجرای SEO Auditor Agent (شامل تا ۲ بازنویسی خودکار در صورت نیاز)...
            </div>
          ) : !auditResults?.length ? (
            <EmptyState message="هنوز ممیزی‌ای برای این مقاله اجرا نشده است." />
          ) : (
            <ul className="space-y-1 text-sm">
              {auditResults.map((r) => (
                <li key={r.id} className="flex items-center gap-2">
                  <span>{r.passed ? "✅" : "❌"}</span>
                  <span className="font-medium">{r.check_name}</span>
                  {r.details && <span className="text-slate-400">— {r.details}</span>}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <PublishCard articleId={articleId} humanApproved={article.human_approved} published={article.status === "published"} />

      <Card>
        <CardHeader>
          <CardTitle>تاریخچه انتشار</CardTitle>
        </CardHeader>
        <CardContent>
          {!publications?.length ? (
            <EmptyState message="هنوز منتشر نشده است." />
          ) : (
            <ul className="space-y-2 text-sm">
              {publications.map((p) => (
                <li key={p.id}>
                  <a href={p.published_url ?? "#"} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                    {p.published_url}
                  </a>{" "}
                  <span className="text-slate-400">({p.method === "manual" ? "دستی" : "خودکار"})</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>تاریخچه مراحل (Pipeline)</CardTitle>
        </CardHeader>
        <CardContent>
          {!statusHistory?.length ? (
            <EmptyState message="هنوز رکوردی در تاریخچه‌ی این مقاله ثبت نشده است." />
          ) : (
            <ul className="space-y-1 text-sm">
              {statusHistory.map((h) => (
                <li key={h.id} className="flex items-center gap-2">
                  <span className="font-medium text-slate-800">{STAGE_LABEL[h.stage] ?? h.stage}</span>
                  <span className="text-slate-400">
                    {h.from_status ?? "—"} → {h.to_status}
                  </span>
                  <span className="text-xs text-slate-400">
                    ({h.actor_type === "ai" ? "AI" : "کاربر"} · {new Date(h.created_at).toLocaleString("fa-IR")})
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PublishCard({
  articleId,
  humanApproved,
  published,
}: {
  articleId: number;
  humanApproved: boolean;
  published: boolean;
}) {
  const { data: pkg } = usePublishPackage(articleId, humanApproved && !published);
  const { data: blogPlatforms } = useBlogPlatforms();
  const publish = usePublishArticle(articleId);
  const runAutomatedPublish = useRunAutomatedPublish(articleId);
  const [blogPlatformId, setBlogPlatformId] = useState("");
  const [automatedBlogPlatformId, setAutomatedBlogPlatformId] = useState("");
  const [publishedUrl, setPublishedUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [automatedNotice, setAutomatedNotice] = useState<string | null>(null);

  if (published) return null;

  if (!humanApproved) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>انتشار</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState message="قبل از انتشار باید مقاله تأیید انسانی (Human Approval) شود." />
        </CardContent>
      </Card>
    );
  }

  async function handlePublish(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await publish.mutateAsync({ blog_platform_id: Number(blogPlatformId), published_url: publishedUrl });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleAutomatedPublish(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setAutomatedNotice(null);
    try {
      await runAutomatedPublish.mutateAsync(automatedBlogPlatformId ? Number(automatedBlogPlatformId) : undefined);
      setAutomatedNotice("درخواست ثبت شد — نتیجه پس از پردازش توسط Worker در صفحه AI Jobs و تاریخچه انتشار این مقاله ظاهر می‌شود.");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>انتشار (Publication Manager — نسخه دستی)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {pkg && (
          <div className="rounded-md bg-slate-50 p-3 text-sm">
            <p>
              <span className="font-medium">وبلاگ پیشنهادی:</span>{" "}
              {pkg.suggested_blog_platform_name ?? "—"}
            </p>
            <p>
              <span className="font-medium">انکر:</span> {pkg.anchor_text}
            </p>
            <p>
              <span className="font-medium">لینک هدف:</span> {pkg.target_url}
            </p>
          </div>
        )}

        <form onSubmit={handlePublish} className="flex flex-wrap items-end gap-2">
          <div className="min-w-48">
            <Label>وبلاگ</Label>
            <Select required value={blogPlatformId} onChange={(e) => setBlogPlatformId(e.target.value)}>
              <option value="">انتخاب کنید...</option>
              {blogPlatforms?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="min-w-64 flex-1">
            <Label>URL نهایی منتشرشده</Label>
            <Input
              required
              type="url"
              value={publishedUrl}
              onChange={(e) => setPublishedUrl(e.target.value)}
            />
          </div>
          <Button type="submit" isLoading={publish.isPending}>
            ثبت انتشار
          </Button>
        </form>

        <div className="border-t border-slate-100 pt-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">انتشار خودکار (Playwright — Sprint 5)</h3>
          <form onSubmit={handleAutomatedPublish} className="flex flex-wrap items-end gap-2">
            <div className="min-w-48">
              <Label>وبلاگ (اختیاری — در صورت خالی بودن، خودکار انتخاب می‌شود)</Label>
              <Select value={automatedBlogPlatformId} onChange={(e) => setAutomatedBlogPlatformId(e.target.value)}>
                <option value="">انتخاب خودکار...</option>
                {blogPlatforms?.map((b) => (
                  <option key={b.id} value={b.id} disabled={!b.has_automation_credentials}>
                    {b.name} {b.has_automation_credentials ? "" : "(بدون اطلاعات ورود)"}
                  </option>
                ))}
              </Select>
            </div>
            <Button type="submit" variant="secondary" isLoading={runAutomatedPublish.isPending}>
              انتشار خودکار با AI
            </Button>
          </form>
          {automatedNotice && <p className="mt-2 text-xs text-emerald-600">{automatedNotice}</p>}
          <p className="mt-2 text-xs text-slate-400">
            نیازمند وبلاگی با اطلاعات ورود تنظیم‌شده (صفحه «وبلاگ‌های انتشار» ← «تنظیم اطلاعات ورود»).
          </p>
        </div>

        {error && <ErrorBanner message={error} />}
      </CardContent>
    </Card>
  );
}
