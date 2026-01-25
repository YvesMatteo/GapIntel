'use client';

import { useState } from 'react';
import { ImageOff } from 'lucide-react';

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
    containerClassName = "relative w-24 aspect-video rounded-lg overflow-hidden bg-slate-100 shrink-0"
}: SafeThumbnailProps) {
    const [hasError, setHasError] = useState(false);

    // Build the thumbnail URL
    let src = thumbnailUrl;

    // If no thumbnail URL but we have videoId, use YouTube's thumbnail
    if (!src && videoId) {
        src = `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
    }

    // Extract video ID from YouTube thumbnail URL if needed
    if (!src && thumbnailUrl) {
        const match = thumbnailUrl.match(/\/vi\/([a-zA-Z0-9_-]{11})/);
        if (match) {
            src = `https://i.ytimg.com/vi/${match[1]}/hqdefault.jpg`;
        }
    }

    if (!src || hasError) {
        return (
            <div className={`${containerClassName} flex items-center justify-center`}>
                <ImageOff className="w-5 h-5 text-slate-300" />
            </div>
        );
    }

    return (
        <div className={containerClassName}>
            <img
                src={src}
                alt={alt}
                className={className}
                onError={() => setHasError(true)}
                loading="lazy"
                referrerPolicy="no-referrer"
            />
        </div>
    );
}

export function SafeThumbnailLarge({ videoId, thumbnailUrl, alt }: SafeThumbnailProps) {
    return (
        <SafeThumbnail
            videoId={videoId}
            thumbnailUrl={thumbnailUrl}
            alt={alt}
            containerClassName="relative w-36 aspect-video rounded-lg overflow-hidden bg-slate-100 shrink-0"
        />
    );
}
