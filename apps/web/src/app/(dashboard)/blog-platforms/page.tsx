"use client";

import { useState, type FormEvent } from "react";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { useAuth } from "@/lib/auth-context";
import { getErrorMessage } from "@/lib/get-error-message";
import { useBlogPlatforms, useCreateBlogPlatform, useSetBlogPlatformCredentials } from "@/lib/hooks";
import type { BlogPlatform } from "@/lib/types";

export default function BlogPlatformsPage() {
  const { user: currentUser } = useAuth();
  const { data: platforms, isLoading, error } = useBlogPlatforms();
  const [modalOpen, setModalOpen] = useState(false);
  const [credentialsTarget, setCredentialsTarget] = useState<BlogPlatform | null>(null);
  const isAdmin = currentUser?.role === "admin";

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
                <Th>اتوماسیون</Th>
                <Th></Th>
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
                  <Td>
                    {b.has_automation_credentials ? (
                      <Badge tone="green">تنظیم‌شده</Badge>
                    ) : (
                      <Badge tone="slate">تنظیم‌نشده</Badge>
                    )}
                  </Td>
                  <Td>
                    {isAdmin && (
                      <Button size="sm" variant="secondary" onClick={() => setCredentialsTarget(b)}>
                        تنظیم اطلاعات ورود
                      </Button>
                    )}
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      <CreateBlogPlatformModal open={modalOpen} onClose={() => setModalOpen(false)} />
      {credentialsTarget && (
        <CredentialsModal blogPlatform={credentialsTarget} onClose={() => setCredentialsTarget(null)} />
      )}
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
          اطلاعات ورود برای اتوماسیون انتشار (Playwright) را بعد از ایجاد، از دکمه «تنظیم اطلاعات ورود» وارد کنید.
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

function CredentialsModal({ blogPlatform, onClose }: { blogPlatform: BlogPlatform; onClose: () => void }) {
  const setCredentials = useSetBlogPlatformCredentials(blogPlatform.id);
  const [form, setForm] = useState({
    username: blogPlatform.username ?? "",
    password: "",
    login_url: blogPlatform.login_url ?? "",
  });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await setCredentials.mutateAsync({
        username: form.username,
        password: form.password,
        ...(form.login_url ? { login_url: form.login_url } : {}),
      });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open onClose={onClose} title={`اطلاعات ورود — ${blogPlatform.name}`}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <p className="text-xs text-slate-400">
          این اطلاعات فقط برای اتوماسیون انتشار با Playwright استفاده می‌شود و به‌صورت رمزنگاری‌شده (Fernet) ذخیره
          می‌شود — هرگز به‌صورت متن ساده در دیتابیس یا پاسخ API قابل مشاهده نیست.
        </p>
        <div>
          <Label>نام کاربری</Label>
          <Input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        </div>
        <div>
          <Label>رمز عبور</Label>
          <Input
            required
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <div>
          <Label>آدرس ورود (اختیاری — پیش‌فرض: آدرس وبلاگ + /wp-login.php)</Label>
          <Input
            type="url"
            value={form.login_url}
            onChange={(e) => setForm({ ...form, login_url: e.target.value })}
          />
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={setCredentials.isPending}>
            ذخیره
          </Button>
        </div>
      </form>
    </Modal>
  );
}
