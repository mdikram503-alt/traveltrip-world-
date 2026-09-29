const { botToken, telegramChannelId } = require("../config");

async function postToTelegram({ caption, imageUrl, videoUrl }) {
  if (!botToken) {
    return { platform: "telegram", ok: false, skipped: true, reason: "BOT_TOKEN missing" };
  }

  let endpoint = `https://api.telegram.org/bot${botToken}/sendMessage`;
  let body = { chat_id: telegramChannelId, text: caption };

  if (videoUrl) {
    endpoint = `https://api.telegram.org/bot${botToken}/sendVideo`;
    body = { chat_id: telegramChannelId, video: videoUrl, caption };
  } else if (imageUrl) {
    endpoint = `https://api.telegram.org/bot${botToken}/sendPhoto`;
    body = { chat_id: telegramChannelId, photo: imageUrl, caption };
  }

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();
  return {
    platform: "telegram",
    ok: response.ok && data.ok === true,
    status: response.status,
    data,
  };
}

module.exports = { postToTelegram };
