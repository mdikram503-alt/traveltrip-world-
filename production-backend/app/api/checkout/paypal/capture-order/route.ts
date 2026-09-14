import { NextResponse } from "next/server";
import { z } from "zod";
import { captureOrder } from "@/lib/paypal";

const bodySchema = z.object({ orderId: z.string().min(8).max(80) });

export async function POST(request: Request) {
  try {
    const { orderId } = bodySchema.parse(await request.json());
    const result = await captureOrder(orderId);
    return NextResponse.json({ id: result.id, status: result.status });
  } catch (error) {
    console.error("PayPal capture failed", error);
    return NextResponse.json({ error: "Unable to capture payment" }, { status: 400 });
  }
}
