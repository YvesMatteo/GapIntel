/**
 * Input validation schemas using Zod
 * All user inputs should be validated against these schemas
 */
import { z } from 'zod';

// ============================================
// Checkout Endpoint Schemas
// ============================================

export const checkoutInputSchema = z.object({
    channelName: z.string()
        .min(1, 'Channel name is required')
        .max(100, 'Channel name too long')
        .regex(/^@?[\w\-\.]+$/, 'Invalid channel name format'),
    email: z.string()
        .email('Invalid email format')
        .max(254, 'Email too long'),
    tier: z.enum(['basic', 'premium']).optional().default('premium'),
}).strict(); // Reject any unexpected fields

export type CheckoutInput = z.infer<typeof checkoutInputSchema>;

// ============================================
// Report Access Schemas
// ============================================

export const accessKeySchema = z.string()
    .min(10, 'Access key too short')
    .max(50, 'Access key too long')
    .regex(/^GAP-[\w\-]+$/, 'Invalid access key format');

export type AccessKey = z.infer<typeof accessKeySchema>;

// ============================================
// Webhook Schemas (internal use)
// ============================================

export const stripeWebhookSchema = z.object({
    type: z.string(),
    data: z.object({
        object: z.record(z.string(), z.unknown())
    })
});

// ============================================
// Helper Functions
// ============================================

/**
 * Safely parse and validate input
 * Returns { success: true, data } or { success: false, error }
 */
export function validateInput<T>(
    schema: z.ZodSchema<T>,
    input: unknown
): { success: true; data: T } | { success: false; error: string } {
    const result = schema.safeParse(input);

    if (result.success) {
        return { success: true, data: result.data };
    }

    // Format error message
    const errorMessage = result.error.issues
        .map(e => `${e.path.join('.')}: ${e.message}`)
        .join(', ');

    return { success: false, error: errorMessage };
}

/**
 * Sanitize string input (remove potential XSS vectors)
 */
export function sanitizeString(input: string): string {
    return input
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .trim();
}
