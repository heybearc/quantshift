import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantShift Trading Platform",
  description: "Real-time monitoring and management for trading bots",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
