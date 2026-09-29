const { botToken, telegramChannelId } = require("../config");

async function postToTelegram({ caption, imageUrl }) {
  if (!botToken) {
    return { platform: "telegram", ok: false, skipped: true, reason: "BOT_TOKEN missing" };
  }

  const endpoint = imageUrl
    ? `https://api.telegram.org/bot${botToken}/sendPhoto`
    : `https://api.telegram.org/bot${botToken}/sendMessage`;

  const body = imageUrl
    ? { chat_id: telegramChannelId, photo: imageUrl, caption }
    : { chat_id: telegramChannelId, text: caption };

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
