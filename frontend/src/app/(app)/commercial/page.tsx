"use client";

import { useQuery } from "@tanstack/react-query";
import { Mail, Users } from "lucide-react";
import { analysisApi, incidentsApi } from "@/lib/api";
import { ApiError } from "@/lib/http";
import { metricIds } from "@/lib/metric-ids";
import { Card, StatCard } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { MetricValue } from "@/components/metric-value";

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function CommercialPage() {
  const incidentQuery = useQuery({
    queryKey: ["incident-current"],
    queryFn: incidentsApi.current,
    retry: false,
  });
  const incident =
    incidentQuery.error instanceof ApiError && incidentQuery.error.status === 404
      ? null
      : incidentQuery.data;

  const commercialQuery = useQuery({
    queryKey: ["commercial", incident?.id],
    queryFn: () => analysisApi.commercial(incident!.id),
    enabled: !!incident,
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Commercial"
        description="Affected high-value subscribers and compensation draft for the active incident."
      />

      {!incident && (
        <Card>
          <EmptyState icon={<Mail size={18} />} message="No active incident — nothing to show." />
        </Card>
      )}

      {incident && commercialQuery.data && (
        <>
          <div className="grid grid-cols-2 gap-6">
            <StatCard
              eyebrow="Affected premium subscribers"
              value={
                <MetricValue
                  metric={commercialQuery.data.affected_premium_subscribers}
                  metricId={metricIds.commercialAffectedPremium(incident.id)}
                  label="Affected premium subscribers"
                  size="xl"
                />
              }
            />
            <StatCard
              accent
              eyebrow="Compensation cost"
              value={
                <MetricValue
                  metric={commercialQuery.data.compensation_cost_azn}
                  metricId={metricIds.commercialCompensationCost(incident.id)}
                  label="Compensation cost"
                  decimals={0}
                  size="xl"
                  className="text-accent-strong"
                />
              }
            />
          </div>

          <Card
            icon={<Users size={14} />}
            eyebrow={`${commercialQuery.data.sample_subscribers.length} shown`}
            title="Premium subscribers in affected cells"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className={th}>Name</th>
                    <th className={th}>MSISDN</th>
                  </tr>
                </thead>
                <tbody>
                  {commercialQuery.data.sample_subscribers.map((s) => (
                    <tr key={s.id} className={row}>
                      <td className={`${td} text-ink`}>{s.name ?? "—"}</td>
                      <td className={`${td} mono text-muted`}>{s.msisdn_masked}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {commercialQuery.data.sample_subscribers.length === 0 && (
              <EmptyState
                icon={<Users size={18} />}
                message="No named subscriber rows for the affected cells."
              />
            )}
          </Card>
        </>
      )}
    </div>
  );
}
