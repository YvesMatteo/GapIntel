import React from 'react';

export default function PrivacyPolicy() {
    return (
        <div className="max-w-4xl mx-auto px-6 py-12 text-slate-300">
            <h1 className="text-3xl font-bold text-white mb-8">Privacy Policy</h1>
            <p className="mb-4">Last updated: {new Date().toLocaleDateString()}</p>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">1. Introduction</h2>
                <p>Welcome to GapIntel ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. This privacy policy will inform you as to how we look after your personal data when you visit our website (gapintel.online) and use our services.</p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">2. Data We Collect</h2>
                <p className="mb-2">We may collect, use, store and transfer different kinds of personal data about you which we have grouped together follows:</p>
                <ul className="list-disc pl-6 space-y-2">
                    <li><strong>Identity Data:</strong> includes first name, last name, username or similar identifier.</li>
                    <li><strong>Contact Data:</strong> includes email address.</li>
                    <li><strong>Technical Data:</strong> includes internet protocol (IP) address, your login data, browser type and version.</li>
                    <li><strong>YouTube Data:</strong> If you connect your YouTube account, we access YouTube Analytics reports (CTR, impressions, views) and public channel information via the YouTube API Services.</li>
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">3. How We Use Your Data</h2>
                <p className="mb-2">We use your data to:</p>
                <ul className="list-disc pl-6 space-y-2">
                    <li>Provide and improve our AI analytics services.</li>
                    <li>Analyze your YouTube channel performance (specifically CTR and thumbnails).</li>
                    <li>Train our machine learning models (anonymized data only).</li>
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">4. YouTube API Services</h2>
                <p>Our application uses YouTube API Services. By using our application, you are agreeing to be bound by the <a href="https://www.youtube.com/t/terms" className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">YouTube Terms of Service</a> and <a href="https://policies.google.com/privacy" className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">Google Privacy Policy</a>. You can revoke our access to your data via the <a href="https://security.google.com/settings/security/permissions" className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">Google Security Settings page</a>.</p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">5. Contact Us</h2>
                <p>If you have any questions about this privacy policy, please contact us at: support@gapintel.online</p>
            </section>
        </div>
    );
}
