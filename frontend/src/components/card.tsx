import clsx from "clsx";

export function Card({
  children,
  className,
  title,
  eyebrow,
  action,
  icon,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
  eyebrow?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div
      className={clsx(
        "rounded-xl border border-line bg-surface/80 p-5 shadow-[var(--shadow-sm)] backdrop-blur-sm",
        className,
      )}
    >
      {(title || eyebrow || action) && (
        <div className="mb-4 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            {icon && (
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-raised text-muted">
                {icon}
              </span>
            )}
            <div>
              {eyebrow && <div className="label">{eyebrow}</div>}
              {title && <h3 className="text-[13px] font-semibold text-ink">{title}</h3>}
            </div>
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function StatCard({
  eyebrow,
  value,
  accent = false,
  children,
}: {
  eyebrow: string;
  value: React.ReactNode;
  accent?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div
      className={clsx(
        "relative overflow-hidden rounded-xl border p-5",
        accent
          ? "border-accent-line bg-gradient-to-br from-accent-soft to-surface shadow-[var(--glow-accent)]"
          : "border-line bg-surface/80",
      )}
    >
      <div className="label">{eyebrow}</div>
      <div className="mt-2">{value}</div>
      {children}
    </div>
  );
}
