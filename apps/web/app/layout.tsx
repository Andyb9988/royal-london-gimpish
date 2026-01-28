import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Gimpish Reports",
  description: "Match reports with gimpified media",
};

const navItems = [
  { href: "/", label: "Home" },
  { href: "/reports", label: "Archive" },
  { href: "/admin", label: "Admin" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <header className="border-b border-slate-200 bg-white">
            <div className="container-page flex h-16 items-center justify-between">
              <Link href="/" className="text-lg font-semibold text-ink">
                Gimpish
              </Link>
              <nav className="flex items-center gap-6 text-sm text-muted">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="transition hover:text-ink"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>
          <main className="container-page py-10">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
