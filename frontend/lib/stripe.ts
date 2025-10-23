import Stripe from "stripe"

const stripeSecretKey = process.env.STRIPE_SECRET_KEY

// Make Stripe optional for Mosaico (we don't need billing for now)
// Stripe features are disabled by default

export const stripe = stripeSecretKey 
  ? new Stripe(stripeSecretKey, {
      apiVersion: "2025-05-28.basil",
      appInfo: {
        name: "Mosaico",
        version: "1.0.0"
      }
    })
  : null
