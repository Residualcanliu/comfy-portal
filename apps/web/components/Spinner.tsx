export default function Spinner({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <span
      className={`inline-block animate-spin rounded-full border-2 border-current/25 border-t-current ${className}`}
      role="status"
      aria-label="加载中"
    />
  );
}
