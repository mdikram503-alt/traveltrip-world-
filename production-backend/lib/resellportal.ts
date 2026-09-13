import { env } from "./env";
const base = "https://panel.resellportal.com/wp-json/resellportal/v1";
const headers = () => ({"Content-Type":"application/json","X-API-Key":env.resellKey(),"X-API-Secret":env.resellSecret()});
export type EsimPackage = { package_code:string; name?:string; title?:string; price:number|string; location?:string };
export async function getPackage(packageCode:string) {
  const r = await fetch(`${base}/esim-packages`, {headers:headers(), cache:"no-store"});
  if (!r.ok) throw new Error(`ResellPortal catalog failed (${r.status})`);
  const body = await r.json() as {packages?:EsimPackage[]} | EsimPackage[];
  const packages = Array.isArray(body) ? body : body.packages || [];
  const item = packages.find(p=>p.package_code===packageCode);
  if (!item) throw new Error("Package is unavailable");
  return item;
}
export async function listPackages(location?:string) {
  const url = new URL(`${base}/esim-packages`); if(location) url.searchParams.set("location",location);
  const r = await fetch(url,{headers:headers(),cache:"no-store"}); if(!r.ok) throw new Error(`ResellPortal catalog failed (${r.status})`); return r.json();
}
export async function createEsimOrder(input:{email:string; name:string; packageCode:string}) {
  const client = await fetch(`${base}/clients`,{method:"POST",headers:headers(),body:JSON.stringify({name:input.name,email:input.email})});
  if(!client.ok) throw new Error(`ResellPortal client failed (${client.status})`);
  const {client_id} = await client.json();
  const order = await fetch(`${base}/orders`,{method:"POST",headers:headers(),body:JSON.stringify({client_id,product_key:"esim",package_code:input.packageCode,skip_client_email:true})});
  if(!order.ok) throw new Error(`ResellPortal order failed (${order.status})`);
  return order.json();
}
