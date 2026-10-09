"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Sidebar } from "@/components/sidebar";
import { Topbar } from "@/components/topbar";
import { ExplainProvider } from "@/components/explain-context";
import { Logo } from "@/components/logo";
import { DemoWalkthrough } from "@/components/demo-walkthrough";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex h-dvh items-center justify-center bg-bg">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-pulse">
            <Logo size={36} />
          </div>
          <div className="text-xs text-muted-2">Loading…</div>
        </div>
      </div>
    );
  }
  if (!user) {
    return null;
  }

  return (
    <ExplainProvider>
      <div className="flex h-dvh">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="min-w-0 flex-1 overflow-y-auto p-7">{children}</main>
        </div>
      </div>
      <DemoWalkthrough />
    </ExplainProvider>
  );
}
