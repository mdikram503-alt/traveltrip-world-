import { NextRequest, NextResponse } from "next/server"; import { listPackages } from "@/lib/resellportal";
export async function GET(req:NextRequest){try{return NextResponse.json(await listPackages(req.nextUrl.searchParams.get("location")||undefined));}catch{return NextResponse.json({error:"Supplier catalog unavailable"},{status:502});}}
