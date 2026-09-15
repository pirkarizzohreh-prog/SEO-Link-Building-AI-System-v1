"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Label, Select } from "@/components/ui/input";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useApplySuggestion, useDismissSuggestion, useInternalLinkSuggestions, useProjects } from "@/lib/hooks";

export default function InternalLinksPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-900">پیشنهادهای لینک‌دهی داخلی</h1>
        <p className="text-sm text-slate-500">
          مستقل از پایپ‌لاین گست‌پست — برای بهبود ساختار لینک‌دهی داخلی سایت پروژه. تولید خودکار پیشنهادها با AI در
          Sprint 3 اضافه می‌شود.
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

      {projectId && <SuggestionsForProject projectId={projectId} />}
    </div>
  );
}

function SuggestionsForProject({ projectId }: { projectId: number }) {
  const { data: suggestions, isLoading, error } = useInternalLinkSuggestions(projectId);
  const apply = useApplySuggestion(projectId);
  const dismiss = useDismissSuggestion(projectId);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!suggestions?.length) return <EmptyState message="هنوز پیشنهادی برای این پروژه ثبت نشده است." />;

  return (
    <Table>
      <Thead>
        <Tr>
          <Th>انکر پیشنهادی</Th>
          <Th>دلیل</Th>
          <Th>وضعیت</Th>
          <Th></Th>
        </Tr>
      </Thead>
      <tbody>
        {suggestions.map((s) => (
          <Tr key={s.id}>
            <Td className="font-medium text-slate-900">{s.suggested_anchor}</Td>
            <Td className="max-w-sm">{s.reason ?? "—"}</Td>
            <Td>
              <StatusBadge status={s.status} />
            </Td>
            <Td>
              {s.status === "suggested" && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => apply.mutate(s.id)}>
                    اعمال شد
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => dismiss.mutate(s.id)}>
                    رد
                  </Button>
                </div>
              )}
            </Td>
          </Tr>
        ))}
      </tbody>
    </Table>
  );
}
