require("dotenv").config();

const express = require("express");
const { Telegraf, Markup } = require("telegraf");

const BOT_TOKEN = process.env.BOT_TOKEN;
const CHANNEL_ID = process.env.CHANNEL_ID || "@tTraveltrip_World";
const PORT = Number(process.env.PORT || 10000);
const WEBSITE_URL = process.env.WEBSITE_URL || "https://traveltrip.world";
const AUTO_POSTER_URL = process.env.AUTO_POSTER_URL || "";
const AUTO_POSTER_ADMIN_KEY = process.env.AUTO_POSTER_ADMIN_KEY || "";

if (!BOT_TOKEN) {
  throw new Error("BOT_TOKEN is required");
}

const bot = new Telegraf(BOT_TOKEN);
const app = express();

const plans = [
  "Bangladesh 1GB - 7 Days",
  "Bangladesh 3GB - 15 Days",
  "Bangladesh 5GB - 30 Days",
  "India 1GB - 7 Days",
  "India 3GB - 15 Days",
  "India 5GB - 30 Days",
  "Malaysia 1GB - 7 Days",
  "Malaysia 3GB - 15 Days",
  "Malaysia 5GB - 30 Days",
  "Thailand 1GB - 7 Days",
  "Thailand 3GB - 15 Days",
  "Thailand 5GB - 30 Days",
  "Singapore 1GB - 7 Days",
  "Singapore 3GB - 15 Days",
  "Singapore 5GB - 30 Days",
  "UAE 1GB - 7 Days",
  "UAE 3GB - 15 Days",
  "UAE 5GB - 30 Days",
  "Saudi Arabia 1GB - 7 Days",
  "Saudi Arabia 3GB - 15 Days",
  "Saudi Arabia 5GB - 30 Days",
  "Turkey 1GB - 7 Days",
  "Turkey 3GB - 15 Days",
  "Turkey 5GB - 30 Days",
  "USA 1GB - 7 Days",
  "USA 3GB - 15 Days",
  "USA 5GB - 30 Days",
  "UK 1GB - 7 Days",
  "UK 3GB - 15 Days",
  "UK 5GB - 30 Days",
  "Europe 3GB - 15 Days",
  "Global 5GB - 30 Days",
];

function mainKeyboard() {
  return Markup.inlineKeyboard([
    [Markup.button.url("Visit Website", WEBSITE_URL)],
    [Markup.button.callback("View Plans", "plans")],
    [Markup.button.callback("Support", "support")],
  ]);
}

function plansText() {
  return [
    "TravelTrip eSIM plans:",
    "",
    ...plans.map((plan, index) => `${index + 1}. ${plan}`),
    "",
    `Buy from: ${WEBSITE_URL}`,
  ].join("\n");
}

async function emergencyFix() {
  await bot.telegram.deleteWebhook({ drop_pending_updates: true });
  console.log("Webhook deleted");

  const me = await bot.telegram.getMe();
  console.log(`Bot verified: @${me.username}`);

  await bot.telegram.deleteMyCommands();
  await bot.telegram.setMyCommands([
    { command: "start", description: "Start TravelTrip bot" },
    { command: "plans", description: "View eSIM packages" },
    { command: "buy", description: "Buy eSIM from website" },
    { command: "website", description: "Open TravelTrip website" },
    { command: "support", description: "Get support" },
  ]);
  console.log("Commands set");
}

async function sendToAutoPoster(payload) {
  if (!AUTO_POSTER_URL || !AUTO_POSTER_ADMIN_KEY) {
    return { ok: false, skipped: true, reason: "AUTO_POSTER_URL or AUTO_POSTER_ADMIN_KEY missing" };
  }

  const response = await fetch(`${AUTO_POSTER_URL.replace(/\/$/, "")}/post`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-admin-key": AUTO_POSTER_ADMIN_KEY,
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return { ok: response.ok && data.ok === true, status: response.status, data };
}

bot.start(async (ctx) => {
  await ctx.reply(
    [
      "Welcome to TravelTrip Alerts.",
      "",
      "Send a photo or video with caption here.",
      "I will publish it through the TravelTrip auto-poster.",
      "",
      "Use /website to open TravelTrip World.",
      "Use /plans to view available eSIM packages.",
    ].join("\n"),
    mainKeyboard()
  );
});

bot.command("website", async (ctx) => {
  await ctx.reply(`TravelTrip World: ${WEBSITE_URL}`, mainKeyboard());
});

bot.command("plans", async (ctx) => {
  await ctx.reply(plansText(), mainKeyboard());
});

bot.command("buy", async (ctx) => {
  await ctx.reply(`Buy your eSIM here: ${WEBSITE_URL}`, mainKeyboard());
});

bot.command("support", async (ctx) => {
  await ctx.reply(
    [
      "TravelTrip support:",
      "",
      "Please message us with your destination, travel date, and eSIM issue.",
      `Website: ${WEBSITE_URL}`,
    ].join("\n")
  );
});

bot.action("plans", async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.reply(plansText(), mainKeyboard());
});

bot.action("support", async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.reply(`Support: ${WEBSITE_URL}`);
});

// Commands must stay above media handlers so command messages are handled first.
bot.on("photo", async (ctx) => {
  const caption = ctx.message.caption || "";
  const photos = ctx.message.photo;
  const largestPhoto = photos[photos.length - 1];
  const imageUrl = await ctx.telegram.getFileLink(largestPhoto.file_id);

  const result = await sendToAutoPoster({ caption, imageUrl: imageUrl.href });
  await ctx.reply(result.ok ? "Posted through TravelTrip auto-poster." : `Auto-poster failed: ${result.reason || result.status || "unknown error"}`);
});

bot.on("video", async (ctx) => {
  const caption = ctx.message.caption || "";
  const videoUrl = await ctx.telegram.getFileLink(ctx.message.video.file_id);

  const result = await sendToAutoPoster({ caption, videoUrl: videoUrl.href });
  await ctx.reply(result.ok ? "Video posted through TravelTrip auto-poster." : `Auto-poster failed: ${result.reason || result.status || "unknown error"}`);
});

bot.catch((err, ctx) => {
  console.error("Bot error", {
    updateType: ctx?.updateType,
    message: err?.message,
    stack: err?.stack,
  });
});

app.get("/", (_req, res) => {
  res.status(200).send("TravelTrip bot is running");
});

app.get("/health", (_req, res) => {
  res.status(200).json({ ok: true, service: "traveltrip-telegram-bot" });
});

async function start() {
  app.listen(PORT, () => {
    console.log(`Health server running on port ${PORT}`);
  });

  await emergencyFix();
  await bot.launch();
  console.log("BOT LAUNCHED - Telegram to auto-poster is ready");
}

start().catch((err) => {
  console.error("Failed to start bot", err);
  process.exit(1);
});

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
