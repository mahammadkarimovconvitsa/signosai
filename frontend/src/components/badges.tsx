import clsx from "clsx";
import type {
  ActionStatus,
  AlarmSeverity,
  ComplianceStatus,
  IncidentStatus,
  OperationalStatus,
  RiskLevel,
} from "@/lib/types";

function Chip({
  children,
  className,
  dot,
  outline,
}: {
  children: React.ReactNode;
  className?: string;
  dot?: string;
  outline?: boolean;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide whitespace-nowrap",
        outline && "border",
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: dot }} />}
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: OperationalStatus }) {
  return status === "up" ? (
    <Chip className="bg-ok-soft text-ok" dot="var(--ok)">
      Up
    </Chip>
  ) : (
    <Chip className="bg-breached-soft text-breached" dot="var(--breached)">
      <span className="pulse-live h-1.5 w-1.5 rounded-full bg-breached" />
      Down
    </Chip>
  );
}

export function ComplianceBadge({ status }: { status: ComplianceStatus }) {
  const map: Record<ComplianceStatus, { cls: string; dot: string; label: string }> = {
    ok: { cls: "bg-ok-soft text-ok", dot: "var(--ok)", label: "On track" },
    at_risk: { cls: "bg-at-risk-soft text-at-risk", dot: "var(--at-risk)", label: "At risk" },
    breached: { cls: "bg-breached-soft text-breached", dot: "var(--breached)", label: "Breached" },
  };
  const m = map[status];
  return (
    <Chip className={m.cls} dot={m.dot}>
      {m.label}
    </Chip>
  );
}

export function SeverityBadge({ severity }: { severity: AlarmSeverity }) {
  const map: Record<AlarmSeverity, string> = {
    critical: "bg-breached-soft text-sev-critical",
    major: "bg-at-risk-soft text-sev-major",
    minor: "bg-at-risk-soft text-sev-minor",
    warning: "bg-accent-soft text-sev-warning",
  };
  return <Chip className={map[severity]}>{severity}</Chip>;
}

export function IncidentStatusBadge({ status }: { status: IncidentStatus }) {
  return status === "open" ? (
    <Chip className="bg-breached-soft text-breached">
      <span className="pulse-live h-1.5 w-1.5 rounded-full bg-breached" />
      Open
    </Chip>
  ) : (
    <Chip className="bg-ok-soft text-ok" dot="var(--ok)">
      Resolved
    </Chip>
  );
}

export function ActionStatusBadge({ status }: { status: ActionStatus }) {
  const map: Record<ActionStatus, { cls: string; dot: string }> = {
    proposed: { cls: "bg-at-risk-soft text-at-risk", dot: "var(--at-risk)" },
    approved: { cls: "bg-ok-soft text-ok", dot: "var(--ok)" },
    rejected: { cls: "bg-breached-soft text-breached", dot: "var(--breached)" },
    executed: { cls: "bg-accent-soft text-accent", dot: "var(--accent)" },
  };
  const m = map[status];
  return (
    <Chip className={m.cls} dot={m.dot}>
      {status}
    </Chip>
  );
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  const map: Record<RiskLevel, string> = {
    low: "bg-ok-soft text-ok",
    medium: "bg-at-risk-soft text-at-risk",
    high: "bg-breached-soft text-breached",
  };
  return <Chip className={map[level]}>{level} risk</Chip>;
}

export function RoleBadge({ role }: { role: string }) {
  return (
    <Chip className="border-line-strong bg-surface-overlay text-ink-secondary" outline>
      {role.replace("_", " ")}
    </Chip>
  );
}

export function PortfolioRecommendationBadge({
  recommendation,
}: {
  recommendation: "upgrade" | "keep" | "consolidate" | "decommission";
}) {
  const map: Record<string, { cls: string; dot: string }> = {
    upgrade: { cls: "bg-ok-soft text-ok", dot: "var(--ok)" },
    keep: { cls: "bg-accent-soft text-accent", dot: "var(--accent)" },
    consolidate: { cls: "bg-at-risk-soft text-at-risk", dot: "var(--at-risk)" },
    decommission: { cls: "bg-breached-soft text-breached", dot: "var(--breached)" },
  };
  const m = map[recommendation];
  return (
    <Chip className={m.cls} dot={m.dot}>
      {recommendation}
    </Chip>
  );
}

export function MarketItemTypeBadge({ type }: { type: string }) {
  return <Chip className="bg-agent-soft text-agent">{type.replace("_", " ")}</Chip>;
}

export function AgentBadge({ agent }: { agent: string }) {
  return (
    <Chip className="bg-agent-soft text-agent" dot="var(--agent)">
      {agent}
    </Chip>
  );
}
