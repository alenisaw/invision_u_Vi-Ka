import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "inVision U — Панель приёмной комиссии",
  description: "AI-система отбора кандидатов для inVision University",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-raleway">{children}</body>
    </html>
  );
}
