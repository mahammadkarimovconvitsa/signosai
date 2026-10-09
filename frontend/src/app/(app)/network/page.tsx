"use client";

import { useQuery } from "@tanstack/react-query";
import { Cable, Radio, Smartphone } from "lucide-react";
import { networkApi } from "@/lib/api";
import { Card } from "@/components/card";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { StatusBadge } from "@/components/badges";

const th = "pb-3 text-left text-[11px] font-semibold uppercase tracking-wide text-muted-2";
const row = "border-b border-line transition-colors last:border-0 hover:bg-surface-raised/50";
const td = "py-3";

export default function NetworkPage() {
  const sitesQuery = useQuery({
    queryKey: ["sites", "list"],
    queryFn: () => networkApi.listSites({ limit: 200 }),
  });
  const linksQuery = useQuery({
    queryKey: ["links", "list"],
    queryFn: () => networkApi.listLinks({ limit: 200 }),
  });
  const cellsQuery = useQuery({
    queryKey: ["cells", "list"],
    queryFn: () => networkApi.listCells({ limit: 200 }),
  });

  const siteNameById = new Map((sitesQuery.data?.items ?? []).map((s) => [s.id, s.name]));

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Network" description="Sites, links and cells — reference data." />

      <Card icon={<Radio size={14} />} eyebrow={`${sitesQuery.data?.total ?? 0} total`} title="Sites">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={th}>Name</th>
                <th className={th}>District</th>
                <th className={th}>Energy cost/mo</th>
                <th className={th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {sitesQuery.data?.items.map((site) => (
                <tr key={site.id} className={row}>
                  <td className={`${td} font-medium text-ink`}>{site.name}</td>
                  <td className={`${td} text-muted`}>{site.district}</td>
                  <td className={`${td} mono text-muted`}>
                    {site.energy_cost_azn_month.toLocaleString()} AZN
                  </td>
                  <td className={td}>
                    <StatusBadge status={site.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {sitesQuery.data?.items.length === 0 && (
          <EmptyState icon={<Radio size={18} />} message="No sites loaded yet." />
        )}
      </Card>

      <div className="grid grid-cols-2 gap-6">
        <Card icon={<Cable size={14} />} eyebrow={`${linksQuery.data?.total ?? 0} total`} title="Links">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className={th}>From → To</th>
                  <th className={th}>Type</th>
                  <th className={th}>Protected</th>
                  <th className={th}>Status</th>
                </tr>
              </thead>
              <tbody>
                {linksQuery.data?.items.map((link) => (
                  <tr key={link.id} className={row}>
                    <td className={`${td} text-ink`}>
                      {siteNameById.get(link.from_site_id) ?? link.from_site_id.slice(0, 8)} →{" "}
                      {siteNameById.get(link.to_site_id) ?? link.to_site_id.slice(0, 8)}
                    </td>
                    <td className={`${td} text-muted`}>{link.type}</td>
                    <td className={`${td} text-muted`}>{link.is_protected ? "yes" : "no"}</td>
                    <td className={td}>
                      <StatusBadge status={link.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {linksQuery.data?.items.length === 0 && (
            <EmptyState icon={<Cable size={18} />} message="No links loaded yet." />
          )}
        </Card>

        <Card icon={<Smartphone size={14} />} eyebrow={`${cellsQuery.data?.total ?? 0} total`} title="Cells">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className={th}>Site</th>
                  <th className={th}>Tech</th>
                  <th className={th}>AZN/min</th>
                  <th className={th}>Status</th>
                </tr>
              </thead>
              <tbody>
                {cellsQuery.data?.items.map((cell) => (
                  <tr key={cell.id} className={row}>
                    <td className={`${td} text-ink`}>
                      {siteNameById.get(cell.site_id) ?? cell.site_id.slice(0, 8)}
                    </td>
                    <td className={`${td} text-muted`}>{cell.technology}</td>
                    <td className={`${td} mono text-muted`}>{cell.revenue_per_min_azn}</td>
                    <td className={td}>
                      <StatusBadge status={cell.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cellsQuery.data?.items.length === 0 && (
            <EmptyState icon={<Smartphone size={18} />} message="No cells loaded yet." />
          )}
        </Card>
      </div>
    </div>
  );
}
