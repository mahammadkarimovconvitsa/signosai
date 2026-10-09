"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  Mail,
  MapPin,
  Radio,
  ShieldCheck,
  TrendingDown,
} from "lucide-react";
import { actionsApi, analysisApi, incidentsApi, networkApi } from "@/lib/api";
import { ApiError } from "@/lib/http";
import { metricIds } from "@/lib/metric-ids";
import { useAuth } from "@/lib/auth-context";
import { Card, StatCard } from "@/components/card";
import { MetricValue } from "@/components/metric-value";
import {
  ActionStatusBadge,
  ComplianceBadge,
  IncidentStatusBadge,
  RiskBadge,
} from "@/components/badges";
import { TriggerIncidentButton } from "@/components/trigger-incident-button";
import { ResetDemoButton } from "@/components/reset-demo-button";
import type { ActionAgent, ActionOut } from "@/lib/types";

const SiteMap = dynamic(() => import("@/components/site-map").then((m) => m.SiteMap), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse rounded-lg bg-surface-raised" />,
});

const LIVE_POLL_MS = 5000;

const AGENT_ICON: Record<ActionAgent, React.ComponentType<{ size?: number }>> = {
  network: Radio,
  contracts: FileText,
  commercial: Mail,
  finance: TrendingDown,
};

export default function IncidentConsolePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const sitesQuery = useQuery({
    queryKey: ["sites", "map"],
    queryFn: () => networkApi.listSites({ limit: 500 }),
    refetchInterval: LIVE_POLL_MS,
  });

  const incidentQuery = useQuery({
    queryKey: ["incident-current"],
    queryFn: incidentsApi.current,
    retry: false,
    refetchInterval: LIVE_POLL_MS,
  });

  const incident =
    incidentQuery.error instanceof ApiError && incidentQuery.error.status === 404
      ? null
      : incidentQuery.data;
  const incidentId = incident?.id;

  const timelineQuery = useQuery({
    queryKey: ["timeline", incidentId],
    queryFn: () => incidentsApi.timeline(incidentId!),
    enabled: !!incidentId,
    refetchInterval: LIVE_POLL_MS,
  });

  const financeQuery = useQuery({
    queryKey: ["finance", incidentId],
    queryFn: () => analysisApi.finance(incidentId!),
    enabled: !!incidentId,
    refetchInterval: LIVE_POLL_MS,
  });

  const slaQuery = useQuery({
    queryKey: ["sla", incidentId],
    queryFn: () => analysisApi.sla(incidentId!),
    enabled: !!incidentId,
    refetchInterval: LIVE_POLL_MS,
  });

  const commercialQuery = useQuery({
    queryKey: ["commercial", incidentId],
    queryFn: () => analysisApi.commercial(incidentId!),
    enabled: !!incidentId,
    refetchInterval: LIVE_POLL_MS,
  });

  const actionsQuery = useQuery({
    queryKey: ["actions", incidentId],
    queryFn: () => actionsApi.list({ incident_id: incidentId!, limit: 50 }),
    enabled: !!incidentId,
    refetchInterval: LIVE_POLL_MS,
  });

  async function refreshIncidentScope() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["incident-current"] }),
      queryClient.invalidateQueries({ queryKey: ["timeline", incidentId] }),
      queryClient.invalidateQueries({ queryKey: ["actions", incidentId] }),
    ]);
  }

  const affectedSiteIds = new Set((incident?.affected_sites ?? []).map((s) => s.id));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-ink">Incident Console</h1>
          <p className="mt-0.5 text-sm text-muted">
            Live view of the network and the active incident.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {(user?.role === "admin" || user?.role === "engineer") && <TriggerIncidentButton />}
          {user?.role === "admin" && <ResetDemoButton />}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        <Card icon={<MapPin size={14} />} eyebrow="Network" title="Baku sites" className="relative col-span-2 h-[440px] !p-0 overflow-hidden">
          <div className="absolute inset-0">
            <SiteMap sites={sitesQuery.data?.items ?? []} affectedSiteIds={affectedSiteIds} />
          </div>
          <div className="pointer-events-none absolute bottom-4 left-4 z-[1000] flex items-center gap-2 rounded-lg border border-line-strong bg-surface-overlay/90 px-3 py-1.5 text-[11px] font-medium text-ink-secondary shadow-[var(--shadow-sm)] backdrop-blur-sm">
            <MapPin size={13} className="text-accent" /> Baku sites
          </div>
          <div className="pointer-events-none absolute right-4 top-4 z-[1000] flex items-center gap-3 rounded-lg border border-line-strong bg-surface-overlay/90 px-3 py-1.5 text-[11px] text-muted-2 shadow-[var(--shadow-sm)] backdrop-blur-sm">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-ok" /> Up
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-breached" /> Down
            </span>
          </div>
        </Card>

        <Card icon={<AlertTriangle size={14} />} eyebrow="Incident" title="Current incident" className="flex flex-col gap-3">
          {!incident && (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 py-10 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-ok-soft">
                <ShieldCheck size={22} className="text-ok" />
              </div>
              <div className="text-sm font-medium text-ink">All clear</div>
              {(user?.role === "admin" || user?.role === "engineer") && (
                <div className="max-w-[20ch] text-xs text-muted-2">
                  Use &quot;Trigger fiber cut&quot; above to start the demo scenario.
                </div>
              )}
            </div>
          )}
          {incident && (
            <>
              <div className="flex items-center gap-2">
                <IncidentStatusBadge status={incident.status} />
                <span className="flex items-center gap-1 text-xs text-muted">
                  <Clock size={11} />
                  since {new Date(incident.started_at).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-[13px] leading-snug text-ink">{incident.root_cause_summary}</p>
              <div className="flex items-center gap-3 text-xs text-muted-2">
                <span>{incident.affected_sites.length} affected sites</span>
                <span className="h-1 w-1 rounded-full bg-line-strong" />
                <span>{incident.alarm_count} alarms</span>
              </div>
              <EtaAndResolveControls incidentId={incident.id} onChanged={refreshIncidentScope} />
            </>
          )}
        </Card>
      </div>

      {incident && (
        <>
          <div className="grid grid-cols-4 gap-5">
            <StatCard
              eyebrow="Revenue loss / min"
              value={
                financeQuery.data && (
                  <MetricValue
                    metric={financeQuery.data.revenue_per_min_azn}
                    metricId={metricIds.financeRevenuePerMin(incident.id)}
                    label="Revenue lost per minute"
                    decimals={2}
                    size="xl"
                  />
                )
              }
            />
            <StatCard
              eyebrow="Lost revenue so far"
              value={
                financeQuery.data && (
                  <MetricValue
                    metric={financeQuery.data.lost_revenue_azn}
                    metricId={metricIds.financeLostRevenue(incident.id)}
                    label="Lost revenue"
                    decimals={0}
                    size="xl"
                  />
                )
              }
            />
            <StatCard
              eyebrow="Projected penalties"
              value={
                financeQuery.data && (
                  <MetricValue
                    metric={financeQuery.data.projected_penalties_azn}
                    metricId={metricIds.financeProjectedPenalties(incident.id)}
                    label="Projected penalties"
                    decimals={0}
                    size="xl"
                  />
                )
              }
            />
            <StatCard
              accent
              eyebrow="Total exposure"
              value={
                financeQuery.data && (
                  <MetricValue
                    metric={financeQuery.data.total_exposure_azn}
                    metricId={metricIds.financeTotalExposure(incident.id)}
                    label="Total exposure"
                    decimals={0}
                    size="xl"
                    className="text-accent-strong"
                  />
                )
              }
            />
          </div>

          <div className="grid grid-cols-2 gap-5">
            <Card icon={<FileText size={14} />} eyebrow="Contracts" title="SLA status">
              <div className="flex flex-col gap-4">
                {slaQuery.data?.length === 0 && (
                  <div className="text-sm text-muted">No contracts affected.</div>
                )}
                {slaQuery.data?.map((sla) => {
                  const pct = Math.max(
                    0,
                    Math.min(100, (sla.time_remaining_min.value as number) / 1.8),
                  );
                  const barColor =
                    sla.compliance_status === "breached"
                      ? "bg-breached"
                      : sla.compliance_status === "at_risk"
                        ? "bg-at-risk"
                        : "bg-ok";
                  return (
                    <div key={sla.contract_id} className="flex flex-col gap-2">
                      <div className="flex items-center justify-between gap-3">
                        <ComplianceBadge status={sla.compliance_status} />
                        <MetricValue
                          metric={sla.penalty_accrued_so_far_azn}
                          metricId={metricIds.slaPenaltyAccrued(incident.id, sla.contract_id)}
                          label="Penalty accrued so far"
                          decimals={0}
                          size="sm"
                        />
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-raised">
                        <div
                          className={`h-full rounded-full ${barColor} transition-all`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <MetricValue
                        metric={sla.time_remaining_min}
                        metricId={metricIds.slaTimeRemaining(incident.id, sla.contract_id)}
                        label="Time remaining"
                        decimals={0}
                        size="sm"
                      />
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card icon={<Mail size={14} />} eyebrow="Commercial" title="Affected premium subscribers">
              {commercialQuery.data && (
                <div className="flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <MetricValue
                      metric={commercialQuery.data.affected_premium_subscribers}
                      metricId={metricIds.commercialAffectedPremium(incident.id)}
                      label="Affected premium subscribers"
                      size="lg"
                    />
                    <MetricValue
                      metric={commercialQuery.data.compensation_cost_azn}
                      metricId={metricIds.commercialCompensationCost(incident.id)}
                      label="Compensation cost"
                      decimals={0}
                    />
                  </div>
                  {commercialQuery.data.sample_subscribers.length > 0 && (
                    <div className="rounded-lg bg-surface-raised px-3 py-2 text-xs text-muted">
                      e.g. {commercialQuery.data.sample_subscribers[0].name} (
                      <span className="mono">
                        {commercialQuery.data.sample_subscribers[0].msisdn_masked}
                      </span>
                      )
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>

          <Card icon={<ShieldCheck size={14} />} eyebrow="Governance" title="Approval queue">
            <ApprovalQueue actions={actionsQuery.data?.items ?? []} onChanged={refreshIncidentScope} />
          </Card>

          <Card icon={<Clock size={14} />} eyebrow="Incident" title="Timeline">
            <ol className="flex flex-col">
              {timelineQuery.data?.map((event, i) => (
                <li key={event.id} className="relative flex gap-4 pb-5 last:pb-0">
                  {i !== (timelineQuery.data?.length ?? 0) - 1 && (
                    <span className="absolute left-[5px] top-3 h-full w-px bg-line-strong" />
                  )}
                  <span className="relative z-[1] mt-1.5 h-[11px] w-[11px] shrink-0 rounded-full border-2 border-accent bg-surface" />
                  <div className="flex flex-1 flex-col gap-0.5 pb-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-semibold text-ink">{event.label}</span>
                      <span className="mono text-[11px] text-muted-2">
                        {new Date(event.ts).toLocaleTimeString()}
                      </span>
                    </div>
                    <span className="text-xs text-muted">{event.detail}</span>
                  </div>
                </li>
              ))}
            </ol>
          </Card>
        </>
      )}
    </div>
  );
}

function EtaAndResolveControls({
  incidentId,
  onChanged,
}: {
  incidentId: string;
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const [etaInput, setEtaInput] = useState("");
  const [saving, setSaving] = useState(false);
  const canAct = user?.role === "admin" || user?.role === "engineer";

  if (!canAct) return null;

  async function setEta() {
    if (!etaInput) return;
    setSaving(true);
    try {
      await incidentsApi.updateEta(incidentId, new Date(etaInput).toISOString());
      onChanged();
    } finally {
      setSaving(false);
    }
  }

  async function resolve() {
    setSaving(true);
    try {
      await incidentsApi.resolve(incidentId);
      onChanged();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-auto flex flex-col gap-2 border-t border-line pt-3">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Calendar
            size={13}
            className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-2"
          />
          <input
            type="datetime-local"
            value={etaInput}
            onChange={(e) => setEtaInput(e.target.value)}
            className="w-full rounded-lg border border-line-strong bg-surface-raised py-1.5 pl-8 pr-2 text-xs text-ink outline-none focus:border-accent"
          />
        </div>
        <button
          onClick={setEta}
          disabled={saving || !etaInput}
          className="rounded-lg border border-line-strong px-3 py-1.5 text-xs font-medium text-ink-secondary hover:border-accent-line hover:text-ink disabled:opacity-60"
        >
          Set ETA
        </button>
      </div>
      <button
        onClick={resolve}
        disabled={saving}
        className="flex items-center justify-center gap-1.5 rounded-lg bg-ok-soft py-1.5 text-xs font-semibold text-ok hover:opacity-90 disabled:opacity-60"
      >
        <CheckCircle2 size={13} />
        Mark resolved
      </button>
    </div>
  );
}

function ApprovalQueue({
  actions,
  onChanged,
}: {
  actions: ActionOut[];
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const [busyId, setBusyId] = useState<string | null>(null);

  async function act(action: ActionOut, decision: "approve" | "reject") {
    setBusyId(action.id);
    try {
      await (decision === "approve" ? actionsApi.approve(action.id) : actionsApi.reject(action.id));
      onChanged();
    } finally {
      setBusyId(null);
    }
  }

  if (actions.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <ShieldCheck size={24} className="text-muted-2" />
        <div className="text-sm text-muted">No actions proposed yet.</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {actions.map((action) => {
        const canDecide =
          action.status === "proposed" &&
          (user?.role === "admin" || user?.role === action.owner_role);
        const Icon = AGENT_ICON[action.agent];
        return (
          <div
            key={action.id}
            className="flex items-start gap-3 rounded-xl border border-line bg-surface-raised/60 p-4"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-agent-soft text-agent">
              <Icon size={15} />
            </span>
            <div className="flex flex-1 flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-agent">
                  {action.agent}
                </span>
                <ActionStatusBadge status={action.status} />
                <RiskBadge level={action.risk_level} />
              </div>
              <p className="max-w-xl text-sm text-ink">{action.proposal}</p>
              <span className="text-xs text-muted-2">Owner: {action.owner_role}</span>
            </div>
            {canDecide && (
              <div className="flex shrink-0 gap-2">
                <button
                  onClick={() => act(action, "approve")}
                  disabled={busyId === action.id}
                  className="rounded-lg bg-ok-soft px-3 py-1.5 text-xs font-semibold text-ok hover:opacity-90 disabled:opacity-60"
                >
                  Approve
                </button>
                <button
                  onClick={() => act(action, "reject")}
                  disabled={busyId === action.id}
                  className="rounded-lg bg-breached-soft px-3 py-1.5 text-xs font-semibold text-breached hover:opacity-90 disabled:opacity-60"
                >
                  Reject
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
