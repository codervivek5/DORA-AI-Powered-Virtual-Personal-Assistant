import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "../styles/background.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "DORA AI - Your AI-Powered Virtual Personal Assistant",
  description: "DORA AI is an intelligent virtual personal assistant designed to streamline your daily tasks, manage your schedule, and help you stay organized effortlessly.",
  manifest: "/favicon/site.webmanifest",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/favicon/site.webmanifest" />
        <meta name="theme-color" content="#0B0B2F" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased gradient-background`}
      >
        {children}
      </body>
    </html>
  );
}
