'use client';

import React from 'react';

// Hook types and their CTR boost percentages (from Skill 7)
export const HOOK_PATTERNS = {
    number: {
        name: 'Number Hook',
        emoji: '🔢',
        ctrBoost: 35,
        score: 10,
        description: '"7 Ways...", "5 Secrets..."',
        regex: /\d+\s*(ways|tips|secrets|rules|steps|hacks|reasons|things|mistakes|strategies)/i
    },
    how_to: {
        name: 'How-To',
        emoji: '📖',
        ctrBoost: 28,
        score: 7,
        description: '"How to [Action]..."',
        test: (title: string) => title.toLowerCase().startsWith('how to')
    },
    ultimate_guide: {
        name: 'Authority Guide',
        emoji: '👑',
        ctrBoost: 22,
        score: 5,
        description: '"Ultimate Guide...", "Complete..."',
        regex: /ultimate|complete|definitive|comprehensive/i
    },
    question: {
        name: 'Question Hook',
        emoji: '❓',
        ctrBoost: 20,
        score: 8,
        description: '"Why...?", "What if...?"',
        test: (title: string) => title.includes('?')
    },
    comparison: {
        name: 'Comparison',
        emoji: '⚔️',
        ctrBoost: 18,
        score: 6,
        description: '"X vs Y"',
        regex: /\svs\.?\s/i
    },
    year: {
        name: 'Year Reference',
        emoji: '📅',
        ctrBoost: 15,
        score: 0, // Bonus, not standalone
        description: '"... 2025"',
        regex: /202[4-9]/
    },
    curiosity: {
        name: 'Curiosity Gap',
        emoji: '🤫',
        ctrBoost: 12,
        score: 0, // Bonus
        description: '"You won\'t believe...", "Secret..."',
        regex: /you (won't|didn't|don't) know|secret|hidden|truth|nobody tells/i
    },
    standard: {
        name: 'Standard',
        emoji: '📝',
        ctrBoost: 0,
        score: 3,
        description: 'Direct title without hook'
    }
};

export interface TitleAnalysis {
    hookType: keyof typeof HOOK_PATTERNS;
    hookName: string;
    hookEmoji: string;
    thss: number; // Title Hook Strength Score (0-10)
    tse: number; // Title Structure Effectiveness (0-10)
    ctrBoost: number; // Expected CTR boost %
    lengthScore: number; // 0-10
    lengthValue: number;
    lengthStatus: 'short' | 'optimal' | 'long' | 'truncated';
    keywordPosition: 'front' | 'middle' | 'back';
    keywordPositionScore: number;
    curiosityBonus: boolean;
    yearBonus: boolean;
    overallScore: number; // 0-100
    issues: string[];
    strengths: string[];
}

export function analyzeTitleHook(title: string): keyof typeof HOOK_PATTERNS {
    const patterns = HOOK_PATTERNS;

    if (patterns.number.regex!.test(title)) return 'number';
    if (patterns.how_to.test!(title)) return 'how_to';
    if (patterns.question.test!(title)) return 'question';
    if (patterns.comparison.regex!.test(title)) return 'comparison';
    if (patterns.ultimate_guide.regex!.test(title)) return 'ultimate_guide';

    return 'standard';
}

export function calculateTHSS(title: string): number {
    const hookType = analyzeTitleHook(title);
    let score = HOOK_PATTERNS[hookType].score;

    // Curiosity bonus
    if (HOOK_PATTERNS.curiosity.regex!.test(title)) score += 1;

    // Year bonus
    if (HOOK_PATTERNS.year.regex!.test(title)) score += 0.5;

    // Emotional triggers bonus
    if (/shocking|insane|crazy|unbelievable|incredible/i.test(title)) score += 0.5;

    return Math.min(10, score);
}

export function calculateTSE(title: string): { score: number; length: number; lengthScore: number; lengthStatus: string } {
    const length = title.length;

    // Length optimization (from Skill 7 research)
    let lengthScore: number;
    let lengthStatus: string;

    if (length >= 50 && length <= 60) {
        lengthScore = 10;
        lengthStatus = 'optimal';
    } else if (length >= 40 && length < 50) {
        lengthScore = 8;
        lengthStatus = 'short';
    } else if (length > 60 && length <= 70) {
        lengthScore = 8;
        lengthStatus = 'long';
    } else if (length < 40) {
        lengthScore = 5;
        lengthStatus = 'short';
    } else {
        lengthScore = 4;
        lengthStatus = 'truncated';
    }

    // Clarity score (penalize special char stuffing)
    const specialChars = (title.match(/[^\w\s'-]/g) || []).length;
    const clarityScore = specialChars <= 2 ? 10 : specialChars <= 4 ? 7 : 3;

    // Readability (word length average)
    const words = title.split(/\s+/);
    const avgWordLength = words.reduce((sum, w) => sum + w.length, 0) / words.length;
    const readabilityScore = avgWordLength <= 6 ? 10 : avgWordLength <= 8 ? 8 : 5;

    const overall = (lengthScore * 0.5 + clarityScore * 0.3 + readabilityScore * 0.2);

    return { score: overall, length, lengthScore, lengthStatus };
}

export function calculateCTRBoost(title: string): number {
    const hookType = analyzeTitleHook(title);
    let boost = HOOK_PATTERNS[hookType].ctrBoost;

    // Additional bonuses
    if (HOOK_PATTERNS.year.regex!.test(title)) boost += HOOK_PATTERNS.year.ctrBoost;
    if (HOOK_PATTERNS.curiosity.regex!.test(title)) boost += HOOK_PATTERNS.curiosity.ctrBoost;

    return boost;
}

export function analyzeTitle(title: string): TitleAnalysis {
    if (!title.trim()) {
        return getEmptyAnalysis();
    }

    const hookType = analyzeTitleHook(title);
    const pattern = HOOK_PATTERNS[hookType];
    const thss = calculateTHSS(title);
    const tseResult = calculateTSE(title);
    const ctrBoost = calculateCTRBoost(title);

    // Keyword position analysis
    const words = title.split(/\s+/);
    const firstThreeWords = words.slice(0, 3).join(' ').toLowerCase();
    const keywordPosition: 'front' | 'middle' | 'back' =
        firstThreeWords.length > 15 ? 'front' :
            title.length > 40 ? 'middle' : 'back';
    const keywordPositionScore = keywordPosition === 'front' ? 10 : keywordPosition === 'middle' ? 7 : 4;

    // Check bonuses
    const curiosityBonus = HOOK_PATTERNS.curiosity.regex!.test(title);
    const yearBonus = HOOK_PATTERNS.year.regex!.test(title);

    // Calculate overall score (0-100)
    const overallScore = Math.round(
        (thss * 10) * 0.35 +   // Title hook 35%
        (tseResult.score * 10) * 0.25 + // Structure 25%
        (ctrBoost / 35 * 100) * 0.25 + // CTR potential 25%
        (keywordPositionScore * 10) * 0.15 // Keyword position 15%
    );

    // Generate issues and strengths
    const issues: string[] = [];
    const strengths: string[] = [];

    // Issues
    if (hookType === 'standard') issues.push('Missing hook pattern - consider number or question hook');
    if (tseResult.lengthStatus === 'truncated') issues.push('Title too long - will be cut off on mobile');
    if (tseResult.lengthStatus === 'short') issues.push('Title could be longer for better SEO');
    if (!yearBonus && !curiosityBonus && hookType === 'standard') {
        issues.push('Add year reference (2025) or curiosity elements');
    }

    // Strengths
    if (hookType === 'number') strengths.push('Number hook = 3x better CTR');
    if (hookType === 'question') strengths.push('Question hook creates curiosity');
    if (tseResult.lengthStatus === 'optimal') strengths.push('Perfect title length (50-60 chars)');
    if (curiosityBonus) strengths.push('Curiosity gap increases clicks');
    if (yearBonus) strengths.push('Year reference adds relevance');
    if (ctrBoost >= 35) strengths.push('High CTR potential (+' + ctrBoost + '%)');

    return {
        hookType,
        hookName: pattern.name,
        hookEmoji: pattern.emoji,
        thss,
        tse: tseResult.score,
        ctrBoost,
        lengthScore: tseResult.lengthScore,
        lengthValue: tseResult.length,
        lengthStatus: tseResult.lengthStatus as any,
        keywordPosition,
        keywordPositionScore,
        curiosityBonus,
        yearBonus,
        overallScore,
        issues,
        strengths
    };
}

function getEmptyAnalysis(): TitleAnalysis {
    return {
        hookType: 'standard',
        hookName: 'Standard',
        hookEmoji: '📝',
        thss: 0,
        tse: 0,
        ctrBoost: 0,
        lengthScore: 0,
        lengthValue: 0,
        lengthStatus: 'short',
        keywordPosition: 'back',
        keywordPositionScore: 0,
        curiosityBonus: false,
        yearBonus: false,
        overallScore: 0,
        issues: [],
        strengths: []
    };
}

// Audience size benchmarks for view predictions
export const AUDIENCE_BENCHMARKS = {
    tiny: { base: 200, multiplier: 1.0, label: 'Under 1K subs', range: '100 - 1K' },
    small: { base: 1000, multiplier: 1.2, label: '1K-10K subs', range: '500 - 5K' },
    medium: { base: 5000, multiplier: 1.5, label: '10K-100K subs', range: '2K - 25K' },
    large: { base: 25000, multiplier: 2.0, label: '100K-1M subs', range: '10K - 100K' },
    huge: { base: 100000, multiplier: 2.5, label: 'Over 1M subs', range: '50K - 500K' }
};

export function predictViewRange(
    viralScore: number,
    audienceSize: keyof typeof AUDIENCE_BENCHMARKS,
    ctrBoost: number
): { min: number; max: number; display: string } {
    const benchmark = AUDIENCE_BENCHMARKS[audienceSize] || AUDIENCE_BENCHMARKS.medium;

    const baseViews = benchmark.base * benchmark.multiplier;
    const ctrMultiplier = 1 + (ctrBoost / 100);
    const viralMultiplier = 0.3 + (viralScore / 100) * 1.2;

    const predicted = baseViews * ctrMultiplier * viralMultiplier;

    const min = Math.round(predicted * 0.4);
    const max = Math.round(predicted * 2.0);

    const formatNumber = (n: number) => {
        if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
        if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
        return n.toString();
    };

    return {
        min,
        max,
        display: `${formatNumber(min)} - ${formatNumber(max)}`
    };
}

// Alternative title generators
export interface AlternativeTitle {
    title: string;
    hookType: keyof typeof HOOK_PATTERNS;
    hookName: string;
    emoji: string;
    thss: number;
    ctrBoost: number;
    improvement: string;
}

export function generateAlternativeTitles(originalTitle: string, topic: string): AlternativeTitle[] {
    if (!originalTitle.trim()) return [];

    const alternatives: AlternativeTitle[] = [];
    const originalAnalysis = analyzeTitle(originalTitle);

    // Extract core topic (simplified - could use AI for better extraction)
    const words = originalTitle.toLowerCase()
        .replace(/how to|why|what|when|the|a|an|is|are|was|were|\d+/gi, '')
        .split(/\s+/)
        .filter(w => w.length > 3)
        .slice(0, 4);
    const coreTopic = words.join(' ') || topic || 'this topic';

    // Number hook variant
    if (originalAnalysis.hookType !== 'number') {
        const numberTitle = `7 ${capitalize(coreTopic)} Secrets Nobody Tells You`;
        const analysis = analyzeTitle(numberTitle);
        alternatives.push({
            title: numberTitle,
            hookType: 'number',
            hookName: 'Number Hook',
            emoji: '🔢',
            thss: analysis.thss,
            ctrBoost: analysis.ctrBoost,
            improvement: `+${analysis.ctrBoost - originalAnalysis.ctrBoost}% CTR potential`
        });
    }

    // Question hook variant
    if (originalAnalysis.hookType !== 'question') {
        const questionTitle = `Why Your ${capitalize(coreTopic)} Strategy Isn't Working`;
        const analysis = analyzeTitle(questionTitle);
        alternatives.push({
            title: questionTitle,
            hookType: 'question',
            hookName: 'Question Hook',
            emoji: '❓',
            thss: analysis.thss,
            ctrBoost: analysis.ctrBoost,
            improvement: 'Creates curiosity gap'
        });
    }

    // Authority variant with year
    const authorityTitle = `The Complete ${capitalize(coreTopic)} Guide for 2025`;
    const authAnalysis = analyzeTitle(authorityTitle);
    alternatives.push({
        title: authorityTitle,
        hookType: 'ultimate_guide',
        hookName: 'Authority Guide',
        emoji: '👑',
        thss: authAnalysis.thss,
        ctrBoost: authAnalysis.ctrBoost,
        improvement: 'Authority positioning + year relevance'
    });

    return alternatives.slice(0, 3);
}

function capitalize(str: string): string {
    return str.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}
