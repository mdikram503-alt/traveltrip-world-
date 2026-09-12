import { env } from "./env";
import type { EsimPackage } from "./resellportal";
export function packagePriceInCents(item: EsimPackage) { const wholesale=Number(item.price); if(!Number.isFinite(wholesale)||wholesale<=0) throw new Error("Supplier returned an invalid package price"); return Math.ceil((Math.round(wholesale*100)*(10000+env.sellingMarginBps()))/10000); }
export const displayUsd = (cents:number) => (cents/100).toFixed(2);
