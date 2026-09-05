"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    // 首次加载：读 localStorage，否则用系统偏好，默认深色
    const saved = localStorage.getItem("theme");
    const initial = saved ? saved === "dark" : true;
    setDark(initial);
    document.documentElement.classList.toggle("dark", initial);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <button
      onClick={toggle}
      aria-label="切换主题"
      className="text-sm text-muted hover:text-fg"
    >
      {dark ? "☀️" : "🌙"}
    </button>
  );
}
