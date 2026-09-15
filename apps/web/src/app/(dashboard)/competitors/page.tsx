"use client";

import { useState, type FormEvent } from "react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select } from "@/components/ui/input";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import {
  useAnalyzeCompetitorPage,
  useCompetitorPages,
  useCompetitors,
  useContentGaps,
  useCreateCompetitor,
  useCreateCompetitorPage,
  useProjects,
  useTargetPages,
} from "@/lib/hooks";
import type { Competitor } from "@/lib/types";

export default function CompetitorsPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Competitor Intelligence</h1>
        <p className="text-sm text-slate-500">
          ثبت رقبا و صفحات آن‌ها، تحلیل خودکار با AI، و استخراج Content Gap — docs/AI_WORKFLOW.md.
        </p>
      </div>

      <div className="max-w-xs">
        <Label>پروژه</Label>
        <Select
          value={projectId ?? ""}
          onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">انتخاب پروژه...</option>
          {projects?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.project_name}
            </option>
          ))}
        </Select>
      </div>

      {projectId && <CompetitorsForProject projectId={projectId} />}
    </div>
  );
}

function CompetitorsForProject({ projectId }: { projectId: number }) {
  const { data: competitors, isLoading, error } = useCompetitors(projectId);
  const { data: targetPages } = useTargetPages(projectId);
  const createCompetitor = useCreateCompetitor(projectId);
  const [form, setForm] = useState({ name: "", website_url: "" });
  const [formError, setFormError] = useState<string | null>(null);
  const [gapsTargetPageId, setGapsTargetPageId] = useState<number | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    try {
      await createCompetitor.mutateAsync(form);
      setForm({ name: "", website_url: "" });
    } catch (err) {
      setFormError(getErrorMessage(err));
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>رقبای ثبت‌شده</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
            <div className="min-w-48 flex-1">
              <Label>نام رقیب</Label>
              <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="min-w-64 flex-1">
              <Label>وب‌سایت</Label>
              <Input
                required
                type="url"
                value={form.website_url}
                onChange={(e) => setForm({ ...form, website_url: e.target.value })}
              />
            </div>
            <Button type="submit" size="sm" isLoading={createCompetitor.isPending}>
              افزودن
            </Button>
          </form>
          {formError && <ErrorBanner message={formError} />}

          {isLoading && <Spinner />}
          {error && <ErrorBanner message={getErrorMessage(error)} />}
          {competitors && competitors.length === 0 && <EmptyState message="هنوز رقیبی ثبت نشده است." />}

          {competitors?.map((c) => (
            <CompetitorCard key={c.id} competitor={c} targetPages={targetPages ?? []} />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Content Gaps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="max-w-xs">
            <Label>صفحه هدف</Label>
            <Select
              value={gapsTargetPageId ?? ""}
              onChange={(e) => setGapsTargetPageId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">انتخاب کنید...</option>
              {targetPages?.map((tp) => (
                <option key={tp.id} value={tp.id}>
                  {tp.title}
                </option>
              ))}
            </Select>
          </div>
          {gapsTargetPageId && <ContentGapsList targetPageId={gapsTargetPageId} />}
        </CardContent>
      </Card>
    </div>
  );
}

function CompetitorCard({
  competitor,
  targetPages,
}: {
  competitor: Competitor;
  targetPages: { id: number; title: string }[];
}) {
  const { data: pages } = useCompetitorPages(competitor.id);
  const createPage = useCreateCompetitorPage(competitor.id);
  const analyzePage = useAnalyzeCompetitorPage(competitor.id);
  const [pageForm, setPageForm] = useState({ url: "", target_page_id: "" });
  const [error, setError] = useState<string | null>(null);

  async function handleAddPage(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createPage.mutateAsync({
        url: pageForm.url,
        target_page_id: pageForm.target_page_id ? Number(pageForm.target_page_id) : undefined,
      });
      setPageForm({ url: "", target_page_id: "" });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleAnalyze(pageId: number) {
    setError(null);
    try {
      await analyzePage.mutateAsync(pageId);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div className="rounded-md border border-slate-200 p-3">
      <p className="font-medium text-slate-900">{competitor.name}</p>
      <p className="mb-2 text-xs text-slate-400">{competitor.website_url}</p>

      <form onSubmit={handleAddPage} className="flex flex-wrap items-end gap-2">
        <div className="min-w-56 flex-1">
          <Label>URL صفحه رقیب</Label>
          <Input
            required
            type="url"
            value={pageForm.url}
            onChange={(e) => setPageForm({ ...pageForm, url: e.target.value })}
          />
        </div>
        <div className="min-w-40">
          <Label>صفحه هدف مرتبط</Label>
          <Select
            value={pageForm.target_page_id}
            onChange={(e) => setPageForm({ ...pageForm, target_page_id: e.target.value })}
          >
            <option value="">انتخاب کنید...</option>
            {targetPages.map((tp) => (
              <option key={tp.id} value={tp.id}>
                {tp.title}
              </option>
            ))}
          </Select>
        </div>
        <Button type="submit" size="sm" variant="secondary" isLoading={createPage.isPending}>
          افزودن صفحه
        </Button>
      </form>
      {error && <ErrorBanner message={error} />}

      {pages && pages.length > 0 && (
        <ul className="mt-3 space-y-2 text-sm">
          {pages.map((p) => (
            <li key={p.id} className="flex items-center gap-2">
              <span className="flex-1 truncate">{p.fetched_title || p.url}</span>
              {p.analyzed_at ? (
                <span className="text-xs text-emerald-600">تحلیل‌شده ({p.fetched_word_count} کلمه)</span>
              ) : (
                <Button
                  size="sm"
                  onClick={() => handleAnalyze(p.id)}
                  isLoading={analyzePage.isPending}
                  disabled={!p.target_page_id}
                  title={!p.target_page_id ? "ابتدا صفحه هدف مرتبط را مشخص کنید" : undefined}
                >
                  تحلیل با AI
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ContentGapsList({ targetPageId }: { targetPageId: number }) {
  const { data: gaps, isLoading } = useContentGaps(targetPageId);

  if (isLoading) return <Spinner />;
  if (!gaps?.length) return <EmptyState message="هنوز خلأ محتوایی‌ای برای این صفحه شناسایی نشده است." />;

  return (
    <Table>
      <Thead>
        <Tr>
          <Th>موضوع خلأ</Th>
          <Th>نوع</Th>
          <Th>وضعیت</Th>
        </Tr>
      </Thead>
      <tbody>
        {gaps.map((g) => (
          <Tr key={g.id}>
            <Td>{g.gap_topic}</Td>
            <Td>{g.gap_type}</Td>
            <Td>
              <StatusBadge status={g.status} />
            </Td>
          </Tr>
        ))}
      </tbody>
    </Table>
  );
}
