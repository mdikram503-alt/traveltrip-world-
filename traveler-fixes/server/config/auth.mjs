// server/config/auth.mjs
// Fixed Better Auth Configuration

import { betterAuth } from 'better-auth';
import { db } from '../db.mjs';

export const auth = betterAuth({
  database: {
    // Your database connection
    db: db,
    type: 'postgres', // or mysql, sqlite, etc.
  },
  
  // ✅ FIXED: Add all trusted domains
  trustedOrigins: [
    'https://traveltrip.world',
    'https://www.traveltrip.world',
    'https://traveler-esim.vercel.app',
    'https://traveler-esim-*.vercel.app', // All Vercel preview deployments
    'http://localhost:3000', // Local development
    'http://localhost:5173', // Vite dev server
  ],

  // ✅ FIXED: Session configuration
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // Update every 24 hours
    cookieCache: {
      enabled: true,
      maxAge: 5 * 60, // 5 minutes
    },
  },

  // ✅ FIXED: CSRF Protection
  csrf: {
    enabled: true,
    // Trust these origins for CSRF (same as trustedOrigins)
    trustedOrigins: [
      'https://traveltrip.world',
      'https://www.traveltrip.world',
      'https://traveler-esim.vercel.app',
    ],
  },

  // Social providers
  socialProviders: {
    // ✅ FIXED: Google OAuth Configuration
    google: {
      enabled: true,
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      // ✅ IMPORTANT: Ensure these URLs match Google Cloud Console settings
      redirectUrl: 'https://traveltrip.world/api/auth/callback/google',
      scopes: ['openid', 'email', 'profile'],
    },

    // Optional: Add more providers as needed
    // github: {
    //   enabled: true,
    //   clientId: process.env.GITHUB_CLIENT_ID,
    //   clientSecret: process.env.GITHUB_CLIENT_SECRET,
    // },
  },

  // Email configuration (for verification, password reset, etc.)
  email: {
    enabled: true,
    sendVerificationEmail: true,
    sendResetPasswordEmail: true,
    from: 'noreply@traveltrip.world',
  },

  // Account linking
  accountLinking: {
    enabled: true,
    allowMultipleAccountsPerEmail: false,
  },

  // User customization
  user: {
    additionalFields: {
      phone: {
        type: 'string',
        required: false,
      },
      country: {
        type: 'string',
        required: false,
      },
      emailVerified: {
        type: 'boolean',
        required: false,
        defaultValue: false,
      },
    },
  },

  // Hooks for custom logic
  hooks: {
    // After successful authentication
    afterSignUp: async (user) => {
      console.log('User signed up:', user.email);
      // Trigger welcome email, etc.
    },

    // After sign in
    afterSignIn: async (user) => {
      console.log('User signed in:', user.email);
    },

    // Before sign out
    beforeSignOut: async (user) => {
      console.log('User signing out:', user.email);
    },
  },

  // Advanced security options
  advanced: {
    useSecureCookies: true,
    disableCSRFProtection: false,
    cookiePrefix: 'traveler_',
  },
});

export default auth;
