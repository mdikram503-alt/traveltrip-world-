import { createHmac, randomBytes, timingSafeEqual } from "crypto";
import { NextRequest, NextResponse } from "next/server";

const appUrl = () => process.env.AUTH_APP_URL || "https://traveltrip.world";
const key = () => {
  const value = process.env.GOOGLE_CLIENT_SECRET;
  if (!value) throw new Error("Google sign-in is not configured");
  return value;
};
const sign = (value: string) => createHmac("sha256", key()).update(value).digest("base64url");
const sessionCookie = "traveltrip_session";
const stateCookie = "traveltrip_google_state";

type Session = { email: string; name: string; picture?: string; exp: number };

export const makeState = () => randomBytes(32).toString("base64url");
export const setStateCookie = (response: NextResponse, state: string) => {
  response.cookies.set(stateCookie, state, { httpOnly: true, secure: true, sameSite: "lax", maxAge: 600, path: "/" });
};
export const hasValidState = (request: NextRequest, state: string | null) => {
  const stored = request.cookies.get(stateCookie)?.value;
  if (!state || !stored || state.length !== stored.length) return false;
  return timingSafeEqual(Buffer.from(state), Buffer.from(stored));
};
export const clearStateCookie = (response: NextResponse) => response.cookies.set(stateCookie, "", { httpOnly: true, secure: true, sameSite: "lax", maxAge: 0, path: "/" });
export const callbackUrl = () => `${appUrl()}/api/auth/google/callback`;
export const createSession = (session: Session) => {
  const payload = Buffer.from(JSON.stringify(session)).toString("base64url");
  return `${payload}.${sign(payload)}`;
};
export const readSession = (request: NextRequest): Session | null => {
  const token = request.cookies.get(sessionCookie)?.value;
  if (!token) return null;
  const [payload, signature] = token.split(".");
  if (!payload || !signature || signature.length !== sign(payload).length) return null;
  if (!timingSafeEqual(Buffer.from(signature), Buffer.from(sign(payload)))) return null;
  try {
    const session = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as Session;
    return session.exp > Date.now() ? session : null;
  } catch { return null; }
};
export const setSessionCookie = (response: NextResponse, session: Session) => {
  response.cookies.set(sessionCookie, createSession(session), { httpOnly: true, secure: true, sameSite: "lax", maxAge: 60 * 60 * 24 * 7, path: "/" });
};
