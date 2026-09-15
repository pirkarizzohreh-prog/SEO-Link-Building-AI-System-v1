"use client";

import { useState, type FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, Spinner } from "@/components/ui/feedback";
import { Input, Label, Select } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Table, Td, Th, Thead, Tr } from "@/components/ui/table";
import { useAuth } from "@/lib/auth-context";
import { getErrorMessage } from "@/lib/get-error-message";
import { useCreateUser, useUsers } from "@/lib/hooks";

const ROLE_LABEL: Record<string, string> = { admin: "مدیر", editor: "ویرایشگر" };

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const { data: users, isLoading, error } = useUsers();
  const [modalOpen, setModalOpen] = useState(false);

  if (currentUser && currentUser.role !== "admin") {
    return <EmptyState message="این صفحه فقط برای مدیران قابل مشاهده است." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">کاربران</h1>
        <Button onClick={() => setModalOpen(true)}>+ کاربر جدید</Button>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorBanner message={getErrorMessage(error)} />}

      {users && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <Table>
            <Thead>
              <Tr>
                <Th>نام</Th>
                <Th>ایمیل</Th>
                <Th>نقش</Th>
                <Th>وضعیت</Th>
              </Tr>
            </Thead>
            <tbody>
              {users.map((u) => (
                <Tr key={u.id}>
                  <Td className="font-medium text-slate-900">{u.name}</Td>
                  <Td>{u.email}</Td>
                  <Td>
                    <Badge tone={u.role === "admin" ? "purple" : "blue"}>{ROLE_LABEL[u.role]}</Badge>
                  </Td>
                  <Td>
                    <Badge tone={u.is_active ? "green" : "slate"}>{u.is_active ? "فعال" : "غیرفعال"}</Badge>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      <CreateUserModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function CreateUserModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createUser = useCreateUser();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "editor" });
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createUser.mutateAsync(form);
      setForm({ name: "", email: "", password: "", role: "editor" });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="کاربر جدید">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <Label>نام</Label>
          <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <Label>ایمیل</Label>
          <Input
            required
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div>
          <Label>رمز عبور موقت</Label>
          <Input
            required
            type="password"
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <div>
          <Label>نقش</Label>
          <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="editor">ویرایشگر</option>
            <option value="admin">مدیر</option>
          </Select>
        </div>
        {error && <ErrorBanner message={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            انصراف
          </Button>
          <Button type="submit" isLoading={createUser.isPending}>
            ایجاد
          </Button>
        </div>
      </form>
    </Modal>
  );
}
