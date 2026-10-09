"use client";

import { useQuery } from "@tanstack/react-query";
import { Newspaper } from "lucide-react";
import { marketApi } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { MarketItemTypeBadge } from "@/components/badges";

export default function MarketPage() {
  const marketQuery = useQuery({
    queryKey: ["market", "list"],
    queryFn: () => marketApi.list({ limit: 100 }),
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Market" description="Competitor, regulator and spectrum news." />

      {marketQuery.data?.items.length === 0 ? (
        <div className="rounded-xl border border-line bg-surface/80 p-5">
          <EmptyState icon={<Newspaper size={18} />} message="No market items loaded yet." />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {marketQuery.data?.items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col gap-2.5 rounded-xl border border-line bg-surface/80 p-5 transition-colors hover:border-line-strong"
            >
              <div className="flex items-center justify-between gap-2">
                <MarketItemTypeBadge type={item.type} />
                <span className="text-xs text-muted-2">
                  {new Date(item.published_at).toLocaleDateString()}
                </span>
              </div>
              <h3 className="text-[14px] font-semibold text-ink">{item.title}</h3>
              <p className="text-[13px] leading-relaxed text-muted">{item.summary}</p>
              <span className="mt-1 text-xs text-muted-2">{item.source}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
