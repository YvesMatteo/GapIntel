'use client';

import { useState } from 'react';
import { Play } from 'lucide-react';

interface SafeThumbnailProps {
    videoId?: string;
    thumbnailUrl?: string;
    alt: string;
    className?: string;
    containerClassName?: string;
}

export function SafeThumbnail({
    videoId,
    thumbnailUrl,
    alt,
    className = "w-full h-full object-cover",
    containerClassName = "relative w-24 aspect-video rounded-xl overflow-hidden border border-slate-100 shadow-[0_2px_8px_rgb(0,0,0,0.06)] shrink-0 bg-slate-50"
}: SafeThumbnailProps) {
    const [hasError, setHasError] = useState(false);

    // Construct the thumbnail URL
    const src = thumbnailUrl || (videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : null);

    // If no valid source or error, show placeholder
    if (!src || hasError) {
        return (
            <div className={`${containerClassName} flex items-center justify-center`}>
                <div className="flex flex-col items-center justify-center text-slate-400">
                    <Play className="w-6 h-6" />
                </div>
            </div>
        );
    }

    return (
        <div className={containerClassName}>
            <img
                src={src}
                alt={alt}
                className={className}
                referrerPolicy="no-referrer"
                crossOrigin="anonymous"
                onError={() => setHasError(true)}
                loading="lazy"
            />
        </div>
    );
}

// Larger variant for thumbnail analysis section
export function SafeThumbnailLarge({
    videoId,
    thumbnailUrl,
    alt
}: SafeThumbnailProps) {
    return (
        <SafeThumbnail
            videoId={videoId}
            thumbnailUrl={thumbnailUrl}
            alt={alt}
            containerClassName="relative w-32 aspect-video rounded-xl overflow-hidden border border-slate-100 shadow-[0_2px_8px_rgb(0,0,0,0.06)] shrink-0 bg-slate-50"
        />
    );
}
