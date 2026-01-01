import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "Colorado 200 - Explore Colorado's Highest Peaks",
  description: "Discover and track the 200 highest peaks in Colorado. View elevations, difficulty ratings, and plan your next summit.",
  keywords: ["Colorado", "peaks", "mountains", "fourteeners", "thirteeners", "hiking", "climbing"],
  openGraph: {
    title: "Colorado 200",
    description: "Explore Colorado's 200 highest peaks",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-gray-50">
        <div className="min-h-screen flex flex-col">
          <Header />
          <main className="flex-1">
            {children}
          </main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
