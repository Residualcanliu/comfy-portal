import type { Metadata } from "next";
import Link from "next/link";
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
    <html lang="zh-CN">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
        <nav className="flex items-center gap-4 border-b border-zinc-800 px-6 py-3">
          <Link href="/" className="text-lg font-bold">
            ComfyPortal
          </Link>
          <Link href="/login" className="ml-auto text-sm text-zinc-400 hover:text-zinc-100">
            登录 / 注册
          </Link>
        </nav>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
