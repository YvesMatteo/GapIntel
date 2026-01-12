/**
 * Rate Limiter utility for Next.js API routes
 * Implements IP-based rate limiting with configurable limits
 */

interface RateLimitEntry {
    count: number;
    resetTime: number;
}

// In-memory store (suitable for serverless with short TTL)
const rateLimitStore = new Map<string, RateLimitEntry>();

// Cleanup old entries periodically
const CLEANUP_INTERVAL = 60 * 1000; // 1 minute
let lastCleanup = Date.now();

function cleanup() {
    const now = Date.now();
    if (now - lastCleanup < CLEANUP_INTERVAL) return;

    lastCleanup = now;
    for (const [key, entry] of rateLimitStore.entries()) {
        if (now > entry.resetTime) {
            rateLimitStore.delete(key);
        }
    }
}

export interface RateLimitConfig {
    maxRequests: number;      // Max requests per window
    windowMs: number;         // Time window in milliseconds
    keyPrefix?: string;       // Optional prefix for the key
}

export interface RateLimitResult {
    success: boolean;
    remaining: number;
    resetTime: number;
}

/**
 * Check if a request should be rate limited
 * @param identifier - Unique identifier (usually IP or user ID)
 * @param config - Rate limit configuration
 * @returns RateLimitResult
 */
export function checkRateLimit(
    identifier: string,
    config: RateLimitConfig = { maxRequests: 10, windowMs: 60000 }
): RateLimitResult {
    cleanup();

    const { maxRequests, windowMs, keyPrefix = '' } = config;
    const key = `${keyPrefix}:${identifier}`;
    const now = Date.now();

    const entry = rateLimitStore.get(key);

    // No existing entry or expired - create new
    if (!entry || now > entry.resetTime) {
        rateLimitStore.set(key, {
            count: 1,
            resetTime: now + windowMs
        });
        return {
            success: true,
            remaining: maxRequests - 1,
            resetTime: now + windowMs
        };
    }

    // Increment count
    entry.count++;

    // Check if over limit
    if (entry.count > maxRequests) {
        return {
            success: false,
            remaining: 0,
            resetTime: entry.resetTime
        };
    }

    return {
        success: true,
        remaining: maxRequests - entry.count,
        resetTime: entry.resetTime
    };
}

/**
 * Get client IP from request headers
 * Works with Vercel, Cloudflare, and standard setups
 */
export function getClientIP(request: Request): string {
    // Vercel
    const forwardedFor = request.headers.get('x-forwarded-for');
    if (forwardedFor) {
        return forwardedFor.split(',')[0].trim();
    }

    // Cloudflare
    const cfConnectingIP = request.headers.get('cf-connecting-ip');
    if (cfConnectingIP) {
        return cfConnectingIP;
    }

    // Real IP header
    const realIP = request.headers.get('x-real-ip');
    if (realIP) {
        return realIP;
    }

    return 'unknown';
}
