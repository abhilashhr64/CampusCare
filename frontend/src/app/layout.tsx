import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/shared/ui/QueryProvider";

export const metadata: Metadata = {
  title: "CampusCare AI — Unified College Services & Intelligence Platform",
  description:
    "Production-oriented multi-tenant college services platform with forced PostgreSQL row-level security, offline attendance, and verified governance.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#090d16] text-slate-100 selection:bg-sky-500/30 selection:text-sky-200">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
