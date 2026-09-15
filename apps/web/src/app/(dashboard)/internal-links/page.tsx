"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Label, Select } from "@/components/ui/input";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import {
  useAnalyzeInternalLinks,
  useApplySuggestion,
  useDismissSuggestion,
  useInternalLinkSuggestions,
  useProjects,
} from "@/lib/hooks";

export default function InternalLinksPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-900">پیشنهادهای لینک‌دهی داخلی</h1>
        <p className="text-sm text-slate-500">
          مستقل از پایپ‌لاین گست‌پست — برای بهبود ساختار لینک‌دهی داخلی سایت پروژه (docs/AI_WORKFLOW.md).
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
  const analyze = useAnalyzeInternalLinks(projectId);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  async function handleAnalyze() {
    setAnalyzeError(null);
    try {
      await analyze.mutateAsync();
    } catch (err) {
      setAnalyzeError(getErrorMessage(err));
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button size="sm" onClick={handleAnalyze} isLoading={analyze.isPending}>
          تحلیل لینک‌های داخلی با AI
        </Button>
        <span className="text-xs text-slate-400">
          نتیجه پس از پردازش توسط Worker در همین لیست ظاهر می‌شود — صفحه AI Jobs را برای وضعیت ببینید.
        </span>
      </div>
      {analyzeError && <ErrorBanner message={analyzeError} />}

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}
      {!isLoading && !suggestions?.length && <EmptyState message="هنوز پیشنهادی برای این پروژه ثبت نشده است." />}

      {suggestions && suggestions.length > 0 && (
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
      )}
    </div>
  );
}
