const express = require("express");
const { adminKey, port, socials } = require("./config");
const { normalizeCaption } = require("./caption");
const { postToTelegram } = require("./connectors/telegram");
const { postToFacebook, postToInstagram } = require("./connectors/meta");
const {
  postToLinkedIn,
  postToPinterest,
  postToX,
  manualPlatforms,
} = require("./connectors/placeholders");

const app = express();
app.use(express.json({ limit: "2mb" }));

function requireAdmin(req, res, next) {
  if (!adminKey) {
    return res.status(500).json({ ok: false, error: "ADMIN_KEY is not configured" });
  }

  if (req.header("x-admin-key") !== adminKey) {
    return res.status(401).json({ ok: false, error: "Invalid admin key" });
  }

  return next();
}

app.get("/", (_req, res) => {
  res.status(200).json({
    ok: true,
    service: "TravelTrip Social Auto Poster",
    usage: "POST /post with x-admin-key",
    socials,
  });
});

app.get("/health", (_req, res) => {
  res.status(200).json({ ok: true });
});

app.post("/post", requireAdmin, async (req, res) => {
  const caption = normalizeCaption(req.body.caption);
  const imageUrl = req.body.imageUrl || "";
  const targets = req.body.targets || [
    "telegram",
    "facebook",
    "instagram",
    "linkedin",
    "x",
    "pinterest",
    "manual",
  ];

  const jobs = [];
  if (targets.includes("telegram")) jobs.push(postToTelegram({ caption, imageUrl }));
  if (targets.includes("facebook")) jobs.push(postToFacebook({ caption, imageUrl }));
  if (targets.includes("instagram")) jobs.push(postToInstagram({ caption, imageUrl }));
  if (targets.includes("linkedin")) jobs.push(postToLinkedIn({ caption, imageUrl }));
  if (targets.includes("x")) jobs.push(postToX({ caption, imageUrl }));
  if (targets.includes("pinterest")) jobs.push(postToPinterest({ caption, imageUrl }));

  const results = await Promise.allSettled(jobs);
  const platformResults = results.map((result) => {
    if (result.status === "fulfilled") return result.value;
    return { ok: false, error: result.reason?.message || String(result.reason) };
  });

  if (targets.includes("manual")) {
    platformResults.push(...manualPlatforms());
  }

  res.status(200).json({
    ok: platformResults.some((result) => result.ok),
    caption,
    imageUrl,
    results: platformResults,
  });
});

app.listen(port, () => {
  console.log(`TravelTrip Social Auto Poster running on port ${port}`);
});
