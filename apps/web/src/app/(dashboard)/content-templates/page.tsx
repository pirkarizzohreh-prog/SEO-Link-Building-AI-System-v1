"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useContentTemplates, useCreateContentTemplate } from "@/lib/hooks";

export default function ContentTemplatesPage() {
  const { data: templates, isLoading, error } = useContentTemplates();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">تمپلیت‌های محتوا</h1>
          <p className="text-sm text-slate-500">
            اسکلت پایه‌ی Content Brief Generator — نگاه کنید به docs/AI_WORKFLOW.md
          </p>
        </div>
        <Button onClick={() => setModalOpen(true)}>+ تمپلیت جدید</Button>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}
      {templates && templates.length === 0 && <EmptyState message="هنوز تمپلیتی ثبت نشده است." />}

      {templates && templates.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <Table>
            <Thead>
              <Tr>
                <Th>نام</Th>
                <Th>توضیح</Th>
                <Th>تعداد کلمه پیش‌فرض</Th>
              </Tr>
            </Thead>
            <tbody>
              {templates.map((t) => (
                <Tr key={t.id}>
                  <Td className="font-medium text-slate-900">{t.name}</Td>
                  <Td>{t.description ?? "—"}</Td>
                  <Td>{t.default_word_count}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      <CreateTemplateModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function CreateTemplateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createTemplate = useCreateContentTemplate();
  const [form, setForm] = useState({ name: "", description: "", default_word_count: 1200 });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createTemplate.mutateAsync(form);
      setForm({ name: "", description: "", default_word_count: 1200 });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="تمپلیت جدید">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Label>نام</Label>
          <Input
            required
            placeholder="مثلاً Educational How-To"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div>
          <Label>توضیح</Label>
          <Textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        <div>
          <Label>تعداد کلمه پیش‌فرض</Label>
          <Input
            type="number"
            value={form.default_word_count}
            onChange={(e) => setForm({ ...form, default_word_count: Number(e.target.value) })}
          />
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={createTemplate.isPending}>
            ایجاد
          </Button>
        </div>
      </form>
    </Modal>
  );
}
