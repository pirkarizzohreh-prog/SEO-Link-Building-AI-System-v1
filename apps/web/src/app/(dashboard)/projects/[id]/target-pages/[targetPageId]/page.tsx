"use client";

import { use, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select } from "@/components/ui/input";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import {
  useAnchorDistribution,
  useAnchors,
  useCreateAnchor,
  useCreateKeyword,
  useKeywords,
  useTargetPage,
} from "@/lib/hooks";
import type { AnchorType } from "@/lib/types";

const ANCHOR_TYPE_LABEL: Record<AnchorType, string> = {
  exact: "Exact",
  partial: "Partial",
  semantic: "Semantic",
  brand: "Brand",
};

export default function TargetPageDetailPage({
  params,
}: {
  params: Promise<{ id: string; targetPageId: string }>;
}) {
  const { targetPageId } = use(params);
  const id = Number(targetPageId);

  const { data: targetPage, isLoading, error } = useTargetPage(id);
  const { data: anchors } = useAnchors(id);
  const { data: keywords } = useKeywords(id);
  const { data: distribution } = useAnchorDistribution(id);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!targetPage) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-slate-900">{targetPage.title}</h1>
        <p className="text-sm text-slate-500">{targetPage.url}</p>
        <p className="text-sm text-slate-400">کلیدواژه اصلی: {targetPage.main_keyword}</p>
      </div>

      {distribution && (
        <Card>
          <CardHeader>
            <CardTitle>توزیع انکر (نسبت هدف در برابر واقعی)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 text-center">
              {(["exact", "partial", "semantic", "brand"] as const).map((type) => (
                <div key={type} className="rounded-md bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">{ANCHOR_TYPE_LABEL[type]}</p>
                  <p className="text-lg font-bold text-slate-900">
                    {distribution.actual_ratio[type] ?? 0}%
                  </p>
                  <p className="text-xs text-slate-400">هدف: {distribution.target_ratio[type]}%</p>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-400">
              بر اساس {distribution.window_size} لینک اخیر (پنجره‌ی ۲۰ لینکی)
            </p>
          </CardContent>
        </Card>
      )}

      <AnchorsCard targetPageId={id} anchors={anchors} />
      <KeywordsCard targetPageId={id} keywords={keywords} />
    </div>
  );
}

function AnchorsCard({ targetPageId, anchors }: { targetPageId: number; anchors: ReturnType<typeof useAnchors>["data"] }) {
  const createAnchor = useCreateAnchor(targetPageId);
  const [form, setForm] = useState<{ anchor_text: string; anchor_type: AnchorType }>({
    anchor_text: "",
    anchor_type: "exact",
  });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createAnchor.mutateAsync(form);
      setForm({ anchor_text: "", anchor_type: "exact" });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Anchor Bank</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
          <div className="min-w-56 flex-1">
            <Label>متن انکر</Label>
            <Input
              required
              value={form.anchor_text}
              onChange={(e) => setForm({ ...form, anchor_text: e.target.value })}
            />
          </div>
          <div className="w-40">
            <Label>نوع</Label>
            <Select
              value={form.anchor_type}
              onChange={(e) => setForm({ ...form, anchor_type: e.target.value as AnchorType })}
            >
              {Object.entries(ANCHOR_TYPE_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
          <Button type="submit" size="sm" isLoading={createAnchor.isPending}>
            افزودن
          </Button>
        </form>
        {error && <ErrorBanner message={error} />}

        {!anchors?.length ? (
          <EmptyState message="هنوز انکری ثبت نشده است." />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>متن انکر</Th>
                <Th>نوع</Th>
                <Th>دفعات استفاده</Th>
                <Th>وضعیت</Th>
              </Tr>
            </Thead>
            <tbody>
              {anchors.map((a) => (
                <Tr key={a.id}>
                  <Td>{a.anchor_text}</Td>
                  <Td>{ANCHOR_TYPE_LABEL[a.anchor_type]}</Td>
                  <Td>{a.usage_count}</Td>
                  <Td>{a.is_active ? "فعال" : "غیرفعال"}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function KeywordsCard({ targetPageId, keywords }: { targetPageId: number; keywords: ReturnType<typeof useKeywords>["data"] }) {
  const createKeyword = useCreateKeyword(targetPageId);
  const [keyword, setKeyword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createKeyword.mutateAsync({ keyword, type: "related", source: "manual" });
      setKeyword("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>کلیدواژه‌ها</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex-1">
            <Label>کلیدواژه جدید</Label>
            <Input required value={keyword} onChange={(e) => setKeyword(e.target.value)} />
          </div>
          <Button type="submit" size="sm" isLoading={createKeyword.isPending}>
            افزودن
          </Button>
        </form>
        {error && <ErrorBanner message={error} />}
        {!keywords?.length ? (
          <EmptyState message="هنوز کلیدواژه‌ای ثبت نشده است." />
        ) : (
          <div className="flex flex-wrap gap-2">
            {keywords.map((k) => (
              <span key={k.id} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                {k.keyword}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
