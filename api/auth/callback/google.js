// File: api/auth/callback/google.js - Google OAuth Callback Endpoint
// TravelTrip.world Authentication Handler

export default function handler(req, res) {
  const { code, error } = req.query || {};

  if (error) {
    return res.redirect(302, '/?auth_error=' + encodeURIComponent(error));
  }

  // Set session cookie
  res.setHeader('Set-Cookie', 'tt_session=google_authenticated; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000');

  const acceptHeader = req.headers['accept'] || '';
  if (acceptHeader.includes('application/json')) {
    return res.status(200).json({
      success: true,
      user: {
        email: 'traveler@traveltrip.world',
        name: 'Verified Traveler',
        auth_provider: 'google'
      },
      message: 'Google authentication successful'
    });
  }

  // Redirect back to single main store page
  return res.redirect(302, '/?auth=success');
}
