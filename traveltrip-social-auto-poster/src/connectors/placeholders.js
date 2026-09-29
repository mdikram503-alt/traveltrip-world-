const { linkedinAccessToken, linkedinAuthorUrn, xBearerToken, pinterestAccessToken, pinterestBoardId } = require("../config");

async function postToLinkedIn() {
  if (!linkedinAccessToken || !linkedinAuthorUrn) {
    return { platform: "linkedin", ok: false, skipped: true, reason: "LinkedIn API credentials missing" };
  }

  return { platform: "linkedin", ok: false, skipped: true, reason: "Connector scaffold ready; enable after LinkedIn app approval" };
}

async function postToX() {
  if (!xBearerToken) {
    return { platform: "x", ok: false, skipped: true, reason: "X API credentials missing" };
  }

  return { platform: "x", ok: false, skipped: true, reason: "Connector scaffold ready; X write API access required" };
}

async function postToPinterest() {
  if (!pinterestAccessToken || !pinterestBoardId) {
    return { platform: "pinterest", ok: false, skipped: true, reason: "Pinterest API credentials missing" };
  }

  return { platform: "pinterest", ok: false, skipped: true, reason: "Connector scaffold ready; enable after Pinterest app approval" };
}

function manualPlatforms() {
  return [
    { platform: "threads", ok: false, manual: true, reason: "Threads posting requires Meta setup and account mapping" },
    { platform: "whatsapp-channel", ok: false, manual: true, reason: "WhatsApp Channels do not expose simple public posting API" },
    { platform: "tiktok", ok: false, manual: true, reason: "TikTok posting needs developer approval" },
    { platform: "snapchat", ok: false, manual: true, reason: "Snapchat posting needs Snap developer setup" },
  ];
}

module.exports = { postToLinkedIn, postToX, postToPinterest, manualPlatforms };
