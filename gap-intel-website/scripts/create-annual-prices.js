#!/usr/bin/env node
/**
 * Create annual Stripe prices for all subscription tiers
 * Run with: node scripts/create-annual-prices.js
 */

const Stripe = require('stripe');

// Load env
require('dotenv').config({ path: '.env.local' });

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

// Monthly prices (in dollars)
const MONTHLY_PRICES = {
    starter: 29,
    pro: 59,
    enterprise: 129
};

// Annual is 20% discount = 10 months for price of 12
const ANNUAL_DISCOUNT = 0.8; // 20% off

async function createAnnualPrices() {
    console.log('Creating annual Stripe prices...\n');

    // Get existing products
    const products = await stripe.products.list({ active: true, limit: 10 });

    const productMap = {};
    for (const product of products.data) {
        const name = product.name.toLowerCase();
        if (name.includes('starter')) productMap['starter'] = product.id;
        if (name.includes('pro') && !name.includes('enterprise')) productMap['pro'] = product.id;
        if (name.includes('enterprise')) productMap['enterprise'] = product.id;
    }

    console.log('Found products:', productMap);

    const results = {};

    for (const [tier, monthlyPrice] of Object.entries(MONTHLY_PRICES)) {
        const productId = productMap[tier];

        if (!productId) {
            console.log(`⚠️  No product found for ${tier}, skipping...`);
            continue;
        }

        // Calculate annual price (monthly * 12 * 0.8 for 20% off)
        const annualPrice = Math.round(monthlyPrice * 12 * ANNUAL_DISCOUNT);

        console.log(`Creating ${tier} annual: $${monthlyPrice}/mo → $${annualPrice}/year (20% off)`);

        const price = await stripe.prices.create({
            product: productId,
            unit_amount: annualPrice * 100, // cents
            currency: 'usd',
            recurring: {
                interval: 'year',
            },
            nickname: `${tier.charAt(0).toUpperCase() + tier.slice(1)} Annual`,
        });

        results[tier] = price.id;
        console.log(`✅ Created: ${price.id}\n`);
    }

    console.log('\n\n=== Add to .env.local ===');
    console.log(`STRIPE_PRICE_STARTER_ANNUAL=${results.starter || 'MISSING'}`);
    console.log(`STRIPE_PRICE_PRO_ANNUAL=${results.pro || 'MISSING'}`);
    console.log(`STRIPE_PRICE_ENTERPRISE_ANNUAL=${results.enterprise || 'MISSING'}`);
}

createAnnualPrices().catch(console.error);
