"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, SlidersHorizontal } from "lucide-react";
import { configApi } from "@/lib/api";
import { Card } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const configQuery = useQuery({
    queryKey: ["business-config", "list"],
    queryFn: () => configApi.listBusinessConfig({ limit: 200 }),
  });

  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [saving, setSaving] = useState(false);

  async function addOrUpdate(e: FormEvent) {
    e.preventDefault();
    if (!newKey || !newValue) return;
    setSaving(true);
    try {
      await configApi.updateBusinessConfig(newKey, newValue);
      setNewKey("");
      setNewValue("");
      await queryClient.invalidateQueries({ queryKey: ["business-config"] });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Settings"
        description="Business constants. Autonomy level is controlled from the header."
      />

      <Card
        icon={<SlidersHorizontal size={14} />}
        eyebrow={`${configQuery.data?.total ?? 0} keys`}
        title="Business config"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={th}>Key</th>
                <th className={th}>Value</th>
                <th className={th}>Description</th>
              </tr>
            </thead>
            <tbody>
              {configQuery.data?.items.map((c) => (
                <tr key={c.id} className={row}>
                  <td className={`${td} mono text-ink`}>{c.key}</td>
                  <td className={`${td} mono font-medium text-accent-strong`}>{c.value}</td>
                  <td className={`${td} text-muted`}>{c.description ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {configQuery.data?.items.length === 0 && (
          <EmptyState
            icon={<SlidersHorizontal size={18} />}
            message="No overrides set — all business constants are using in-code defaults."
          />
        )}

        <form
          onSubmit={addOrUpdate}
          className="mt-5 flex items-end gap-2.5 border-t border-line pt-5"
        >
          <div className="flex flex-1 flex-col gap-1.5">
            <label className="label">Key</label>
            <input
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="sla_at_risk_threshold_min"
              className="mono rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <div className="flex flex-1 flex-col gap-1.5">
            <label className="label">Value</label>
            <input
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder="60"
              className="mono rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-accent to-accent-strong px-3.5 py-2 text-sm font-semibold text-bg hover:opacity-90 disabled:opacity-60"
          >
            <Plus size={14} />
            {saving ? "Saving…" : "Set"}
          </button>
        </form>
      </Card>
    </div>
  );
}
