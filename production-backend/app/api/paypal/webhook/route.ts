import { NextResponse } from "next/server";
import { db, query } from "@/lib/db";
import { sendEsimEmail } from "@/lib/email";
import { verifyWebhook } from "@/lib/paypal";
import { createEsimOrder } from "@/lib/resellportal";

type OrderRow = { paypal_order_id:string; package_code:string; package_name:string; amount_cents:number; buyer_email:string; buyer_name:string; status:string };
const cents = (value:unknown) => Math.round(Number(value) * 100);

export async function POST(request:Request) {
  let event: any;
  try { event = await request.json(); } catch { return NextResponse.json({error:"Invalid JSON"},{status:400}); }
  try {
    if (!(await verifyWebhook(request.headers,event))) return NextResponse.json({error:"Invalid PayPal signature"},{status:400});
    const eventId=String(event.id||"");
    if (!eventId) return NextResponse.json({error:"Missing event ID"},{status:400});
    const inserted=await query("INSERT INTO webhook_events (event_id,event_type) VALUES ($1,$2) ON CONFLICT DO NOTHING RETURNING event_id",[eventId,String(event.event_type||"")]);
    if (inserted.rowCount === 0) return NextResponse.json({ok:true, duplicate:true});
    if (event.event_type !== "PAYMENT.CAPTURE.COMPLETED") return NextResponse.json({ok:true, ignored:true});

    const resource=event.resource || {};
    const paypalOrderId=String(resource?.supplementary_data?.related_ids?.order_id || resource?.invoice_id || "");
    const amount=resource.amount || {};
    if (!paypalOrderId || amount.currency_code !== "USD") throw new Error("Payment event does not identify a USD order");

    const client=await db().connect();
    let order:OrderRow | undefined;
    try {
      await client.query("BEGIN");
      const result=await client.query<OrderRow>("SELECT paypal_order_id,package_code,package_name,amount_cents,buyer_email,buyer_name,status FROM orders WHERE paypal_order_id=$1 FOR UPDATE",[paypalOrderId]);
      order=result.rows[0];
      if (!order) throw new Error("No local order matches this PayPal payment");
      if (order.status !== "PENDING_PAYMENT") { await client.query("COMMIT"); return NextResponse.json({ok:true, duplicate:true}); }
      if (cents(amount.value) !== order.amount_cents) throw new Error("Captured amount does not match the server-side order");
      await client.query("UPDATE orders SET status='FULFILLING', paid_at=now() WHERE paypal_order_id=$1",[paypalOrderId]);
      await client.query("COMMIT");
    } catch(error) { await client.query("ROLLBACK"); throw error; } finally { client.release(); }
    if (!order) throw new Error("Order missing");
    try {
      const supplierOrder=await createEsimOrder({email:order.buyer_email,name:order.buyer_name,packageCode:order.package_code});
      await query("UPDATE orders SET status='FULFILLED_EMAIL_PENDING', supplier_response=$2, fulfilled_at=now() WHERE paypal_order_id=$1",[paypalOrderId,supplierOrder]);
      try { await sendEsimEmail({to:order.buyer_email,customerName:order.buyer_name,packageName:order.package_name,supplierOrder}); await query("UPDATE orders SET status='FULFILLED' WHERE paypal_order_id=$1",[paypalOrderId]); } catch(emailError) { console.error("eSIM supplied but email failed",emailError); }
    } catch(supplierError) { await query("UPDATE orders SET status='FULFILLMENT_FAILED' WHERE paypal_order_id=$1",[paypalOrderId]); throw supplierError; }
    return NextResponse.json({ok:true});
  } catch(error) { console.error("PayPal webhook processing failed",error); return NextResponse.json({error:"Webhook processing failed"},{status:500}); }
}
