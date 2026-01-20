"use client";

import { useState, useEffect, useRef } from "react";

interface ChannelInfo {
    title: string;
    subscriberCount: string;
    subscriberCountRaw: number;
    thumbnailUrl: string;
    handle: string;
    channelId: string;
}

interface ChannelVerifierProps {
    value: string;
    onChange: (value: string) => void;
    onVerified: (info: ChannelInfo | null) => void;
    required?: boolean;
}

export default function ChannelVerifier({ value, onChange, onVerified, required }: ChannelVerifierProps) {
    const [channelInfo, setChannelInfo] = useState<ChannelInfo | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const debounceTimeout = useRef<NodeJS.Timeout | null>(null);
    const lastVerifiedValue = useRef<string>("");

    const verifyChannel = async (input: string) => {
        if (!input.trim()) {
            setChannelInfo(null);
            setError(null);
            onVerified(null);
            lastVerifiedValue.current = "";
            return;
        }

        // Don't re-verify if already verified this value
        if (input === lastVerifiedValue.current && channelInfo) {
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const res = await fetch(`/api/youtube/channel?input=${encodeURIComponent(input)}`);
            const data = await res.json();

            if (res.ok) {
                setChannelInfo(data);
                setError(null);
                onVerified(data);
                lastVerifiedValue.current = input;
            } else {
                setChannelInfo(null);
                setError(data.error || "Channel not found");
                onVerified(null);
            }
        } catch (err) {
            setChannelInfo(null);
            setError("Failed to verify channel");
            onVerified(null);
        } finally {
            setLoading(false);
        }
    };

    // Debounced verification - triggers 500ms after user stops typing
    useEffect(() => {
        if (debounceTimeout.current) {
            clearTimeout(debounceTimeout.current);
        }

        if (value.trim() && value !== lastVerifiedValue.current) {
            debounceTimeout.current = setTimeout(() => {
                verifyChannel(value);
            }, 500); // 500ms debounce
        }

        return () => {
            if (debounceTimeout.current) {
                clearTimeout(debounceTimeout.current);
            }
        };
    }, [value]);

    return (
        <div className="relative">
            <input
                type="text"
                placeholder="@YourChannelName or paste channel URL"
                value={value}
                onChange={(e) => {
                    onChange(e.target.value);
                    // Clear channel info when typing different value
                    if (e.target.value !== lastVerifiedValue.current) {
                        setChannelInfo(null);
                        onVerified(null);
                    }
                }}
                onBlur={() => verifyChannel(value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition"
                required={required}
            />

            {loading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <svg className="animate-spin h-5 w-5 text-[#9d94ff]" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                </div>
            )}

            {channelInfo && (
                <div className="mt-2 flex items-center gap-2 text-sm text-green-600">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>{channelInfo.title} • {channelInfo.subscriberCount} subscribers</span>
                </div>
            )}

            {error && (
                <div className="mt-2 text-sm text-red-500">
                    {error}
                </div>
            )}
        </div>
    );
}

export type { ChannelInfo };
