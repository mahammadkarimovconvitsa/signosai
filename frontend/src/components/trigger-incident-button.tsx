"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, MapPinOff, Zap } from "lucide-react";
import { alarmsApi, networkApi } from "@/lib/api";
import type { SiteOut } from "@/lib/types";

export function TriggerIncidentButton() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [firing, setFiring] = useState(false);
  // Belt-and-suspenders against a double-fire: a ref flips synchronously
  // (state updates don't), so a second click in the same tick can't slip
  // through before `firing`/`disabled` re-renders.
  const firingRef = useRef(false);

  const sitesQuery = useQuery({
    queryKey: ["sites", "all-for-trigger"],
    queryFn: () => networkApi.listSites({ limit: 500 }),
    enabled: open,
  });

  const candidateSites = (sitesQuery.data?.items ?? []).filter(
    (s: SiteOut) => s.uplink_link_id,
  );

  async function fire(site: SiteOut) {
    if (firingRef.current) return;
    firingRef.current = true;
    setOpen(false);
    setFiring(true);
    try {
      const now = new Date().toISOString();
      await alarmsApi.ingest(
        Array.from({ length: 10 }, () => ({
          timestamp: now,
          site_id: site.id,
          severity: "critical",
          type: "fiber_cut",
        })),
      );
      await queryClient.invalidateQueries({ queryKey: ["incident-current"] });
      await queryClient.invalidateQueries({ queryKey: ["sites"] });
    } finally {
      firingRef.current = false;
      setFiring(false);
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={firing}
        className="flex items-center gap-1.5 rounded-lg border border-breached-line bg-breached-soft px-3 py-2 text-xs font-semibold text-breached transition-colors hover:border-breached hover:bg-breached/20 disabled:opacity-60"
      >
        {firing ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
        Trigger fiber cut
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="fade-in-up absolute right-0 top-full z-20 mt-1.5 max-h-80 w-80 overflow-y-auto rounded-xl border border-line-strong bg-surface-overlay p-1.5 shadow-[var(--shadow-lg)]">
            <div className="px-2.5 py-2 text-xs font-medium text-muted">
              Pick a site to cut — sends 10 critical <span className="mono">fiber_cut</span>{" "}
              alarms
            </div>
            {sitesQuery.isLoading && (
              <div className="px-2.5 py-3 text-xs text-muted">Loading sites…</div>
            )}
            {sitesQuery.data && candidateSites.length === 0 && (
              <div className="flex items-center gap-2 px-2.5 py-3 text-xs text-muted">
                <MapPinOff size={14} />
                No sites with an uplink link found — load reference data first.
              </div>
            )}
            {candidateSites.map((site) => (
              <button
                key={site.id}
                disabled={firing}
                onClick={() => fire(site)}
                className="w-full rounded-lg px-2.5 py-2 text-left text-sm hover:bg-surface-raised disabled:opacity-60"
              >
                <div className="font-medium text-ink">{site.name}</div>
                <div className="text-xs text-muted">{site.district}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
