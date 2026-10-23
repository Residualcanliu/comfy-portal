"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");
  const [demo, setDemo] = useState(false);

  // 只读演示站关闭注册：默认落在登录态，并隐藏切换入口
  useEffect(() => {
    api<{ readonly_demo: boolean }>("/api/status")
      .then((s) => {
        setDemo(s.readonly_demo);
        if (s.readonly_demo) setMode("login");
      })
      .catch(() => {});
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body =
        mode === "login"
          ? { email, password }
          : { email, password, display_name: name };
      const res = await api<{ access_token: string }>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setToken(res.access_token);
      router.push("/");
      router.refresh();
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  const inputCls =
    "w-full rounded border border-line bg-surface px-3 py-2 text-sm text-fg placeholder:text-muted";

  return (
    <div className="mx-auto max-w-sm">
      <h2 className="mb-4 text-xl font-semibold">
        {mode === "login" ? "登录" : "注册"}
      </h2>
      {demo && (
        <p className="mb-4 rounded border border-line bg-surface px-3 py-2 text-sm text-muted">
          公开演示站为只读模式，不开放注册。
        </p>
      )}
      <form onSubmit={submit} className="space-y-3">
        {mode === "register" && (
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="昵称"
            className={inputCls}
          />
        )}
        <input
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="账号 / 邮箱"
          className={inputCls}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码（至少 6 位）"
          className={inputCls}
        />
        {err && <p className="text-sm text-red-400">{err}</p>}
        <button className="w-full rounded bg-gradient-to-r from-violet-500 to-blue-500 py-2 font-medium text-white transition hover:opacity-90">
          {mode === "login" ? "登录" : "注册"}
        </button>
      </form>
      {!demo && (
        <button
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="mt-3 text-sm text-muted hover:text-fg"
        >
          {mode === "login" ? "没有账号？去注册" : "已有账号？去登录"}
        </button>
      )}
    </div>
  );
}
