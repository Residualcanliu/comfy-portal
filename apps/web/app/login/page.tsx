export default function Login() {
  return (
    <div className="mx-auto max-w-sm">
      <h2 className="mb-4 text-xl font-semibold">只读演示</h2>
      <p className="rounded border border-line bg-surface px-3 py-2 text-sm leading-relaxed text-muted">
        公开演示站为静态快照，不开放登录与注册，也不提供生成服务。
      </p>
      <a
        href="https://github.com/Residualcanliu/comfy-portal"
        target="_blank"
        rel="noreferrer"
        className="mt-4 inline-block text-sm text-accent hover:underline"
      >
        查看源码 ↗
      </a>
    </div>
  );
}
