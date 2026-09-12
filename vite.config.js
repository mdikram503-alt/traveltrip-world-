import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const webRoot = fileURLToPath(new URL("./web", import.meta.url));
const page = (name) => resolve(webRoot, "pages", name);

export default defineConfig({
  root: "web",
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: resolve(webRoot, "index.html"),
        account: page("account.html"),
        checkout: page("checkout.html"),
        coverage: page("coverage.html"),
        help: page("help.html"),
        plans: page("plans.html"),
        compatible: page("compatible.html"),
        install: page("install.html"),
        contact: page("contact.html"),
        legal: page("legal.html"),
        privacy: page("privacy.html"),
        terms: page("terms.html"),
        refund: page("refund.html"),
        acceptableUse: page("acceptable-use.html"),
        cookies: page("cookies.html"),
        partners: page("partners.html"),
        status: page("status.html"),
        topup: page("topup.html"),
        wallet: page("wallet.html")
      }
    }
  }
});
