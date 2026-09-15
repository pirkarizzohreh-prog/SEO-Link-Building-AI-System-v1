"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select } from "@/components/ui/input";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useCompetitors, useCreateCompetitor, useProjects } from "@/lib/hooks";

export default function CompetitorsPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Competitor Intelligence</h1>
        <p className="text-sm text-slate-500">
          تحلیل خودکار صفحات رقیب و استخراج Content Gap در Sprint 3 اضافه می‌شود؛ فعلاً فقط ثبت رقبا.
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
  const createCompetitor = useCreateCompetitor(projectId);
  const [form, setForm] = useState({ name: "", website_url: "" });
  const [formError, setFormError] = useState<string | null>(null);

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
        {competitors && competitors.length > 0 && (
          <Table>
            <Thead>
              <Tr>
                <Th>نام</Th>
                <Th>وب‌سایت</Th>
                <Th>یادداشت</Th>
              </Tr>
            </Thead>
            <tbody>
              {competitors.map((c) => (
                <Tr key={c.id}>
                  <Td className="font-medium text-slate-900">{c.name}</Td>
                  <Td className="max-w-xs truncate">{c.website_url}</Td>
                  <Td>{c.notes ?? "—"}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
