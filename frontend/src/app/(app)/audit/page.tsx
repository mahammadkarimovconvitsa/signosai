"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { auditApi } from "@/lib/api";
import { Card } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { RoleBadge } from "@/components/badges";

const ENTITIES = ["", "settings", "business_config", "user", "action", "incident", "system"];

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function AuditPage() {
  const [entity, setEntity] = useState("");

  const auditQuery = useQuery({
    queryKey: ["audit", entity],
    queryFn: () => auditApi.list({ limit: 100, entity: entity || undefined }),
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Audit log"
        description="Append-only record of every system and user action."
        action={
          <select
            value={entity}
            onChange={(e) => setEntity(e.target.value)}
            className="rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-[13px] text-ink outline-none focus:border-accent"
          >
            {ENTITIES.map((e) => (
              <option key={e} value={e}>
                {e === "" ? "All entities" : e}
              </option>
            ))}
          </select>
        }
      />

      <Card
        icon={<ShieldCheck size={14} />}
        eyebrow={`${auditQuery.data?.total ?? 0} events`}
        title="Events"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={th}>Time</th>
                <th className={th}>Event</th>
                <th className={th}>Entity</th>
                <th className={th}>Actor</th>
                <th className={th}>Details</th>
              </tr>
            </thead>
            <tbody>
              {auditQuery.data?.items.map((event) => (
                <tr key={event.id} className={`${row} align-top`}>
                  <td className={`${td} mono text-xs text-muted`}>
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className={`${td} font-medium text-ink`}>{event.event_type}</td>
                  <td className={`${td} text-muted`}>{event.entity}</td>
                  <td className={td}>{event.actor_role && <RoleBadge role={event.actor_role} />}</td>
                  <td className={`${td} mono max-w-xs truncate text-xs text-muted-2`}>
                    {JSON.stringify(event.details)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {auditQuery.data?.items.length === 0 && (
          <EmptyState icon={<ShieldCheck size={18} />} message="No audit events yet." />
        )}
      </Card>
    </div>
  );
}
