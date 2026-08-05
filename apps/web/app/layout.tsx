import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LunaTraverse | Lunar Ice & Traverse Planner",
  description: "Chandrayaan-2-inspired lunar south-polar mission planning workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
