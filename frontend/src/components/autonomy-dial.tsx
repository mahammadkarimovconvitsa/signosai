"use client";

import { useState } from "react";
import clsx from "clsx";
import { Bot, Check, ChevronDown, ShieldAlert, Zap } from "lucide-react";
import { configApi } from "@/lib/api";
import type { AutonomyLevel } from "@/lib/types";

const LEVELS: {
  value: AutonomyLevel;
  label: string;
  hint: string;
  icon: React.ComponentType<{ size?: number }>;
}[] = [
  {
    value: "recommend_only",
    label: "Recommend only",
    hint: "Agents propose actions; nothing executes without manual approval.",
    icon: ShieldAlert,
  },
  {
    value: "approve_to_act",
    label: "Approve to act",
    hint: "Actions wait in the queue — a human decision is always required.",
    icon: Bot,
  },
  {
    value: "auto_low_risk",
    label: "Auto (low risk)",
    hint: "Low-risk actions execute immediately; medium/high risk still wait.",
    icon: Zap,
  },
];

export function AutonomyDial({
  value,
  onChanged,
}: {
  value: AutonomyLevel;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const current = LEVELS.find((l) => l.value === value) ?? LEVELS[0];
  const CurrentIcon = current.icon;

  async function select(level: AutonomyLevel) {
    if (level === value) {
      setOpen(false);
      return;
    }
    setSaving(true);
    try {
      await configApi.updateSettings(level);
      onChanged();
    } finally {
      setSaving(false);
      setOpen(false);
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={saving}
        className="flex items-center gap-2 rounded-lg border border-line-strong bg-surface-raised py-1.5 pl-2.5 pr-2 text-[12px] font-medium text-ink-secondary hover:border-accent-line hover:text-ink disabled:opacity-60"
      >
        <CurrentIcon size={13} />
        {current.label}
        <ChevronDown size={13} className="text-muted-2" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-1.5 w-80 rounded-xl border border-line-strong bg-surface-overlay p-1.5 shadow-[var(--shadow-lg)]">
            {LEVELS.map((level) => {
              const Icon = level.icon;
              const activeLevel = level.value === value;
              return (
                <button
                  key={level.value}
                  onClick={() => select(level.value)}
                  className={clsx(
                    "flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left hover:bg-surface-raised",
                    activeLevel && "bg-accent-soft",
                  )}
                >
                  <span
                    className={clsx(
                      "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md",
                      activeLevel ? "bg-accent text-bg" : "bg-surface-raised text-muted",
                    )}
                  >
                    <Icon size={13} />
                  </span>
                  <span className="flex-1">
                    <span
                      className={clsx(
                        "block text-[13px] font-medium",
                        activeLevel ? "text-accent-strong" : "text-ink",
                      )}
                    >
                      {level.label}
                    </span>
                    <span className="mt-0.5 block text-xs text-muted">{level.hint}</span>
                  </span>
                  {activeLevel && <Check size={14} className="mt-1 shrink-0 text-accent" />}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
