/**
 * TravelTrip World - Global Multi-Language Auto-Detection & Translation Engine
 * Automatically detects the visitor's local language & country, supports RTL (Arabic, Urdu),
 * and provides 1-click manual switching across 12+ world languages.
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

  // 2. Set language and trigger dynamic page translation
  window.setSiteLanguage = function (langCode) {
    if (!SUPPORTED_LANGS[langCode]) langCode = "en";
    localStorage.setItem("tt_lang", langCode);

    // Apply RTL for Arabic & Urdu
    const isRtl = SUPPORTED_LANGS[langCode].rtl;
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = langCode;

    // Update select element if present
    const selector = document.getElementById("tt-lang-select");
    if (selector && selector.value !== langCode) {
      selector.value = langCode;
    }

    // Set cookie for Google Translate
    document.cookie = "googtrans=/en/" + langCode + "; path=/; domain=.traveltrip.world";
    document.cookie = "googtrans=/en/" + langCode + "; path=/";

    // Trigger Google Translate engine
    applyGoogleTranslate(langCode);
  };

  function applyGoogleTranslate(langCode) {
    const teCombo = document.querySelector(".goog-te-combo");
    if (teCombo) {
      teCombo.value = langCode;
      teCombo.dispatchEvent(new Event("change"));
    }
  }

  // 3. Inject Google Translate library silently
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

      // Auto trigger detected language
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

  // 4. Render sleek language selector in navigation bar
  function injectLanguageSelector() {
    const slots = document.querySelectorAll(".lang-slot, #nav-auth-slot, .nav-right, #auth-nav-slot");
    if (!slots.length) return;

    const currentLang = detectVisitorLang();
    const isRtl = SUPPORTED_LANGS[currentLang].rtl;
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = currentLang;

    slots.forEach((slot) => {
      if (slot.querySelector(".tt-lang-picker")) return;

      const wrap = document.createElement("div");
      wrap.className = "tt-lang-picker";
      wrap.style.cssText = "display:inline-flex; align-items:center; margin-right:8px;";

      let optionsHtml = "";
      for (const [code, info] of Object.entries(SUPPORTED_LANGS)) {
        const selected = code === currentLang ? "selected" : "";
        optionsHtml += `<option value="${code}" ${selected}>${info.flag} ${info.name}</option>`;
      }

      wrap.innerHTML = `
        <select id="tt-lang-select" onchange="setSiteLanguage(this.value)" style="background:#1E293B; color:#F8FAFC; border:1px solid #475569; border-radius:8px; padding:6px 10px; font-size:0.85rem; font-weight:600; cursor:pointer; outline:none; transition:all 0.2s;">
          ${optionsHtml}
        </select>
      `;

      slot.insertBefore(wrap, slot.firstChild);
    });
  }

  // Auto initialize on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      injectLanguageSelector();
      loadGoogleTranslate();
    });
  } else {
    injectLanguageSelector();
    loadGoogleTranslate();
  }
})();
