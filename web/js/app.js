async function boot() {
  const q = document.querySelector("#q");
  const grid = document.querySelector("#grid");
  if (!grid) return;
  const res = await fetch("./data/countries.json");
  const countries = (await res.json()).countries;
  const paint = (list) => {
    grid.innerHTML = list.map(c => `
      <a class="card" href="./pages/plans.html?cc=${c.code}">
        <div class="flag">${c.flag}</div>
        <h3>${c.name}</h3>
        <div class="muted">${c.region}${c.fiveG ? " · 5G" : ""}</div>
        <div class="price">from $${c.fromUsd.toFixed(2)}</div>
      </a>`).join("");
  };
  paint(countries);
  q?.addEventListener("input", () => {
    const s = q.value.toLowerCase();
    paint(countries.filter(c => (c.name + c.code + c.region).toLowerCase().includes(s)));
  });
}
boot();
