/**
 * TravelTrip World - Global Multi-Language & Multi-Currency Engine
 * Features:
 * - Auto-detects visitor language & country
 * - 12+ world languages with RTL support for Arabic & Urdu
 * - Dynamic Currency Switcher (USD, AED, SAR, EUR, GBP, BDT)
 * - Real-time price conversion on cards & checkout routing
 */

(function () {
  const SUPPORTED_LANGS = {
    en: { name: "English", flag: "🇺🇸", rtl: false },
    ar: { name: "العربية", flag: "🇦🇪", rtl: true },
    bn: { name: "বাংলা", flag: "🇧🇩", rtl: false },
    hi: { name: "हिन्दी", flag: "🇮🇳", rtl: false },
    ur: { name: "اردو", flag: "🇵🇰", rtl: true },
    fr: { name: "Français", flag: "🇫🇷", rtl: false },
    es: { name: "Español", flag: "🇪🇸", rtl: false },
    de: { name: "Deutsch", flag: "🇩🇪", rtl: false },
    ja: { name: "日本語", flag: "🇯🇵", rtl: false },
    tr: { name: "Türkçe", flag: "🇹🇷", rtl: false },
    ru: { name: "Русский", flag: "🇷🇺", rtl: false },
    zh: { name: "中文", flag: "🇨🇳", rtl: false }
  };

  const CURRENCIES = {
    USD: { code: "USD", symbol: "$", rate: 1.0, flag: "🇺🇸" },
    AED: { code: "AED", symbol: "د.إ ", rate: 3.6725, flag: "🇦🇪" },
    SAR: { code: "SAR", symbol: "﷼ ", rate: 3.75, flag: "🇸🇦" },
    EUR: { code: "EUR", symbol: "€", rate: 0.925, flag: "🇪🇺" },
    GBP: { code: "GBP", symbol: "£", rate: 0.79, flag: "🇬🇧" },
    BDT: { code: "BDT", symbol: "৳", rate: 121.5, flag: "🇧🇩" }
  };

  // 1. Detect visitor's language preference
  function detectVisitorLang() {
    const saved = localStorage.getItem("tt_lang");
    if (saved && SUPPORTED_LANGS[saved]) return saved;

    const navLangs = navigator.languages || [navigator.language || "en"];
    for (const l of navLangs) {
      const code = l.toLowerCase().split("-")[0];
      if (SUPPORTED_LANGS[code]) return code;
    }
    return "en";
  }

  // 2. Detect visitor's currency preference
  function detectVisitorCurrency() {
    const saved = localStorage.getItem("tt_currency");
    if (saved && CURRENCIES[saved]) return saved;

    const lang = detectVisitorLang();
    if (lang === "ar") return "AED";
    if (lang === "bn") return "BDT";
    return "USD";
  }

  // 3. Set language and trigger translation
  window.setSiteLanguage = function (langCode) {
    if (!SUPPORTED_LANGS[langCode]) langCode = "en";
    localStorage.setItem("tt_lang", langCode);

    const isRtl = SUPPORTED_LANGS[langCode].rtl;
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = langCode;

    const selector = document.getElementById("tt-lang-select");
    if (selector && selector.value !== langCode) {
      selector.value = langCode;
    }

    document.cookie = "googtrans=/en/" + langCode + "; path=/; domain=.traveltrip.world";
    document.cookie = "googtrans=/en/" + langCode + "; path=/";

    applyGoogleTranslate(langCode);
  };

  function applyGoogleTranslate(langCode) {
    const teCombo = document.querySelector(".goog-te-combo");
    if (teCombo) {
      teCombo.value = langCode;
      teCombo.dispatchEvent(new Event("change"));
    }
  }

  // 4. Set site currency & convert live prices
  window.setSiteCurrency = function (currCode) {
    if (!CURRENCIES[currCode]) currCode = "USD";
    localStorage.setItem("tt_currency", currCode);

    const curr = CURRENCIES[currCode];
    const selector = document.getElementById("tt-curr-select");
    if (selector && selector.value !== currCode) {
      selector.value = currCode;
    }

    // Convert all pricing boxes
    const usdPrices = {
      "global-7d-unlimited": { perDay: 1.67, total: 11.69, days: 7 },
      "global-3d-3gb": { perDay: 1.40, total: 4.20, days: 3 },
      "global-15d-10gb": { perDay: 1.13, total: 16.95, days: 15 },
      "global-30d-unlimited": { perDay: 1.23, total: 36.99, days: 30 }
    };

    // Update plan buttons and checkout URLs
    document.querySelectorAll("a[href*='checkout.html']").forEach(a => {
      const url = new URL(a.href, window.location.origin);
      url.searchParams.set("currency", currCode);
      a.href = url.pathname + url.search;
    });

    // Update destination cards prices
    document.querySelectorAll(".maya-dest-price").forEach(el => {
      const txt = el.innerText;
      const match = txt.match(/([0-9]+\.[0-9]+)/);
      if (match) {
        if (!el.getAttribute("data-usd")) {
          el.setAttribute("data-usd", match[1]);
        }
        const usdVal = parseFloat(el.getAttribute("data-usd"));
        const convVal = (usdVal * curr.rate).toFixed(2);
        el.innerHTML = `${curr.code} ${convVal} <span>/day</span>`;
      }
    });

    // Update plan card pricing
    document.querySelectorAll(".maya-plan-card").forEach(card => {
      const btn = card.querySelector(".maya-plan-btn");
      if (btn) {
        const url = new URL(btn.href, window.location.origin);
        const pkg = url.searchParams.get("package");
        if (pkg && usdPrices[pkg]) {
          const pInfo = usdPrices[pkg];
          const convDay = (pInfo.perDay * curr.rate).toFixed(2);
          const convTotal = (pInfo.total * curr.rate).toFixed(2);

          const perDayEl = card.querySelector(".maya-price-per-day .amount");
          if (perDayEl) perDayEl.innerText = `${curr.code} ${convDay}`;

          const totalEl = card.querySelector(".maya-price-total");
          if (totalEl) totalEl.innerText = `*${pInfo.days}-day cycle · ${curr.code} ${convTotal} total`;
        }
      }
    });
  };

  // 5. Inject Google Translate library silently
  function loadGoogleTranslate() {
    if (document.getElementById("google-translate-script")) return;

    window.googleTranslateElementInit = function () {
      new window.google.translate.TranslateElement(
        {
          pageLanguage: "en",
          includedLanguages: "en,ar,bn,hi,ur,fr,es,de,ja,tr,ru,zh,ms,id,vi,th,ko,it,pt",
          autoDisplay: false
        },
        "google_translate_element"
      );

      const userLang = detectVisitorLang();
      if (userLang !== "en") {
        setTimeout(() => {
          applyGoogleTranslate(userLang);
        }, 350);
      }
    };

    const gtDiv = document.createElement("div");
    gtDiv.id = "google_translate_element";
    gtDiv.style.display = "none";
    document.body.appendChild(gtDiv);

    const s = document.createElement("script");
    s.id = "google-translate-script";
    s.src = "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    s.async = true;
    document.head.appendChild(s);
  }

  // 6. Render sleek language & currency selectors in navigation bar
  function injectSelectors() {
    const slots = document.querySelectorAll("#i18n-language-selector, .maya-nav-actions, .lang-slot");
    if (!slots.length) return;

    const currentLang = detectVisitorLang();
    const currentCurr = detectVisitorCurrency();
    const isRtl = SUPPORTED_LANGS[currentLang].rtl;
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = currentLang;

    // Use dedicated slot or first navigation action
    const targetSlot = document.getElementById("i18n-language-selector") || slots[0];
    if (targetSlot.querySelector(".tt-controls-wrap")) return;

    const wrap = document.createElement("div");
    wrap.className = "tt-controls-wrap";
    wrap.style.cssText = "display:inline-flex; align-items:center; gap:6px;";

    let langOptions = "";
    for (const [code, info] of Object.entries(SUPPORTED_LANGS)) {
      const selected = code === currentLang ? "selected" : "";
      langOptions += `<option value="${code}" ${selected}>${info.flag} ${info.name}</option>`;
    }

    let currOptions = "";
    for (const [code, info] of Object.entries(CURRENCIES)) {
      const selected = code === currentCurr ? "selected" : "";
      currOptions += `<option value="${code}" ${selected}>${info.flag} ${info.code}</option>`;
    }

    wrap.innerHTML = `
      <select id="tt-curr-select" onchange="setSiteCurrency(this.value)" style="background:#F1F5F9; color:#0E131F; border:1px solid #CBD5E1; border-radius:8px; padding:6px 10px; font-size:12.5px; font-weight:700; cursor:pointer; outline:none; font-family:inherit;">
        ${currOptions}
      </select>
      <select id="tt-lang-select" onchange="setSiteLanguage(this.value)" style="background:#F1F5F9; color:#0E131F; border:1px solid #CBD5E1; border-radius:8px; padding:6px 10px; font-size:12.5px; font-weight:700; cursor:pointer; outline:none; font-family:inherit;">
        ${langOptions}
      </select>
    `;

    targetSlot.appendChild(wrap);

    // Apply currency immediately
    setTimeout(() => {
      window.setSiteCurrency(currentCurr);
    }, 100);
  }

  // Initialize
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      injectSelectors();
      loadGoogleTranslate();
    });
  } else {
    injectSelectors();
    loadGoogleTranslate();
  }
})();
