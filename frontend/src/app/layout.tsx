import type { Metadata } from "next";
import "./globals.css";
import ThemeProvider from "@/components/providers/ThemeProvider";

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
    <html lang="ru" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-raleway">
        <ThemeProvider
          attribute="data-theme"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}