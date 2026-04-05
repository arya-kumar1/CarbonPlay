import "./globals.css";
import { Toaster } from "react-hot-toast";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sustainable Sports Scheduler",
  description: "Carbon-optimized schedule analytics dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <ThemeProvider>
          <QueryProvider>
            {children}
            <Toaster position="top-right" toastOptions={{ style: { borderRadius: 12 } }} />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
