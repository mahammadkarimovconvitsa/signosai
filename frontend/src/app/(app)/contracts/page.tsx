"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Info } from "lucide-react";
import { contractsApi } from "@/lib/api";
import { Card } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";

const TYPE_LABEL: Record<string, string> = {
  enterprise_sla: "Enterprise SLA",
  tower_lease: "Tower lease",
  interconnect: "Interconnect",
  vendor_sla: "Vendor SLA",
};

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function ContractsPage() {
  const contractsQuery = useQuery({
    queryKey: ["contracts", "list"],
    queryFn: () => contractsApi.list({ limit: 200 }),
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Contracts"
        description="Reference contracts. Live SLA compliance is computed per active incident."
      />

      <div className="flex items-start gap-2.5 rounded-xl border border-accent-line bg-accent-soft px-4 py-3 text-[13px] text-ink-secondary">
        <Info size={15} className="mt-0.5 shrink-0 text-accent" />
        <span>
          Compliance status, time remaining and penalty figures only exist in the context of an
          active incident — see the <span className="font-medium text-accent">Incident Console</span>.
        </span>
      </div>

      <Card
        icon={<FileText size={14} />}
        eyebrow={`${contractsQuery.data?.total ?? 0} total`}
        title="All contracts"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={th}>Type</th>
                <th className={th}>Restore within</th>
                <th className={th}>Penalty/hour</th>
                <th className={th}>Cap</th>
                <th className={th}>Valid from</th>
                <th className={th}>Valid to</th>
              </tr>
            </thead>
            <tbody>
              {contractsQuery.data?.items.map((c) => (
                <tr key={c.id} className={`${row} align-top`}>
                  <td className="py-3.5">
                    <div className="font-medium text-ink">{TYPE_LABEL[c.type] ?? c.type}</div>
                    <div className="mt-0.5 max-w-md text-xs text-muted-2">{c.clause_text}</div>
                  </td>
                  <td className={`${td} mono text-muted`}>{c.restore_within_min} min</td>
                  <td className={`${td} mono text-muted`}>
                    {c.penalty_per_started_hour_azn.toLocaleString()} AZN
                  </td>
                  <td className={`${td} mono text-muted`}>{c.penalty_cap_azn.toLocaleString()} AZN</td>
                  <td className={`${td} text-muted`}>{c.valid_from}</td>
                  <td className={`${td} text-muted`}>{c.valid_to ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {contractsQuery.data?.items.length === 0 && (
          <EmptyState icon={<FileText size={18} />} message="No contracts loaded yet." />
        )}
      </Card>
    </div>
  );
}
