import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Entrelaços · Agenda Escolar",
  description: "Agenda escolar: comunicados, calendário e atividades. Demonstração acadêmica UNIVESP 2026.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">{children}</body>
    </html>
  );
}
