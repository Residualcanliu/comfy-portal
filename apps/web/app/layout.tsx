import type { Metadata } from "next";
import Link from "next/link";
import AuthNav from "@/components/AuthNav";
import ThemeToggle from "@/components/ThemeToggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "ComfyPortal",
  description: "自托管 ComfyUI 图像生成门户",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="min-h-screen bg-bg text-fg antialiased">
        <div className="aurora" aria-hidden="true">
          <div className="aurora__blob aurora__blob--1" />
          <div className="aurora__blob aurora__blob--2" />
          <div className="aurora__blob aurora__blob--3" />
          <div className="aurora__beam" />
        </div>
        <nav className="sticky top-0 z-10 flex items-center gap-6 border-b border-line bg-bg/80 px-6 py-3 backdrop-blur">
          <Link
            href="/"
            className="bg-gradient-to-r from-violet-500 to-blue-500 bg-clip-text text-lg font-black text-transparent"
          >
            ComfyPortal
          </Link>
          <div className="hidden items-center gap-5 text-sm md:flex">
            <Link href="/#workflows" className="text-muted transition hover:text-fg">
              工作流
            </Link>
            <Link href="/#gallery" className="text-muted transition hover:text-fg">
              画廊
            </Link>
          </div>
          <div className="ml-auto flex items-center gap-4">
            <ThemeToggle />
            <AuthNav />
            <Link
              href="/#workflows"
              className="rounded-full bg-gradient-to-r from-violet-500 to-blue-500 px-4 py-1.5 text-sm font-semibold text-white transition hover:opacity-90"
            >
              开始生成
            </Link>
          </div>
        </nav>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="border-t border-line px-6 py-8 text-center text-sm text-muted">
          <p>© 2026 ComfyPortal · 自托管 ComfyUI 图像生成门户</p>
        </footer>
      </body>
    </html>
  );
}
