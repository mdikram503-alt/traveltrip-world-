import { NextRequest, NextResponse } from "next/server";
import { callbackUrl, clearStateCookie, hasValidState, setSessionCookie } from "../../../../../lib/google-auth";

type GoogleProfile = { email?: string; email_verified?: boolean; name?: string; picture?: string };

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  if (!code || !hasValidState(request, state)) return NextResponse.redirect(new URL("/pages/login.html?error=google_auth", "https://traveltrip.world"));

  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  if (!clientId || !clientSecret) return NextResponse.redirect(new URL("/pages/login.html?error=not_configured", "https://traveltrip.world"));

  const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ code, client_id: clientId, client_secret: clientSecret, redirect_uri: callbackUrl(), grant_type: "authorization_code" }),
    cache: "no-store"
  });
  if (!tokenResponse.ok) return NextResponse.redirect(new URL("/pages/login.html?error=token_exchange", "https://traveltrip.world"));

  const tokens = await tokenResponse.json() as { access_token?: string };
  const profileResponse = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", { headers: { Authorization: `Bearer ${tokens.access_token || ""}` }, cache: "no-store" });
  const profile = await profileResponse.json() as GoogleProfile;
  if (!profileResponse.ok || !profile.email || !profile.email_verified) return NextResponse.redirect(new URL("/pages/login.html?error=profile", "https://traveltrip.world"));

  const response = NextResponse.redirect(new URL("/?login=success", "https://traveltrip.world"));
  clearStateCookie(response);
  setSessionCookie(response, { email: profile.email, name: profile.name || profile.email.split("@")[0], picture: profile.picture, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 });
  return response;
}
