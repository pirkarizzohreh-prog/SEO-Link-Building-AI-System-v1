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
  useBlogPlatforms,
  usePublications,
  usePublishArticle,
  usePublishPackage,
  useRejectArticle,
  useSeoAuditResults,
} from "@/lib/hooks";

export default function ArticleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const articleId = Number(id);

  const { data: article, isLoading, error } = useArticle(articleId);
  const { data: auditResults } = useSeoAuditResults(articleId);
  const { data: publications } = usePublications(articleId);
  const approve = useApproveArticle(articleId);
  const reject = useRejectArticle(articleId);
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!article) return null;

  const canDecide = article.status === "reviewed" || article.status === "needs_human_review" || article.status === "draft";

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

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900">{article.title}</h1>
          <div className="mt-1 flex items-center gap-2">
            <ArticleStatusBadge status={article.status} />
            {article.human_approved && (
              <span className="text-xs font-medium text-emerald-600">✅ تأیید انسانی ثبت شده</span>
            )}
          </div>
        </div>

        {canDecide && !article.human_approved && (
          <div className="flex shrink-0 gap-2">
            <Button size="sm" onClick={handleApprove} isLoading={approve.isPending}>
              تأیید (Human Approval)
            </Button>
            <Button size="sm" variant="danger" onClick={handleReject} isLoading={reject.isPending}>
              رد
            </Button>
          </div>
        )}
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
          {!auditResults?.length ? (
            <EmptyState message="هنوز ممیزی‌ای ثبت نشده (SEO Auditor Agent در Sprint 4 اضافه می‌شود)." />
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
  const [blogPlatformId, setBlogPlatformId] = useState("");
  const [publishedUrl, setPublishedUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

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
        {error && <ErrorBanner message={error} />}
      </CardContent>
    </Card>
  );
}
