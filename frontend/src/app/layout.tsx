import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function AgrisightLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={`${geistSans.variable} ${geistMono.variable} flex flex-col items-center justify-center min-h-screen font-mono overflow-hidden`}>
        <header
          className="w-full max-w-[640px] bg-white shadow-lg p-4 text-center font-semibold text-gray-700 text-2xl font-mono tracking-wider rounded-lg fixed top-8">
          <p>Agricultural image analyzer</p>
        </header>
        <main className="w-full max-w-[1100px] px-12 py-7 bg-white rounded-lg shadow-lg my-28 flex flex-col h-[calc(100vh-180px)]">
          <small className='text-center pb-4 text-gray-500'>
            농업 관련 인공위성 이미지를 입력하여 Segformer Baseline 모델과 Optimized 모델 비교
          </small>
          {children}
        </main>
        <footer className="w-full text-center p-4 text-gray-500 mt-6 shadow-md fixed bottom-0">
          &copy; 2025 Hjey Website. All rights reserved.
        </footer>
      </body>
    </html>
  );
}
