export async function loadCountries() {
  const r = await fetch("./data/countries.json");
  return (await r.json()).countries;
}
export async function loadPlans() {
  const r = await fetch("./data/plans.json");
  return (await r.json()).plans;
}
export function formatMoney(n) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}
