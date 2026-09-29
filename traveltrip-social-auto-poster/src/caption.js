const { websiteUrl, socials } = require("./config");

function normalizeCaption(input) {
  const caption = String(input || "").trim();
  const footer = [
    "",
    `Book eSIM: ${websiteUrl}`,
    `WhatsApp: ${socials.whatsappBusiness}`,
    "#TravelTripWorld #eSIM #TravelSmart",
  ].join("\n");

  if (!caption) {
    return `Travel smart with TravelTrip World.${footer}`;
  }

  if (caption.includes(websiteUrl)) {
    return caption;
  }

  return `${caption}${footer}`;
}

module.exports = { normalizeCaption };
