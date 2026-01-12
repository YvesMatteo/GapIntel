"use client";

import { Share2, Download, Check, Copy } from "lucide-react";
import { useState } from "react";

interface ReportActionsProps {
    channelName: string;
    accessKey: string;
}

export default function ReportActions({ channelName, accessKey }: ReportActionsProps) {
    const [copied, setCopied] = useState(false);

    const handleExportPDF = () => {
        // Use browser print functionality with print styles
        window.print();
    };

    const handleShare = async () => {
        const shareUrl = `${window.location.origin}/report/${accessKey}`;
        const shareData = {
            title: `GAP Intel Report - ${channelName}`,
            text: `Check out this content strategy report for ${channelName}`,
            url: shareUrl,
        };

        // Try native share first (mobile)
        if (navigator.share && typeof navigator.share === 'function') {
            try {
                await navigator.share(shareData);
                return;
            } catch (err) {
                // User cancelled or share failed, fall back to clipboard
            }
        }

        // Fallback: Copy to clipboard
        try {
            await navigator.clipboard.writeText(shareUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            // Final fallback: show URL in alert
            alert(`Share this link: ${shareUrl}`);
        }
    };

    return (
        <div className="flex gap-3">
            <button
                onClick={handleShare}
                className="h-12 w-12 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-50 bg-white shadow-sm transition"
                title={copied ? "Copied!" : "Share Report"}
            >
                {copied ? <Check className="w-5 h-5 text-green-500" /> : <Share2 className="w-5 h-5" />}
            </button>
            <button
                onClick={handleExportPDF}
                className="h-12 px-6 rounded-full bg-slate-900 text-white font-medium hover:bg-slate-800 shadow-xl shadow-slate-900/10 transition flex items-center gap-2"
            >
                <Download className="w-4 h-4" /> Export PDF
            </button>
        </div>
    );
}
