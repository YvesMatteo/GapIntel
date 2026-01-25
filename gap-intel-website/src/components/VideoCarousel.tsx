'use client';

import { useRef, useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, MessageCircle, ExternalLink } from 'lucide-react';
import { SafeThumbnail } from './SafeThumbnail';

interface Video {
    title: string;
    comments: number;
    url: string;
    videoId?: string;
    thumbnail?: string;
}

interface VideoCarouselProps {
    videos: Video[];
}

export function VideoCarousel({ videos }: VideoCarouselProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [canScrollLeft, setCanScrollLeft] = useState(false);
    const [canScrollRight, setCanScrollRight] = useState(true);

    const checkScrollPosition = () => {
        if (scrollRef.current) {
            const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
            setCanScrollLeft(scrollLeft > 0);
            setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
        }
    };

    useEffect(() => {
        checkScrollPosition();
        const ref = scrollRef.current;
        if (ref) {
            ref.addEventListener('scroll', checkScrollPosition);
            return () => ref.removeEventListener('scroll', checkScrollPosition);
        }
    }, [videos]);

    const scroll = (direction: 'left' | 'right') => {
        if (scrollRef.current) {
            const scrollAmount = 320;
            scrollRef.current.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
        }
    };

    if (videos.length === 0) return null;

    return (
        <div className="relative group/carousel">
            {/* Scroll Buttons */}
            {canScrollLeft && (
                <button
                    onClick={() => scroll('left')}
                    className="absolute left-0 top-1/2 -translate-y-1/2 z-20 w-12 h-12 bg-white/90 backdrop-blur-sm rounded-full shadow-lg border border-slate-200/50 flex items-center justify-center text-slate-600 hover:text-slate-900 hover:bg-white transition-all opacity-0 group-hover/carousel:opacity-100 -translate-x-4 group-hover/carousel:translate-x-2"
                >
                    <ChevronLeft className="w-5 h-5" />
                </button>
            )}
            {canScrollRight && (
                <button
                    onClick={() => scroll('right')}
                    className="absolute right-0 top-1/2 -translate-y-1/2 z-20 w-12 h-12 bg-white/90 backdrop-blur-sm rounded-full shadow-lg border border-slate-200/50 flex items-center justify-center text-slate-600 hover:text-slate-900 hover:bg-white transition-all opacity-0 group-hover/carousel:opacity-100 translate-x-4 group-hover/carousel:-translate-x-2"
                >
                    <ChevronRight className="w-5 h-5" />
                </button>
            )}

            {/* Gradient Fades */}
            {canScrollLeft && (
                <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-[#FAFAFA] to-transparent z-10 pointer-events-none" />
            )}
            {canScrollRight && (
                <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-[#FAFAFA] to-transparent z-10 pointer-events-none" />
            )}

            {/* Scrollable Container */}
            <div
                ref={scrollRef}
                className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth pb-2"
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
            >
                {videos.map((video, i) => (
                    <a
                        key={i}
                        href={video.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-shrink-0 w-72 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 overflow-hidden group"
                    >
                        <div className="relative aspect-video w-full bg-slate-50 overflow-hidden">
                            <SafeThumbnail
                                videoId={video.videoId}
                                thumbnailUrl={video.thumbnail}
                                alt={video.title}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                containerClassName="relative w-full h-full"
                            />
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                            <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="w-8 h-8 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm">
                                    <ExternalLink className="w-4 h-4 text-slate-600" />
                                </div>
                            </div>
                        </div>
                        <div className="p-4">
                            <h3 className="font-medium text-slate-900 text-sm line-clamp-2 leading-snug mb-2 group-hover:text-blue-600 transition-colors">
                                {video.title}
                            </h3>
                            <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                <MessageCircle className="w-3.5 h-3.5" />
                                <span>{video.comments.toLocaleString()} comments</span>
                            </div>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    );
}
