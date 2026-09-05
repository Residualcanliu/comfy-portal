"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, clearToken, getToken } from "@/lib/api";

interface Me {
  id: number;
  email: string;
  display_name: string;
}

export default function AuthNav() {
  const [me, setMe] = useState<Me | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) return;
    api<Me>("/api/auth/me")
      .then(setMe)
      .catch(() => {});
  }, []);

  function logout() {
    clearToken();
    setMe(null);
    router.push("/");
    router.refresh();
  }

  if (!me) {
    return (
      <Link href="/login" className="text-sm text-zinc-400 hover:text-zinc-100">
        登录 / 注册
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-zinc-300">{me.display_name}</span>
      <button onClick={logout} className="text-zinc-400 hover:text-zinc-100">
        退出
      </button>
    </div>
  );
}
