"use client";

import Link from "next/link";
import { use, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/get-error-message";
import {
  useCreateTargetPage,
  useProject,
  useProjectKnowledgeBase,
  useTargetPages,
  useUpsertKnowledgeBase,
} from "@/lib/hooks";
import type { PageType, ProjectKnowledgeBase } from "@/lib/types";

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const projectId = Number(id);

  const { data: project, isLoading, error } = useProject(projectId);
  const { data: targetPages } = useTargetPages(projectId);
  const [modalOpen, setModalOpen] = useState(false);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner message={getErrorMessage(error)} />;
  if (!project) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-slate-900">{project.project_name}</h1>
        <p className="text-sm text-slate-500">{project.website_url}</p>
      </div>

      <KnowledgeBaseCard projectId={projectId} />

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>صفحات هدف</CardTitle>
          <Button size="sm" onClick={() => setModalOpen(true)}>
            + صفحه هدف جدید
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {!targetPages?.length ? (
            <div className="p-5">
              <EmptyState message="هنوز صفحه هدفی برای این پروژه ثبت نشده است." />
            </div>
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>عنوان</Th>
                  <Th>کلیدواژه اصلی</Th>
                  <Th>نوع صفحه</Th>
                  <Th>اولویت</Th>
                </Tr>
              </Thead>
              <tbody>
                {targetPages.map((tp) => (
                  <Tr key={tp.id}>
                    <Td>
                      <Link
                        href={`/projects/${projectId}/target-pages/${tp.id}`}
                        className="font-medium text-slate-900 hover:underline"
                      >
                        {tp.title}
                      </Link>
                    </Td>
                    <Td>{tp.main_keyword}</Td>
                    <Td>{tp.page_type}</Td>
                    <Td>{tp.priority}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>

      <CreateTargetPageModal projectId={projectId} open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function KnowledgeBaseCard({ projectId }: { projectId: number }) {
  const { data: kb, isLoading } = useProjectKnowledgeBase(projectId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Knowledge Base (برند، لحن، مخاطب)</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Spinner />
        ) : (
          // `key` forces a remount (and fresh initial state) once `kb` goes
          // from "not loaded yet" to its real value, instead of syncing an
          // effect into local form state for the same purpose.
          <KnowledgeBaseForm key={kb ? kb.id : "new"} projectId={projectId} kb={kb ?? null} />
        )}
      </CardContent>
    </Card>
  );
}

function KnowledgeBaseForm({
  projectId,
  kb,
}: {
  projectId: number;
  kb: ProjectKnowledgeBase | null;
}) {
  const upsert = useUpsertKnowledgeBase(projectId);
  const [form, setForm] = useState({
    brand_name: kb?.brand_name ?? "",
    brand_voice_tone: kb?.brand_voice_tone ?? "",
    target_audience: kb?.target_audience ?? "",
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    try {
      await upsert.mutateAsync(form);
      setSaved(true);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <Label>نام برند</Label>
        <Input value={form.brand_name} onChange={(e) => setForm({ ...form, brand_name: e.target.value })} />
      </div>
      <div>
        <Label>لحن برند</Label>
        <Input
          placeholder="مثلاً: تخصصی، غیررسمی، مبتنی بر داده"
          value={form.brand_voice_tone}
          onChange={(e) => setForm({ ...form, brand_voice_tone: e.target.value })}
        />
      </div>
      <div>
        <Label>مخاطب هدف</Label>
        <Textarea
          value={form.target_audience}
          onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
        />
      </div>
      {error && <ErrorBanner message={error} />}
      <div className="flex items-center gap-3">
        <Button type="submit" size="sm" isLoading={upsert.isPending}>
          ذخیره
        </Button>
        {saved && <span className="text-sm text-emerald-600">ذخیره شد.</span>}
      </div>
    </form>
  );
}

function CreateTargetPageModal({
  projectId,
  open,
  onClose,
}: {
  projectId: number;
  open: boolean;
  onClose: () => void;
}) {
  const createTargetPage = useCreateTargetPage(projectId);
  const [form, setForm] = useState<{
    title: string;
    url: string;
    main_keyword: string;
    page_type: PageType;
    priority: number;
  }>({ title: "", url: "", main_keyword: "", page_type: "article", priority: 0 });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createTargetPage.mutateAsync(form);
      setForm({ title: "", url: "", main_keyword: "", page_type: "article", priority: 0 });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="صفحه هدف جدید">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Label>عنوان</Label>
          <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </div>
        <div>
          <Label>URL</Label>
          <Input required type="url" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} />
        </div>
        <div>
          <Label>کلیدواژه اصلی</Label>
          <Input
            required
            value={form.main_keyword}
            onChange={(e) => setForm({ ...form, main_keyword: e.target.value })}
          />
        </div>
        <div>
          <Label>نوع صفحه</Label>
          <Select
            value={form.page_type}
            onChange={(e) => setForm({ ...form, page_type: e.target.value as PageType })}
          >
            <option value="article">مقاله</option>
            <option value="product">محصول</option>
            <option value="category">دسته‌بندی</option>
          </Select>
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={createTargetPage.isPending}>
            ایجاد
          </Button>
        </div>
      </form>
    </Modal>
  );
}
