"use client";

import { useState, useEffect } from "react";
import { MessageCircle, X } from "lucide-react";

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [scriptLoaded, setScriptLoaded] = useState(false);

    useEffect(() => {
        // Load ElevenLabs script only when widget is opened
        if (isOpen && !scriptLoaded) {
            const script = document.createElement("script");
            script.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
            script.async = true;
            script.onload = () => setScriptLoaded(true);
            document.body.appendChild(script);
        }
    }, [isOpen, scriptLoaded]);

    return (
        <>
            {/* Floating Toggle Button - white background, dark icon */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-white text-gray-800 rounded-full shadow-xl hover:bg-gray-50 transition-all hover:scale-105 flex items-center justify-center border border-gray-200"
                    aria-label="Open chat"
                >
                    <MessageCircle className="w-6 h-6 text-gray-700" />
                </button>
            )}

            {/* Widget Container */}
            {isOpen && (
                <div className="fixed bottom-6 right-6 z-50">
                    {/* Close Button - positioned at top-right outside widget */}
                    <button
                        onClick={() => setIsOpen(false)}
                        className="absolute -top-3 -right-3 z-[60] w-8 h-8 bg-white text-gray-700 rounded-full shadow-lg hover:bg-gray-100 transition flex items-center justify-center border border-gray-200"
                        aria-label="Close chat"
                    >
                        <X className="w-4 h-4" />
                    </button>

                    {/* ElevenLabs Widget */}
                    {/* @ts-ignore */}
                    <elevenlabs-convai agent-id="agent_7701ke5j1v4bf5evcr1nfrtygh25"></elevenlabs-convai>
                </div>
            )}
        </>
    );
}
