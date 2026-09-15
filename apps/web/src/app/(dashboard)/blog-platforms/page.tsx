"use client";

import { useState, type FormEvent } from "react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useBlogPlatforms, useCreateBlogPlatform } from "@/lib/hooks";

export default function BlogPlatformsPage() {
  const { data: platforms, isLoading, error } = useBlogPlatforms();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">وبلاگ‌های انتشار</h1>
        <Button onClick={() => setModalOpen(true)}>+ وبلاگ جدید</Button>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}
      {platforms && platforms.length === 0 && <EmptyState message="هنوز وبلاگی ثبت نشده است." />}

      {platforms && platforms.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <Table>
            <Thead>
              <Tr>
                <Th>نام</Th>
                <Th>آدرس</Th>
                <Th>آخرین انتشار</Th>
                <Th>وضعیت</Th>
              </Tr>
            </Thead>
            <tbody>
              {platforms.map((b) => (
                <Tr key={b.id}>
                  <Td className="font-medium text-slate-900">{b.name}</Td>
                  <Td className="max-w-xs truncate">{b.url}</Td>
                  <Td>{b.last_publish_date ? new Date(b.last_publish_date).toLocaleDateString("fa-IR") : "—"}</Td>
                  <Td>
                    <StatusBadge status={b.status} />
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      <CreateBlogPlatformModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function CreateBlogPlatformModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createBlogPlatform = useCreateBlogPlatform();
  const [form, setForm] = useState({ name: "", url: "" });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createBlogPlatform.mutateAsync(form);
      setForm({ name: "", url: "" });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="وبلاگ جدید">
      <form onSubmit={handleSubmit} className="space-y-3">
        <p className="text-xs text-slate-400">
          اتصال ورود/رمز عبور و اتوماسیون انتشار (Playwright) در Sprint 5 اضافه می‌شود؛ فعلاً فقط اطلاعات پایه.
        </p>
        <div>
          <Label>نام وبلاگ</Label>
          <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <Label>آدرس</Label>
          <Input required type="url" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} />
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={createBlogPlatform.isPending}>
            ایجاد
          </Button>
        </div>
      </form>
    </Modal>
  );
}
