"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Play, Square, Radio, Activity, FileText, Mail, LayoutGrid, Newspaper, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface Step {
  href: string;
  label: string;
  caption: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
  ms: number;
  adminOnly?: boolean;
}

const STEPS: Step[] = [
  {
    href: "/",
    label: "Incident Console",
    caption: "Live incidents, collapsed from raw alarms down to one root cause each.",
    icon: Activity,
    ms: 5000,
  },
  {
    href: "/network",
    label: "Network",
    caption: "Every site and link on the map, colored by status in real time.",
    icon: Radio,
    ms: 4500,
  },
  {
    href: "/contracts",
    label: "Contracts",
    caption: "Enterprise customers, their sites, and SLA terms behind every exposure number.",
    icon: FileText,
    ms: 4000,
  },
  {
    href: "/commercial",
    label: "Commercial",
    caption: "SI-drafted, bilingual compensation messages for affected subscribers.",
    icon: Mail,
    ms: 4000,
  },
  {
    href: "/portfolio",
    label: "Portfolio",
    caption: "Deterministic upgrade / keep / consolidate / decommission recommendations per site.",
    icon: LayoutGrid,
    ms: 4000,
  },
  {
    href: "/market",
    label: "Market",
    caption: "Market context feeding into portfolio and commercial decisions.",
    icon: Newspaper,
    ms: 3500,
  },
  {
    href: "/audit",
    label: "Audit log",
    caption: "Every action, by every role, append-only and fully traceable.",
    icon: ShieldCheck,
    ms: 3500,
    adminOnly: true,
  },
  {
    href: "/settings",
    label: "Settings",
    caption: "Autonomy level and business constants that drive every computed metric.",
    icon: SlidersHorizontal,
    ms: 3500,
    adminOnly: true,
  },
];

export function DemoWalkthrough() {
  const { user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [running, setRunning] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [done, setDone] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const doneTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const steps = STEPS.filter((s) => !s.adminOnly || user?.role === "admin");

  const stop = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (doneTimerRef.current) clearTimeout(doneTimerRef.current);
    timerRef.current = null;
    doneTimerRef.current = null;
    setRunning(false);
    setDone(false);
  }, []);

  const start = useCallback(() => {
    setDone(false);
    setStepIndex(0);
    setRunning(true);
    router.push(steps[0]?.href ?? "/");
  }, [router, steps]);

  useEffect(() => {
    if (!running) return;
    const step = steps[stepIndex];
    if (!step) return;

    timerRef.current = setTimeout(() => {
      const next = stepIndex + 1;
      if (next < steps.length) {
        setStepIndex(next);
        router.push(steps[next].href);
      } else {
        setRunning(false);
        setDone(true);
        doneTimerRef.current = setTimeout(() => setDone(false), 2600);
      }
    }, step.ms);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, stepIndex]);

  useEffect(() => stop, [stop]);

  if (pathname === "/login") return null;

  const current = steps[stepIndex];

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-6 z-50 flex justify-center px-4">
      <AnimatePresence mode="wait">
        {!running && !done && (
          <motion.button
            key="start"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10, scale: 0.92 }}
            transition={{ duration: 0.2 }}
            onClick={start}
            className="pointer-events-auto flex items-center gap-2 rounded-full border border-line-strong bg-surface-overlay px-4 py-2.5 text-[13px] font-medium text-ink shadow-[var(--shadow-lg)] transition-colors hover:border-accent-line hover:text-accent-strong"
          >
            <Play size={14} className="text-accent" />
            Start demo walkthrough
          </motion.button>
        )}

        {running && current && (
          <motion.div
            key="running"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.2 }}
            className="pointer-events-auto flex w-full max-w-xl items-center gap-3 rounded-2xl border border-line-strong bg-surface-overlay/95 px-4 py-3 shadow-[var(--shadow-lg)] backdrop-blur-sm"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent">
              <current.icon size={16} strokeWidth={2.25} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-ink">{current.label}</span>
                <span className="mono text-[10px] text-muted-2">
                  {stepIndex + 1} / {steps.length}
                </span>
              </div>
              <p className="truncate text-[12px] text-ink-secondary">{current.caption}</p>
              <div className="mt-1.5 h-[3px] w-full overflow-hidden rounded-full bg-line">
                <motion.div
                  key={stepIndex}
                  className="h-full rounded-full bg-accent"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: current.ms / 1000, ease: "linear" }}
                />
              </div>
            </div>
            <button
              onClick={stop}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-2 transition-colors hover:bg-surface-raised hover:text-breached"
              title="Stop walkthrough"
            >
              <Square size={13} />
            </button>
          </motion.div>
        )}

        {done && (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.2 }}
            className="pointer-events-auto rounded-full border border-ok-line bg-ok-soft px-4 py-2.5 text-[13px] font-medium text-ok"
          >
            Walkthrough complete
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
