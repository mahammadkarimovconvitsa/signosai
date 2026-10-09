"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { UserPlus, Users as UsersIcon } from "lucide-react";
import { usersApi } from "@/lib/api";
import { Card } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { RoleBadge } from "@/components/badges";
import { ApiError } from "@/lib/http";
import type { UserRole } from "@/lib/types";

const ROLES: UserRole[] = ["admin", "engineer", "account_manager", "viewer"];

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function UsersPage() {
  const queryClient = useQueryClient();
  const usersQuery = useQuery({
    queryKey: ["users", "list"],
    queryFn: () => usersApi.list({ limit: 200 }),
  });

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("viewer");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function createUser(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await usersApi.create(email, password, role);
      setEmail("");
      setPassword("");
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create user");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(id: string, isActive: boolean) {
    setBusyId(id);
    try {
      await (isActive ? usersApi.deactivate(id) : usersApi.activate(id));
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Users" description="Manage accounts and roles." />

      <Card icon={<UsersIcon size={14} />} eyebrow={`${usersQuery.data?.total ?? 0} total`} title="All users">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={th}>Email</th>
                <th className={th}>Role</th>
                <th className={th}>Status</th>
                <th className={th} />
              </tr>
            </thead>
            <tbody>
              {usersQuery.data?.items.map((u) => (
                <tr key={u.id} className={row}>
                  <td className={`${td} text-ink`}>{u.email}</td>
                  <td className={td}>
                    <RoleBadge role={u.role} />
                  </td>
                  <td className={td}>
                    <span
                      className={
                        "inline-flex items-center gap-1.5 text-xs font-medium " +
                        (u.is_active ? "text-ok" : "text-muted-2")
                      }
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${u.is_active ? "bg-ok" : "bg-muted-2"}`}
                      />
                      {u.is_active ? "active" : "inactive"}
                    </span>
                  </td>
                  <td className={`${td} text-right`}>
                    <button
                      onClick={() => toggleActive(u.id, u.is_active)}
                      disabled={busyId === u.id}
                      className="rounded-lg border border-line-strong px-2.5 py-1 text-xs font-medium text-muted hover:border-accent-line hover:text-ink disabled:opacity-60"
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card icon={<UserPlus size={14} />} eyebrow="Admin" title="Create user">
        <form onSubmit={createUser} className="flex items-end gap-2.5">
          <div className="flex flex-1 flex-col gap-1.5">
            <label className="label">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <div className="flex flex-1 flex-col gap-1.5">
            <label className="label">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="label">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-accent to-accent-strong px-3.5 py-2 text-sm font-semibold text-bg hover:opacity-90 disabled:opacity-60"
          >
            <UserPlus size={14} />
            {saving ? "Creating…" : "Create"}
          </button>
        </form>
        {error && (
          <p className="mt-3 rounded-lg border border-breached-line bg-breached-soft px-3 py-2 text-sm text-breached">
            {error}
          </p>
        )}
      </Card>
    </div>
  );
}
