import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Chhaon (छांव) — Urban Heat Intelligence",
  description: "Urban Heat Island Forecasting and Simulation for Indian Cities",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
