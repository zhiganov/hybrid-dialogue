import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { Atkinson_Hyperlegible } from "next/font/google";

const atkinson = Atkinson_Hyperlegible({
  weight: ["400", "700"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-atkinson",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Hybrid Dialogue",
  description: "A shared conversation room with Claude as a quiet facilitator.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={atkinson.variable}>
      <body>
        <header className="site-header">
          <div className="site-header-in">
            <Link className="site-name" href="/">
              Hybrid Dialogue
            </Link>
            <nav className="site-nav" aria-label="Main">
              <Link className="nav-link" href="/about">
                About
              </Link>
              <Link className="nav-link" href="/transparency">
                Under the hood
              </Link>
              <Link className="nav-cta" href="/create">
                Start a conversation
              </Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
