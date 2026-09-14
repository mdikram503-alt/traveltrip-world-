import { NextRequest, NextResponse } from "next/server";
import { listPackages } from "@/lib/resellportal";
import { displayUsd, packagePriceInCents } from "@/lib/pricing";

export async function GET(req: NextRequest) {
  try {
    const location = req.nextUrl.searchParams.get("location") || undefined;
    const packages = await listPackages(location);
    const publicPackages = packages.map((item) => ({
      packageCode: item.package_code,
      name: item.name || item.title || "Travel eSIM",
      location: item.location || item.country || location || "Global",
      data: String(item.data_amount || item.data || "Data plan"),
      validity: String(item.validity_days || item.validity || "See plan"),
      network: item.network || item.operator || "4G/5G",
      priceUsd: displayUsd(packagePriceInCents(item)),
    }));
    return NextResponse.json({ packages: publicPackages });
  } catch (error) {
    console.error("ResellPortal catalog request failed", error);
    return NextResponse.json({ error: "Supplier catalog unavailable" }, { status: 502 });
  }
}
