// components/MediaBox.tsx
import React from "react";

interface MediaBoxProps {
    src: string | null;
    alt: string;
    fallback: React.ReactNode;
    title: string;
}

export default function MediaBox({ src, alt, fallback, title }: MediaBoxProps) {
    return (
        <div className="p-4 flex-1 flex flex-col items-center justify-center border-r border-gray-200 last:border-r-0">
            {src ? (
                <>
                    <img src={src} alt={alt} className="object-contain max-w-full max-h-[355px]" />
                </>
            ) : (
                fallback
            )}
            <p className="mt-1 text-center text-gray-700 text-sm">{title}</p>
        </div>
    );
}
