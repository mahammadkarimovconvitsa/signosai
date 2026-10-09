"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronDown, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { configApi } from "@/lib/api";
import { RoleBadge } from "./badges";
import { AutonomyDial } from "./autonomy-dial";

export function Topbar() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: configApi.getSettings,
    enabled: user?.role === "admin",
  });

  const initial = user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-line bg-surface/40 px-6 backdrop-blur-sm">
      <div />
      <div className="flex items-center gap-3">
        {user?.role === "admin" && settingsQuery.data && (
          <AutonomyDial
            value={settingsQuery.data.autonomy_level}
            onChanged={() => queryClient.invalidateQueries({ queryKey: ["settings"] })}
          />
        )}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2.5 rounded-lg py-1.5 pl-1.5 pr-2.5 hover:bg-surface-raised"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-accent to-agent text-[12px] font-bold text-bg">
              {initial}
            </span>
            <span className="flex flex-col items-start leading-tight">
              <span className="text-[13px] font-medium text-ink">{user?.email}</span>
            </span>
            {user && <RoleBadge role={user.role} />}
            <ChevronDown size={14} className="text-muted-2" />
          </button>
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full z-20 mt-1.5 w-44 rounded-lg border border-line-strong bg-surface-overlay py-1 shadow-[var(--shadow-lg)]">
                <button
                  onClick={logout}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-ink-secondary hover:bg-surface-raised hover:text-ink"
                >
                  <LogOut size={14} />
                  Log out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
