"use client";

import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useAiJobs } from "@/lib/hooks";

const STATUS_TONE = {
  pending: "slate",
  running: "blue",
  success: "green",
  failed: "red",
} as const;

const STATUS_LABEL: Record<string, string> = {
  pending: "در صف",
  running: "در حال اجرا",
  success: "موفق",
  failed: "ناموفق",
};

const JOB_TYPE_LABEL: Record<string, string> = {
  keyword_intel: "Keyword Intelligence",
  topic_gen: "Topic Generator",
  competitor_analysis: "Competitor Intelligence",
  brief_generation: "Content Brief Generator",
  article_write: "Article Writer",
  internal_link_suggestion: "Internal Link Suggestion",
  seo_audit: "SEO Auditor",
  publish: "Publish",
  serp_fetch: "SERP Fetch",
};

export default function JobsPage() {
  const { data: jobs, isLoading, error } = useAiJobs();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-900">AI Jobs</h1>
        <p className="text-sm text-slate-500">
          صف کار + لاگ کامل فراخوانی‌های AI (docs/ARCHITECTURE.md). این صفحه هر ۳ ثانیه به‌روزرسانی می‌شود تا وقتی
          چیزی در صف یا در حال اجرا باشد.
        </p>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}
      {jobs && jobs.length === 0 && <EmptyState message="هنوز هیچ Job ای اجرا نشده است." />}

      {jobs && jobs.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <Table>
            <Thead>
              <Tr>
                <Th>نوع</Th>
                <Th>وضعیت</Th>
                <Th>Provider</Th>
                <Th>توکن</Th>
                <Th>هزینه تقریبی</Th>
                <Th>خطا</Th>
              </Tr>
            </Thead>
            <tbody>
              {jobs.map((job) => (
                <Tr key={job.id}>
                  <Td>
                    {JOB_TYPE_LABEL[job.job_type] ?? job.job_type}
                    <span className="ms-1 text-xs text-slate-400">
                      ({job.reference_table}#{job.reference_id})
                    </span>
                  </Td>
                  <Td>
                    <Badge tone={STATUS_TONE[job.status]}>{STATUS_LABEL[job.status]}</Badge>
                  </Td>
                  <Td>{job.provider ?? "—"}</Td>
                  <Td>{job.tokens_used ?? "—"}</Td>
                  <Td>{job.cost_estimate != null ? `$${job.cost_estimate.toFixed(4)}` : "—"}</Td>
                  <Td className="max-w-xs truncate text-red-600">{job.error_message ?? "—"}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
    </div>
  );
}
