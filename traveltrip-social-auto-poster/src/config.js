require("dotenv").config();

const socials = {
  instagram: ["trave_ltripworld", "trave.ltripworld"],
  threads: "trave_ltripworld",
  facebookPages: [
    "https://www.facebook.com/share/19NeszaHUy/",
    "https://www.facebook.com/share/1EGE852aeb/",
  ],
  whatsappChannel: "https://whatsapp.com/channel/0029VbDFOpd17EmwZMkdO50l",
  pinterest: "https://pin.it/A0wZ84guk",
  tiktok: "@traveltrip.world8",
  snapchat: "Traveltripworld",
  x: "@traveltripakm",
  linkedin: "Traveltrip.world",
  email: "Traveltripworld8@gmail.com",
  whatsappBusiness: "+971524413931",
};

module.exports = {
  port: Number(process.env.PORT || 10000),
  adminKey: process.env.ADMIN_KEY || "",
  websiteUrl: process.env.WEBSITE_URL || "https://traveltrip.world",
  botToken: process.env.BOT_TOKEN || "",
  telegramChannelId: process.env.TELEGRAM_CHANNEL_ID || "@tTraveltrip_World",
  metaPageAccessToken: process.env.META_PAGE_ACCESS_TOKEN || "",
  metaPageId: process.env.META_PAGE_ID || "",
  instagramBusinessAccountId: process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || "",
  linkedinAccessToken: process.env.LINKEDIN_ACCESS_TOKEN || "",
  linkedinAuthorUrn: process.env.LINKEDIN_AUTHOR_URN || "",
  xBearerToken: process.env.X_BEARER_TOKEN || "",
  pinterestAccessToken: process.env.PINTEREST_ACCESS_TOKEN || "",
  pinterestBoardId: process.env.PINTEREST_BOARD_ID || "",
  socials,
};
