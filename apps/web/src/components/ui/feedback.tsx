export function Spinner() {
  return (
    <div className="flex items-center justify-center py-10 text-sm text-slate-500">در حال بارگذاری...</div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{message}</div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}
