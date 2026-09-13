import { NextRequest, NextResponse } from "next/server";
import { readSession } from "../../../../lib/google-auth";

export async function GET(request: NextRequest) {
  const session = readSession(request);
  return NextResponse.json({ authenticated: Boolean(session), user: session ? { email: session.email, name: session.name, picture: session.picture } : null });
}
