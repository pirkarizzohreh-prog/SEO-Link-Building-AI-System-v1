"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/badge";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import { useCreateProject, useProjects } from "@/lib/hooks";

export default function ProjectsPage() {
  const { data: projects, isLoading, error } = useProjects();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">پروژه‌ها</h1>
        <Button onClick={() => setModalOpen(true)}>+ پروژه جدید</Button>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}

      {projects && projects.length === 0 && <EmptyState message="هنوز پروژه‌ای ثبت نشده است." />}

      {projects && projects.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <Table>
            <Thead>
              <Tr>
                <Th>نام پروژه</Th>
                <Th>حوزه فعالیت</Th>
                <Th>وب‌سایت</Th>
                <Th>وضعیت</Th>
              </Tr>
            </Thead>
            <tbody>
              {projects.map((p) => (
                <Tr key={p.id}>
                  <Td>
                    <Link href={`/projects/${p.id}`} className="font-medium text-slate-900 hover:underline">
                      {p.project_name}
                    </Link>
                  </Td>
                  <Td>{p.industry ?? "—"}</Td>
                  <Td className="max-w-xs truncate">{p.website_url}</Td>
                  <Td>
                    <StatusBadge status={p.status} />
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      <CreateProjectModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function CreateProjectModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createProject = useCreateProject();
  const [form, setForm] = useState({ project_name: "", website_url: "", industry: "", description: "" });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createProject.mutateAsync(form);
      setForm({ project_name: "", website_url: "", industry: "", description: "" });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="پروژه جدید">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Label>نام پروژه</Label>
          <Input
            required
            value={form.project_name}
            onChange={(e) => setForm({ ...form, project_name: e.target.value })}
          />
        </div>
        <div>
          <Label>آدرس وب‌سایت</Label>
          <Input
            required
            type="url"
            value={form.website_url}
            onChange={(e) => setForm({ ...form, website_url: e.target.value })}
          />
        </div>
        <div>
          <Label>حوزه فعالیت</Label>
          <Input value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={createProject.isPending}>
            ایجاد
          </Button>
        </div>
      </form>
    </Modal>
  );
}
