import { EmptyState } from "@/components/ui/feedback";

export default function ReportsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-slate-900">گزارش‌ها</h1>
      <EmptyState message="گزارش‌گیری (تعداد لینک، توزیع Anchor، Pipeline Bottleneck Report) در Sprint 4 اضافه می‌شود." />
    </div>
  );
}
