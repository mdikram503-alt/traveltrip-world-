// File: api/auth/google.js - Google OAuth Initialization Endpoint
// TravelTrip.world Authentication Handler

export default function handler(req, res) {
  const clientId = process.env.GOOGLE_CLIENT_ID || '1048291823719-sampletraveltripgoogleclientid.apps.googleusercontent.com';
  const redirectUri = 'https://traveltrip.world/api/auth/callback/google';
  const scope = encodeURIComponent('openid email profile');
  const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${scope}&prompt=select_account`;

  const acceptHeader = req.headers['accept'] || '';
  if (acceptHeader.includes('application/json') || req.method === 'POST') {
    return res.status(200).json({
      success: true,
      authUrl: googleAuthUrl,
      provider: 'google'
    });
  }

  // Redirect browser to Google Sign-In
  return res.redirect(302, googleAuthUrl);
}
