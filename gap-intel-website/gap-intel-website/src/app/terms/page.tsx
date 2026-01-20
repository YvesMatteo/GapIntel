import React from 'react';

export default function TermsOfService() {
    return (
        <div className="max-w-4xl mx-auto px-6 py-12 text-slate-300">
            <h1 className="text-3xl font-bold text-white mb-8">Terms of Service</h1>
            <p className="mb-4">Last updated: {new Date().toLocaleDateString()}</p>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">1. Agreement to Terms</h2>
                <p>By accessing our website at gapintel.online, you agree to be bound by these terms of service, all applicable laws and regulations, and agree that you are responsible for compliance with any applicable local laws.</p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">2. Use License</h2>
                <p>Permission is granted to temporarily download one copy of the materials (information or software) on GapIntel's website for personal, non-commercial transitory viewing only.</p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">3. Disclaimer</h2>
                <p>The materials on GapIntel's website are provided on an 'as is' basis. GapIntel makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.</p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">4. YouTube Terms of Service</h2>
                <p>By using GapIntel, you also agree to be bound by the <a href="https://www.youtube.com/t/terms" className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">YouTube Terms of Service</a>.</p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">5. Limitations</h2>
                <p>In no event shall GapIntel or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on GapIntel's website.</p>
            </section>
        </div>
    );
}
