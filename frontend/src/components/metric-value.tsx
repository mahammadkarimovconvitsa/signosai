"use client";

import clsx from "clsx";
import { Info } from "lucide-react";
import { useExplain } from "./explain-context";
import type { Metric } from "@/lib/types";

function formatNumber(value: number, decimals = 0): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function MetricValue({
  metric,
  metricId,
  label,
  decimals = 0,
  size = "md",
  className,
}: {
  metric: Metric;
  metricId: string;
  label: string;
  decimals?: number;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}) {
  const { open } = useExplain();
  const display =
    typeof metric.value === "number" ? formatNumber(metric.value, decimals) : metric.value;

  const sizeClass = {
    sm: "text-sm",
    md: "text-2xl",
    lg: "text-3xl",
    xl: "text-[2.5rem] leading-none",
  }[size];

  return (
    <button
      type="button"
      onClick={() => open(metricId, label)}
      className={clsx(
        "mono group inline-flex items-baseline gap-1.5 text-left transition-opacity hover:opacity-85",
        className,
      )}
      title="Why this number?"
    >
      <span className={clsx("font-semibold tracking-tight text-ink", sizeClass)}>{display}</span>
      <span className="text-xs font-medium text-muted">{metric.unit}</span>
      <Info
        size={13}
        strokeWidth={2.25}
        className="shrink-0 text-accent opacity-0 transition-opacity group-hover:opacity-100"
      />
    </button>
  );
}
