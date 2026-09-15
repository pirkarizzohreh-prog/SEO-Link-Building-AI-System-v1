"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/badge";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useCampaigns, useCreateCampaign, useProjects, useTargetPages } from "@/lib/hooks";

export default function CampaignsPage() {
  const { data: campaigns, isLoading, error } = useCampaigns();
  const { data: projects } = useProjects();
  const [modalOpen, setModalOpen] = useState(false);

  const projectNameById = new Map((projects ?? []).map((p) => [p.id, p.project_name]));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">کمپین‌ها</h1>
        <Button onClick={() => setModalOpen(true)}>+ کمپین جدید</Button>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}
      {campaigns && campaigns.length === 0 && <EmptyState message="هنوز کمپینی ثبت نشده است." />}

      {campaigns && campaigns.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <Table>
            <Thead>
              <Tr>
                <Th>نام کمپین</Th>
                <Th>پروژه</Th>
                <Th>تعداد لینک هدف</Th>
                <Th>وضعیت</Th>
              </Tr>
            </Thead>
            <tbody>
              {campaigns.map((c) => (
                <Tr key={c.id}>
                  <Td>
                    <Link href={`/campaigns/${c.id}`} className="font-medium text-slate-900 hover:underline">
                      {c.name}
                    </Link>
                  </Td>
                  <Td>{projectNameById.get(c.project_id) ?? c.project_id}</Td>
                  <Td>{c.total_links_target}</Td>
                  <Td>
                    <StatusBadge status={c.status} />
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      <CreateCampaignModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function CreateCampaignModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { data: projects } = useProjects();
  const createCampaign = useCreateCampaign();
  const [form, setForm] = useState({
    project_id: "",
    target_page_id: "",
    name: "",
    total_links_target: 20,
    blog_count: 10,
    duration_days: 60,
  });
  const [error, setError] = useState<string | null>(null);
  const { data: targetPages } = useTargetPages(Number(form.project_id) || 0);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createCampaign.mutateAsync({
        ...form,
        project_id: Number(form.project_id),
        target_page_id: Number(form.target_page_id),
      });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="کمپین جدید">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Label>پروژه</Label>
          <Select
            required
            value={form.project_id}
            onChange={(e) => setForm({ ...form, project_id: e.target.value, target_page_id: "" })}
          >
            <option value="">انتخاب کنید...</option>
            {projects?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>صفحه هدف</Label>
          <Select
            required
            disabled={!form.project_id}
            value={form.target_page_id}
            onChange={(e) => setForm({ ...form, target_page_id: e.target.value })}
          >
            <option value="">انتخاب کنید...</option>
            {targetPages?.map((tp) => (
              <option key={tp.id} value={tp.id}>
                {tp.title}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>نام کمپین</Label>
          <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div>
            <Label>تعداد لینک هدف</Label>
            <Input
              type="number"
              value={form.total_links_target}
              onChange={(e) => setForm({ ...form, total_links_target: Number(e.target.value) })}
            />
          </div>
          <div>
            <Label>تعداد وبلاگ</Label>
            <Input
              type="number"
              value={form.blog_count}
              onChange={(e) => setForm({ ...form, blog_count: Number(e.target.value) })}
            />
          </div>
          <div>
            <Label>مدت (روز)</Label>
            <Input
              type="number"
              value={form.duration_days}
              onChange={(e) => setForm({ ...form, duration_days: Number(e.target.value) })}
            />
          </div>
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={createCampaign.isPending}>
            ایجاد
          </Button>
        </div>
      </form>
    </Modal>
  );
}
