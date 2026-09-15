"use client";

import Link from "next/link";
import { Fragment, use, useState, type FormEvent } from "react";

import { ArticleStatusBadge, StatusBadge, TopicStatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import {
  useAnchors,
  useApproveBrief,
  useApproveTopic,
  useArticles,
  useBrief,
  useCampaign,
  useCreateArticle,
  useCreateBrief,
  useCreateTopic,
  useGenerateArticle,
  useGenerateBrief,
  usePauseCampaign,
  useRejectTopic,
  useResolvedLinkPlacementRule,
  useStartCampaign,
  useTopics,
} from "@/lib/hooks";
import type { Topic } from "@/lib/types";

export default function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const campaignId = Number(id);

  const { data: campaign, isLoading, error } = useCampaign(campaignId);
  const { data: rule } = useResolvedLinkPlacementRule(campaignId);
  const startCampaign = useStartCampaign();
  const pauseCampaign = usePauseCampaign();
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!campaign) return null;

  async function handleStart() {
    setActionError(null);
    try {
      await startCampaign.mutateAsync(campaignId);
    } catch (err) {
      setActionError(getErrorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-slate-900">{campaign.name}</h1>
            <StatusBadge status={campaign.status} />
          </div>
          <p className="text-sm text-slate-500">
            هدف: {campaign.total_links_target} لینک · {campaign.blog_count} وبلاگ · {campaign.duration_days} روز
          </p>
          {rule && (
            <p className="mt-1 text-xs text-slate-400">
              نسبت انکر مؤثر (resolve‌شده از سطح {rule.resolved_from}): Exact {rule.anchor_distribution.exact}٪ ·
              Partial {rule.anchor_distribution.partial}٪ · Semantic {rule.anchor_distribution.semantic}٪ · Brand{" "}
              {rule.anchor_distribution.brand}٪
            </p>
          )}
        </div>
        <div className="flex shrink-0 gap-2">
          {(campaign.status === "planning" || campaign.status === "paused") && (
            <Button size="sm" onClick={handleStart} isLoading={startCampaign.isPending}>
              شروع خودکار با AI (Keyword Intelligence)
            </Button>
          )}
          {campaign.status === "in_progress" && (
            <Button size="sm" variant="secondary" onClick={() => pauseCampaign.mutate(campaignId)}>
              توقف موقت
            </Button>
          )}
        </div>
      </div>
      {actionError && <ErrorBanner message={actionError} />}

      <TopicsSection campaignId={campaignId} targetPageId={campaign.target_page_id} />
      <ArticlesSection campaignId={campaignId} targetPageId={campaign.target_page_id} />
    </div>
  );
}

function TopicsSection({ campaignId, targetPageId }: { campaignId: number; targetPageId: number }) {
  const { data: topics } = useTopics(campaignId);
  const createTopic = useCreateTopic(campaignId);
  const approveTopic = useApproveTopic(campaignId);
  const rejectTopic = useRejectTopic(campaignId);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createTopic.mutateAsync({ title });
      setTitle("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>موضوعات (Stage: Idea)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleCreate} className="flex items-end gap-2">
          <div className="flex-1">
            <Label>موضوع جدید (ثبت دستی — تولید خودکار با AI در Sprint 3)</Label>
            <Input required value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <Button type="submit" size="sm" isLoading={createTopic.isPending}>
            افزودن
          </Button>
        </form>
        {error && <ErrorBanner message={error} />}

        {!topics?.length ? (
          <EmptyState message="هنوز موضوعی ثبت نشده است." />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>عنوان</Th>
                <Th>وضعیت</Th>
                <Th>منبع</Th>
                <Th></Th>
              </Tr>
            </Thead>
            <tbody>
              {topics.map((t) => (
                <Fragment key={t.id}>
                  <Tr>
                    <Td>{t.title}</Td>
                    <Td>
                      <TopicStatusBadge status={t.status} />
                    </Td>
                    <Td>{t.generated_by === "ai" ? "AI" : "دستی"}</Td>
                    <Td>
                      {t.status === "suggested" && (
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => approveTopic.mutate({ id: t.id })}>
                            تأیید
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => rejectTopic.mutate({ id: t.id })}
                          >
                            رد
                          </Button>
                        </div>
                      )}
                    </Td>
                  </Tr>
                  {t.status === "selected" && (
                    <tr className="border-b border-slate-100 last:border-0">
                      <td colSpan={4} className="bg-slate-50 px-4 py-3">
                        <BriefPanel topic={t} targetPageId={targetPageId} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function BriefPanel({ topic, targetPageId }: { topic: Topic; targetPageId: number }) {
  const [polling, setPolling] = useState(false);
  const { data: brief, isLoading } = useBrief(topic.id, true, { poll: polling });
  const createBrief = useCreateBrief(topic.id);
  const approveBrief = useApproveBrief(topic.id);
  const generateBrief = useGenerateBrief(topic.id);
  const [heading, setHeading] = useState("");
  const [keyPoint, setKeyPoint] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setError(null);
    try {
      await generateBrief.mutateAsync();
      setPolling(true);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  if (isLoading) return <Spinner />;

  if (brief) {
    return (
      <div className="text-sm">
        <div className="mb-2 flex items-center gap-2">
          <span className="font-medium text-slate-700">Content Brief (Stage: Brief)</span>
          <StatusBadge status={brief.status} />
          {brief.status === "draft" && (
            <Button size="sm" onClick={() => approveBrief.mutate(brief.id)} isLoading={approveBrief.isPending}>
              تأیید بریف
            </Button>
          )}
        </div>
        <ul className="list-inside list-disc space-y-1 text-slate-600">
          {brief.outline.map((item, i) => (
            <li key={i}>
              <span className="font-medium">{item.heading}</span>
              {item.key_points.length > 0 && ` — ${item.key_points.join("، ")}`}
            </li>
          ))}
        </ul>
        <p className="mt-1 text-xs text-slate-400">تعداد کلمه هدف: {brief.target_word_count}</p>
      </div>
    );
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createBrief.mutateAsync({
        target_page_id: targetPageId,
        outline: [{ heading, level: "h2", key_points: keyPoint ? [keyPoint] : [] }],
        target_word_count: 1200,
      });
      setHeading("");
      setKeyPoint("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <p className="text-xs text-slate-400">هنوز بریفی برای این موضوع ثبت نشده.</p>
        <Button size="sm" onClick={handleGenerate} isLoading={generateBrief.isPending}>
          تولید بریف با AI
        </Button>
        {polling && <span className="text-xs text-slate-400">در حال پردازش توسط Worker...</span>}
      </div>

      <form onSubmit={handleCreate} className="space-y-2">
        <p className="text-xs text-slate-400">یا به‌صورت دستی:</p>
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-48 flex-1">
            <Label>عنوان بخش اول (H2)</Label>
            <Input required value={heading} onChange={(e) => setHeading(e.target.value)} />
          </div>
          <div className="min-w-48 flex-1">
            <Label>نکته کلیدی</Label>
            <Input value={keyPoint} onChange={(e) => setKeyPoint(e.target.value)} />
          </div>
          <Button type="submit" size="sm" variant="secondary" isLoading={createBrief.isPending}>
            ایجاد بریف دستی
          </Button>
        </div>
      </form>
      {error && <ErrorBanner message={error} />}
    </div>
  );
}

function ArticlesSection({ campaignId, targetPageId }: { campaignId: number; targetPageId: number }) {
  const { data: articles } = useArticles(campaignId);
  const { data: topics } = useTopics(campaignId);
  const { data: anchors } = useAnchors(targetPageId);
  const createArticle = useCreateArticle(campaignId);

  const [form, setForm] = useState({ title: "", content: "", topic_id: "", anchor_id: "" });
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  // If the chosen topic already has a brief, attach it — Article Writer's
  // real input is the brief, not just the topic (docs/AI_WORKFLOW.md).
  const { data: selectedTopicBrief } = useBrief(Number(form.topic_id) || 0, !!form.topic_id);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createArticle.mutateAsync({
        title: form.title,
        content: form.content,
        target_page_id: targetPageId,
        anchor_id: Number(form.anchor_id),
        topic_id: form.topic_id ? Number(form.topic_id) : undefined,
        content_brief_id: selectedTopicBrief?.id,
      });
      setForm({ title: "", content: "", topic_id: "", anchor_id: "" });
      setShowForm(false);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  const approvedBriefTopics = (topics ?? []).filter((t) => t.status === "selected");

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <CardTitle>مقالات (Writing → Audit → Human Review → Published)</CardTitle>
        <Button size="sm" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "بستن فرم" : "+ مقاله جدید (دستی)"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {approvedBriefTopics.length > 0 && (
          <div className="space-y-2 rounded-md border border-slate-200 p-3">
            <p className="text-xs font-medium text-slate-600">تولید مقاله با AI از روی بریف تأییدشده:</p>
            {approvedBriefTopics.map((t) => (
              <GenerateArticleRow key={t.id} topic={t} campaignId={campaignId} />
            ))}
          </div>
        )}

        {showForm && (
          <form onSubmit={handleCreate} className="space-y-3 rounded-md border border-slate-200 p-4">
            <p className="text-xs text-slate-400">
              ثبت دستی برای تست/fallback — برای تولید خودکار با AI، از بخش بالا (روی یک بریف تأییدشده) استفاده کنید.
            </p>
            <div>
              <Label>عنوان</Label>
              <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div>
              <Label>موضوع مرتبط (اختیاری)</Label>
              <Select value={form.topic_id} onChange={(e) => setForm({ ...form, topic_id: e.target.value })}>
                <option value="">بدون موضوع</option>
                {topics?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>انکر</Label>
              <Select
                required
                value={form.anchor_id}
                onChange={(e) => setForm({ ...form, anchor_id: e.target.value })}
              >
                <option value="">انتخاب کنید...</option>
                {anchors?.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.anchor_text} ({a.anchor_type})
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>محتوا</Label>
              <Textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
            </div>
            {error && <ErrorBanner message={error} />}
            <Button type="submit" size="sm" isLoading={createArticle.isPending}>
              ایجاد
            </Button>
          </form>
        )}

        {!articles?.length ? (
          <EmptyState message="هنوز مقاله‌ای ثبت نشده است." />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>عنوان</Th>
                <Th>وضعیت</Th>
                <Th>تأیید انسانی</Th>
              </Tr>
            </Thead>
            <tbody>
              {articles.map((a) => (
                <Tr key={a.id}>
                  <Td>
                    <Link href={`/articles/${a.id}`} className="font-medium text-slate-900 hover:underline">
                      {a.title}
                    </Link>
                  </Td>
                  <Td>
                    <ArticleStatusBadge status={a.status} />
                  </Td>
                  <Td>{a.human_approved ? "✅" : "—"}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function GenerateArticleRow({ topic, campaignId }: { topic: Topic; campaignId: number }) {
  const { data: brief } = useBrief(topic.id, true);
  const generateArticle = useGenerateArticle(campaignId);
  const [triggered, setTriggered] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!brief || brief.status !== "approved") return null;

  async function handleGenerate() {
    setError(null);
    try {
      await generateArticle.mutateAsync(brief!.id);
      setTriggered(true);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="flex-1 truncate">{topic.title}</span>
      <Button size="sm" onClick={handleGenerate} isLoading={generateArticle.isPending} disabled={triggered}>
        {triggered ? "در صف پردازش..." : "تولید مقاله با AI"}
      </Button>
      {error && <ErrorBanner message={error} />}
    </div>
  );
}
