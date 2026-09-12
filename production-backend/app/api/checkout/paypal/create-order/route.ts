import { NextResponse } from "next/server";
import { z } from "zod";
import { query } from "@/lib/db";
import { createOrder } from "@/lib/paypal";
import { displayUsd, packagePriceInCents } from "@/lib/pricing";
import { getPackage } from "@/lib/resellportal";
const bodySchema=z.object({packageCode:z.string().min(1).max(180),buyerEmail:z.string().email().max(254),buyerName:z.string().trim().min(1).max(120)});
export async function POST(request:Request) { try { const body=bodySchema.parse(await request.json()); const pkg=await getPackage(body.packageCode); const amountCents=packagePriceInCents(pkg); const order=await createOrder(displayUsd(amountCents),crypto.randomUUID()); const paypalOrderId=String(order.id||""); if(!paypalOrderId) throw new Error("PayPal did not return an order ID"); await query("INSERT INTO orders (paypal_order_id, package_code, package_name, amount_cents, buyer_email, buyer_name) VALUES ($1,$2,$3,$4,$5,$6)",[paypalOrderId,body.packageCode,pkg.name||pkg.title||body.packageCode,amountCents,body.buyerEmail.toLowerCase(),body.buyerName]); return NextResponse.json({id:paypalOrderId}); } catch(error) { console.error("PayPal order creation failed",error); return NextResponse.json({error:"Unable to start checkout"},{status:400}); } }
