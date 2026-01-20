import Stripe from 'stripe';

// Lazy initialization to avoid build-time errors
let stripeInstance: Stripe | null = null;

export const getStripe = () => {
    if (!stripeInstance && process.env.STRIPE_SECRET_KEY) {
        stripeInstance = new Stripe(process.env.STRIPE_SECRET_KEY, {
            apiVersion: '2025-12-15.clover',
            typescript: true,
        });
    }
    return stripeInstance;
};

// For backward compatibility
export const stripe = {
    get checkout() { return getStripe()!.checkout; },
    get prices() { return getStripe()!.prices; },
    get webhooks() { return getStripe()!.webhooks; },
};
