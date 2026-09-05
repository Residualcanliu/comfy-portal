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
        <nav className="sticky top-0 z-10 flex items-center gap-4 border-b border-line bg-bg/80 px-6 py-3 backdrop-blur">
          <Link
            href="/"
            className="bg-gradient-to-r from-violet-500 to-blue-500 bg-clip-text text-lg font-bold text-transparent"
          >
            ComfyPortal
          </Link>
          <div className="ml-auto flex items-center gap-4">
            <ThemeToggle />
            <AuthNav />
          </div>
        </nav>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
