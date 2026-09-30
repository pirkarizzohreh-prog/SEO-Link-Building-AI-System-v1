"use client";

import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Label, Select } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/get-error-message";
import { useCampaignReport, useCampaigns, usePipelineStats, useProjectReport, useProjects } from "@/lib/hooks";

const ANCHOR_TYPE_LABEL: Record<string, string> = {
  exact: "دقیق",
  partial: "جزئی",
  semantic: "معنایی",
  brand: "برند",
};

const STAGE_LABEL: Record<string, string> = {
  idea: "Idea",
  brief: "Brief",
  writing: "Writing",
  audit: "Audit",
  human_review: "Human Review",
  published: "Published",
  rejected: "Rejected",
};

export default function ReportsPage() {
  const { data: projects } = useProjects();
  const [projectId, setProjectId] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-slate-900">گزارش‌ها</h1>
        <p className="text-sm text-slate-500">خلاصه پروژه، Anchor Distribution واقعی، نرخ موفقیت ممیزی و Pipeline Bottleneck Report.</p>
      </div>

      <div className="max-w-xs">
        <Label>پروژه</Label>
        <Select value={projectId ?? ""} onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">انتخاب پروژه...</option>
          {projects?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.project_name}
            </option>
          ))}
        </Select>
      </div>

      {projectId && <ProjectReportSection projectId={projectId} />}
    </div>
  );
}

function ProjectReportSection({ projectId }: { projectId: number }) {
  const { data: report, isLoading, error } = useProjectReport(projectId);
  const { data: campaigns } = useCampaigns(projectId);
  const [campaignId, setCampaignId] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}
      {report && (
        <Card>
          <CardHeader>
            <CardTitle>خلاصه پروژه: {report.project_name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="صفحات هدف" value={report.total_target_pages} />
              <Stat label="کمپین‌ها" value={report.total_campaigns} />
              <Stat label="لینک‌های ساخته‌شده" value={report.total_links_built} />
              <Stat label="صفحات تقویت‌شده" value={report.pages_covered} />
            </div>
          </CardContent>
        </Card>
      )}

      <div className="max-w-xs">
        <Label>کمپین</Label>
        <Select value={campaignId ?? ""} onChange={(e) => setCampaignId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">انتخاب کمپین...</option>
          {campaigns?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
      </div>

      {campaignId && <CampaignReportSection campaignId={campaignId} />}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-slate-50 p-3 text-center">
      <div className="text-xl font-bold text-slate-900">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function CampaignReportSection({ campaignId }: { campaignId: number }) {
  const { data: report, isLoading, error } = useCampaignReport(campaignId);
  const { data: stats } = usePipelineStats(campaignId);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!report) return null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>گزارش کمپین: {report.campaign_name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="کل مقالات" value={report.total_articles} />
            <Stat label="ممیزی‌شده" value={report.audited_articles} />
            <Stat
              label="نرخ موفقیت ممیزی"
              value={report.audit_success_rate != null ? Math.round(report.audit_success_rate) : 0}
            />
            <Stat label="منتشرشده" value={report.published_urls.length} />
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">Anchor Distribution (هدف در برابر واقعی)</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-right text-slate-400">
                  <th className="pb-1 font-normal">نوع انکر</th>
                  <th className="pb-1 font-normal">هدف (٪)</th>
                  <th className="pb-1 font-normal">واقعی (تعداد)</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(report.anchor_distribution_target).map((type) => (
                  <tr key={type} className="border-t border-slate-100">
                    <td className="py-1 font-medium text-slate-800">{ANCHOR_TYPE_LABEL[type] ?? type}</td>
                    <td className="py-1">{report.anchor_distribution_target[type]}</td>
                    <td className="py-1">{report.anchor_distribution_actual[type] ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">URLهای منتشرشده</h3>
            {!report.published_urls.length ? (
              <EmptyState message="هنوز هیچ مقاله‌ای در این کمپین منتشر نشده است." />
            ) : (
              <ul className="space-y-1 text-sm">
                {report.published_urls.map((url) => (
                  <li key={url}>
                    <a href={url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline Bottleneck Report</CardTitle>
        </CardHeader>
        <CardContent>
          {!stats || !Object.keys(stats.stages).length ? (
            <EmptyState message="هنوز داده‌ی کافی برای محاسبه‌ی میانگین زمان توقف در هر مرحله وجود ندارد." />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-right text-slate-400">
                  <th className="pb-1 font-normal">مرحله</th>
                  <th className="pb-1 font-normal">میانگین زمان توقف (ساعت)</th>
                  <th className="pb-1 font-normal">تعداد نمونه</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.stages).map(([stage, stat]) => (
                  <tr key={stage} className="border-t border-slate-100">
                    <td className="py-1 font-medium text-slate-800">{STAGE_LABEL[stage] ?? stage}</td>
                    <td className="py-1">{stat.avg_hours}</td>
                    <td className="py-1 text-slate-400">{stat.sample_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
