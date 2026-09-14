import { NextRequest, NextResponse } from "next/server";
import { listPackages } from "@/lib/resellportal";

export async function GET(req: NextRequest) {
  try {
    const location = req.nextUrl.searchParams.get("location") || undefined;
    return NextResponse.json(await listPackages(location));
  } catch (error) {
    console.error("ResellPortal catalog request failed", error);
    return NextResponse.json({ error: "Supplier catalog unavailable" }, { status: 502 });
  }
}
