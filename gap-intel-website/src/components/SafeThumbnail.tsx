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

// Extract video ID from any YouTube URL format or string
function extractVideoId(input: string | undefined): string | null {
    if (!input) return null;

    // Clean the input
    const cleaned = input.trim();

    // Already a video ID (11 chars, alphanumeric with - and _)
    if (/^[a-zA-Z0-9_-]{11}$/.test(cleaned)) {
        return cleaned;
    }

    // Try multiple patterns in order of likelihood
    const patterns = [
        // YouTube thumbnail URLs
        /img\.youtube\.com\/vi\/([a-zA-Z0-9_-]{11})/,
        /i\.ytimg\.com\/vi\/([a-zA-Z0-9_-]{11})/,
        /i[0-9]?\.ytimg\.com\/vi\/([a-zA-Z0-9_-]{11})/,
        // Standard watch URLs
        /youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})/,
        /[?&]v=([a-zA-Z0-9_-]{11})/,
        // Short URLs
        /youtu\.be\/([a-zA-Z0-9_-]{11})/,
        // Embed URLs
        /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
        // Any URL containing /vi/ (common in YouTube APIs)
        /\/vi\/([a-zA-Z0-9_-]{11})/,
        // Last resort: any 11-char sequence that looks like a video ID
        /([a-zA-Z0-9_-]{11})/,
    ];

    for (const pattern of patterns) {
        const match = cleaned.match(pattern);
        if (match) return match[1];
    }

    return null;
}

// Build thumbnail URL options for a video ID (in order of quality/reliability)
function getThumbnailUrls(videoId: string): string[] {
    return [
        `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
        `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`,
        `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
        `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
        `https://i.ytimg.com/vi/${videoId}/default.jpg`,
    ];
}

export function SafeThumbnail({
    videoId,
    thumbnailUrl,
    alt,
    className = "w-full h-full object-cover",
    containerClassName = "relative w-24 aspect-video rounded-lg overflow-hidden bg-slate-100 shrink-0"
}: SafeThumbnailProps) {
    const [urlIndex, setUrlIndex] = useState(0);
    const [allFailed, setAllFailed] = useState(false);

    // Try to get video ID from either prop
    const extractedId = videoId || extractVideoId(thumbnailUrl);

    // Build list of URLs to try
    const urlsToTry: string[] = [];

    if (extractedId) {
        urlsToTry.push(...getThumbnailUrls(extractedId));
    }

    // Add the original URL as final fallback
    if (thumbnailUrl && !urlsToTry.includes(thumbnailUrl)) {
        urlsToTry.push(thumbnailUrl);
    }

    const currentSrc = urlsToTry[urlIndex];

    const handleError = () => {
        if (urlIndex < urlsToTry.length - 1) {
            // Try next URL
            setUrlIndex(urlIndex + 1);
        } else {
            // All URLs failed
            setAllFailed(true);
        }
    };

    if (!currentSrc || allFailed) {
        return (
            <div className={`${containerClassName} flex items-center justify-center`}>
                <ImageOff className="w-5 h-5 text-slate-300" />
            </div>
        );
    }

    return (
        <div className={containerClassName}>
            <img
                src={currentSrc}
                alt={alt}
                className={className}
                onError={handleError}
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
