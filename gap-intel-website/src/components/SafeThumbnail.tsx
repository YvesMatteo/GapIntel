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

// Extract video ID from any YouTube URL format
function extractVideoId(input: string | undefined): string | null {
    if (!input) return null;

    // Already a video ID (11 chars)
    if (/^[a-zA-Z0-9_-]{11}$/.test(input)) {
        return input;
    }

    // YouTube thumbnail URL: img.youtube.com/vi/VIDEO_ID/...
    const imgMatch = input.match(/img\.youtube\.com\/vi\/([a-zA-Z0-9_-]{11})/);
    if (imgMatch) return imgMatch[1];

    // YouTube thumbnail URL: i.ytimg.com/vi/VIDEO_ID/...
    const ytimgMatch = input.match(/i\.ytimg\.com\/vi\/([a-zA-Z0-9_-]{11})/);
    if (ytimgMatch) return ytimgMatch[1];

    // youtube.com/watch?v=VIDEO_ID
    const watchMatch = input.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
    if (watchMatch) return watchMatch[1];

    // youtu.be/VIDEO_ID
    const shortMatch = input.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/);
    if (shortMatch) return shortMatch[1];

    // youtube.com/embed/VIDEO_ID
    const embedMatch = input.match(/embed\/([a-zA-Z0-9_-]{11})/);
    if (embedMatch) return embedMatch[1];

    return null;
}

export function SafeThumbnail({
    videoId,
    thumbnailUrl,
    alt,
    className = "w-full h-full object-cover",
    containerClassName = "relative w-24 aspect-video rounded-lg overflow-hidden bg-slate-100 shrink-0"
}: SafeThumbnailProps) {
    const [hasError, setHasError] = useState(false);

    // Try to get video ID from either prop
    const extractedId = videoId || extractVideoId(thumbnailUrl);

    // Build the final thumbnail URL
    let src: string | null = null;

    if (extractedId) {
        // Use YouTube's high quality thumbnail
        src = `https://i.ytimg.com/vi/${extractedId}/hqdefault.jpg`;
    } else if (thumbnailUrl) {
        // Use the provided URL directly as fallback
        src = thumbnailUrl;
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
