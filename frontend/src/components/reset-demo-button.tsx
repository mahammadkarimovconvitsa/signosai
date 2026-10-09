"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, RotateCcw } from "lucide-react";
import { adminApi } from "@/lib/api";

export function ResetDemoButton() {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  const [resetting, setResetting] = useState(false);

  async function doReset() {
    setResetting(true);
    try {
      await adminApi.reset();
      await queryClient.invalidateQueries();
      setConfirming(false);
    } finally {
      setResetting(false);
    }
  }

  if (confirming) {
    return (
      <div className="fade-in-up flex items-center gap-2 rounded-lg border border-line-strong bg-surface-raised px-2 py-1.5 text-xs">
        <span className="text-muted">Clear incidents/actions/alarms?</span>
        <button
          onClick={doReset}
          disabled={resetting}
          className="flex items-center gap-1 rounded-md bg-breached px-2.5 py-1 font-semibold text-bg hover:opacity-90 disabled:opacity-60"
        >
          {resetting && <Loader2 size={11} className="animate-spin" />}
          Confirm
        </button>
        <button
          onClick={() => setConfirming(false)}
          className="rounded-md px-2.5 py-1 font-medium text-muted hover:text-ink"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      className="flex items-center gap-1.5 rounded-lg border border-line-strong px-3 py-2 text-xs font-medium text-muted hover:border-line-strong hover:text-ink"
    >
      <RotateCcw size={13} />
      Reset demo
    </button>
  );
}
