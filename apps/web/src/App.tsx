import { useEffect, useState } from "react";

type Health = {
  status: string;
  service: string;
  version: string;
  time: string;
};

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/health", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json() as Promise<Health>;
      })
      .then(setHealth)
      .catch((reason: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(reason instanceof Error ? reason.message : String(reason));
      });

    return () => controller.abort();
  }, []);

  return (
    <main className="app">
      <h1>漫剧生成平台</h1>
      <p className="hint">前端骨架已就绪：Vite + React + TypeScript，请求经代理转发到 gateway。</p>

      <section className="card">
        <h2>后端连通性</h2>
        {error !== null && <p className="bad">未连上 gateway：{error}（先在仓库根目录执行 make dev-backend）</p>}
        {error === null && health === null && <p className="muted">检查中…</p>}
        {health !== null && (
          <dl>
            <dt>服务</dt>
            <dd>{health.service}</dd>
            <dt>状态</dt>
            <dd>{health.status}</dd>
            <dt>版本</dt>
            <dd>{health.version}</dd>
            <dt>时间</dt>
            <dd>{health.time}</dd>
          </dl>
        )}
      </section>
    </main>
  );
}
