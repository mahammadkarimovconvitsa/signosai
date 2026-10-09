export function EmptyState({
  icon,
  message,
}: {
  icon: React.ReactNode;
  message: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2.5 py-10 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-raised text-muted-2">
        {icon}
      </span>
      <div className="text-sm text-muted">{message}</div>
    </div>
  );
}
