"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Database, Sigma, X } from "lucide-react";
import { explainApi } from "@/lib/api";

interface ExplainContextValue {
  open: (metricId: string, label: string) => void;
}

const ExplainContext = createContext<ExplainContextValue | null>(null);

export function ExplainProvider({ children }: { children: React.ReactNode }) {
  const [target, setTarget] = useState<{ metricId: string; label: string } | null>(null);

  const open = useCallback((metricId: string, label: string) => {
    setTarget({ metricId, label });
  }, []);
  const close = useCallback(() => setTarget(null), []);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["explain", target?.metricId],
    queryFn: () => explainApi.get(target!.metricId),
    enabled: !!target,
  });

  return (
    <ExplainContext.Provider value={{ open }}>
      {children}
      {target && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-[2px]" onClick={close} />
          <div className="fade-in-up relative h-full w-full max-w-md overflow-y-auto border-l border-line-strong bg-surface-overlay shadow-[var(--shadow-lg)]">
            <div className="sticky top-0 flex items-start justify-between gap-4 border-b border-line bg-surface-overlay/95 p-6 backdrop-blur-sm">
              <div>
                <div className="label flex items-center gap-1.5 text-accent">
                  <Sigma size={12} />
                  Why this number
                </div>
                <h2 className="mt-1.5 text-lg font-semibold text-ink">{target.label}</h2>
              </div>
              <button
                onClick={close}
                className="rounded-lg p-1.5 text-muted hover:bg-surface-raised hover:text-ink"
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6">
              {isLoading && (
                <div className="flex flex-col gap-3">
                  <div className="h-10 w-32 animate-pulse rounded-lg bg-surface-raised" />
                  <div className="h-16 animate-pulse rounded-lg bg-surface-raised" />
                  <div className="h-24 animate-pulse rounded-lg bg-surface-raised" />
                </div>
              )}
              {isError && (
                <p className="rounded-lg border border-breached-line bg-breached-soft p-3 text-sm text-breached">
                  {error instanceof Error ? error.message : "Failed to load explanation"}
                </p>
              )}
              {data && (
                <div className="flex flex-col gap-6">
                  <div className="rounded-xl border border-accent-line bg-gradient-to-br from-accent-soft to-transparent p-4">
                    <div className="label">Value</div>
                    <div className="mono mt-1 text-3xl font-bold tracking-tight text-ink">
                      {typeof data.value === "number" ? data.value.toLocaleString() : data.value}{" "}
                      <span className="text-sm font-normal text-muted">{data.unit}</span>
                    </div>
                  </div>

                  <div>
                    <div className="label mb-1.5">Formula</div>
                    <div className="mono rounded-lg bg-surface-raised p-3 text-[13px] leading-relaxed text-ink-secondary">
                      {data.formula}
                    </div>
                  </div>

                  {Object.keys(data.inputs).length > 0 && (
                    <div>
                      <div className="label mb-1.5">Inputs</div>
                      <dl className="flex flex-col gap-0 overflow-hidden rounded-lg border border-line">
                        {Object.entries(data.inputs).map(([k, v], i) => (
                          <div
                            key={k}
                            className={
                              "mono flex justify-between gap-4 px-3 py-2 text-xs " +
                              (i % 2 === 0 ? "bg-surface-raised" : "")
                            }
                          >
                            <dt className="text-muted">{k}</dt>
                            <dd className="break-all text-right text-ink-secondary">{String(v)}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  )}

                  {data.sources.length > 0 && (
                    <div>
                      <div className="label mb-1.5 flex items-center gap-1.5">
                        <Database size={11} />
                        Source rows ({data.sources.length})
                      </div>
                      <ul className="flex flex-col gap-1">
                        {data.sources.map((s, i) => (
                          <li
                            key={i}
                            className="mono rounded-md bg-surface-raised px-2.5 py-1.5 text-[11px] text-muted"
                          >
                            <span className="text-ink-secondary">{s.table}</span>
                            <span className="text-muted-2">:{s.id}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </ExplainContext.Provider>
  );
}

export function useExplain(): ExplainContextValue {
  const ctx = useContext(ExplainContext);
  if (!ctx) throw new Error("useExplain must be used within ExplainProvider");
  return ctx;
}
