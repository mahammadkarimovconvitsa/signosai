"use client";

import { useQuery } from "@tanstack/react-query";
import { LayoutGrid } from "lucide-react";
import { portfolioApi } from "@/lib/api";
import { metricIds } from "@/lib/metric-ids";
import { Card } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { PortfolioRecommendationBadge } from "@/components/badges";
import { MetricValue } from "@/components/metric-value";

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function PortfolioPage() {
  const portfolioQuery = useQuery({
    queryKey: ["portfolio", "list"],
    queryFn: () => portfolioApi.list({ limit: 200 }),
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Portfolio"
        description="Deterministic upgrade / keep / consolidate / decommission recommendation per site."
      />

      <Card
        icon={<LayoutGrid size={14} />}
        eyebrow={`${portfolioQuery.data?.total ?? 0} sites`}
        title="Site recommendations"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={th}>Site</th>
                <th className={th}>Traffic (subs)</th>
                <th className={th}>Revenue/mo</th>
                <th className={th}>Energy cost/mo</th>
                <th className={th}>Ratio</th>
                <th className={th}>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {portfolioQuery.data?.items.map((p) => (
                <tr key={p.site_id} className={row}>
                  <td className={`${td} font-medium text-ink`}>{p.site_name}</td>
                  <td className={td}>
                    <MetricValue
                      metric={p.traffic_proxy_subscribers}
                      metricId={metricIds.portfolioTraffic(p.site_id)}
                      label="Traffic proxy"
                      size="sm"
                    />
                  </td>
                  <td className={td}>
                    <MetricValue
                      metric={p.revenue_azn_month}
                      metricId={metricIds.portfolioRevenue(p.site_id)}
                      label="Revenue / month"
                      size="sm"
                    />
                  </td>
                  <td className={td}>
                    <MetricValue
                      metric={p.energy_cost_azn_month}
                      metricId={metricIds.portfolioEnergyCost(p.site_id)}
                      label="Energy cost / month"
                      size="sm"
                    />
                  </td>
                  <td className={td}>
                    <MetricValue
                      metric={p.revenue_to_cost_ratio}
                      metricId={metricIds.portfolioRatio(p.site_id)}
                      label="Revenue to cost ratio"
                      decimals={2}
                      size="sm"
                    />
                  </td>
                  <td className={td}>
                    <PortfolioRecommendationBadge recommendation={p.recommendation} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {portfolioQuery.data?.items.length === 0 && (
          <EmptyState icon={<LayoutGrid size={18} />} message="No sites loaded yet." />
        )}
      </Card>
    </div>
  );
}
