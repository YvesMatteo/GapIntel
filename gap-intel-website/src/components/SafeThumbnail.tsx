'use client';

import { useState, useEffect } from 'react';
import { ImageOff } from 'lucide-react';

interface SafeThumbnailProps {
    videoId?: string;
    thumbnailUrl?: string;
    alt: string;
    className?: string;
    containerClassName?: string;
}

// Extract video ID from various YouTube URL formats
function extractVideoId(url: string): string | null {
    if (!url) return null;

    // Already a video ID (11 chars, alphanumeric + dash/underscore)
    if (/^[a-zA-Z0-9_-]{11}$/.test(url)) {
        return url;
    }

    // youtube.com/watch?v=ID
    const watchMatch = url.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
    if (watchMatch) return watchMatch[1];

    // youtu.be/ID
    const shortMatch = url.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/);
    if (shortMatch) return shortMatch[1];

    // youtube.com/embed/ID
    const embedMatch = url.match(/embed\/([a-zA-Z0-9_-]{11})/);
    if (embedMatch) return embedMatch[1];

    // youtube.com/v/ID
    const vMatch = url.match(/\/v\/([a-zA-Z0-9_-]{11})/);
    if (vMatch) return vMatch[1];

    // Extract from img.youtube.com URL
    const imgMatch = url.match(/img\.youtube\.com\/vi\/([a-zA-Z0-9_-]{11})/);
    if (imgMatch) return imgMatch[1];

    return null;
}

// Generate thumbnail URLs with fallback chain
function getThumbnailUrls(videoId: string): string[] {
    return [
        `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`,
        `https://i.ytimg.com/vi/${videoId}/sddefault.jpg`,
        `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
        `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
        `https://img.youtube.com/vi/${videoId}/default.jpg`,
    ];
}

export function SafeThumbnail({
    videoId,
    thumbnailUrl,
    alt,
    className = "w-full h-full object-cover",
    containerClassName = "relative w-24 aspect-video rounded-xl overflow-hidden border border-slate-100 shadow-[0_2px_8px_rgb(0,0,0,0.06)] shrink-0 bg-slate-100"
}: SafeThumbnailProps) {
    const [currentUrlIndex, setCurrentUrlIndex] = useState(0);
    const [hasError, setHasError] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [urls, setUrls] = useState<string[]>([]);

    useEffect(() => {
        // Reset state when props change
        setCurrentUrlIndex(0);
        setHasError(false);
        setIsLoading(true);

        // Build URL list
        const urlList: string[] = [];

        // If we have a direct thumbnail URL, try it first
        if (thumbnailUrl && !thumbnailUrl.includes('img.youtube.com') && !thumbnailUrl.includes('i.ytimg.com')) {
            urlList.push(thumbnailUrl);
        }

        // Extract video ID from various sources
        let extractedId = videoId;
        if (!extractedId && thumbnailUrl) {
            extractedId = extractVideoId(thumbnailUrl) || undefined;
        }

        // Add YouTube thumbnail URLs if we have a video ID
        if (extractedId) {
            urlList.push(...getThumbnailUrls(extractedId));
        } else if (thumbnailUrl) {
            // Fallback to provided URL if no video ID extracted
            urlList.push(thumbnailUrl);
        }

        setUrls(urlList);
    }, [videoId, thumbnailUrl]);

    const handleError = () => {
        if (currentUrlIndex < urls.length - 1) {
            setCurrentUrlIndex(prev => prev + 1);
        } else {
            setHasError(true);
            setIsLoading(false);
        }
    };

    const handleLoad = () => {
        setIsLoading(false);
    };

    // No valid URLs available
    if (urls.length === 0 || hasError) {
        return (
            <div className={`${containerClassName} flex items-center justify-center bg-slate-100`}>
                <div className="flex flex-col items-center justify-center text-slate-400 gap-1">
                    <ImageOff className="w-5 h-5" />
                </div>
            </div>
        );
    }

    return (
        <div className={containerClassName}>
            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-100 z-10">
                    <div className="w-6 h-6 border-2 border-slate-200 border-t-slate-400 rounded-full animate-spin" />
                </div>
            )}
            <img
                src={urls[currentUrlIndex]}
                alt={alt}
                className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
                referrerPolicy="no-referrer"
                crossOrigin="anonymous"
                onError={handleError}
                onLoad={handleLoad}
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
            containerClassName="relative w-40 aspect-video rounded-xl overflow-hidden border border-slate-200 shadow-sm shrink-0 bg-slate-100"
        />
    );
}
