// File: api/telegram-bot.js - Vercel Serverless Function
// Just copy-paste this file, no extra setup needed!

export default async function handler(req, res) {
  const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
  const CHANNEL = '@tTraveltrip_World';
  
  if (!BOT_TOKEN) {
    return res.status(200).send('Add TELEGRAM_BOT_TOKEN in Vercel Env');
  }

  // GET request - to check bot is live
  if (req.method === 'GET') {
    return res.status(200).send('Traveltrip.world Bot is LIVE! 🌍 Bot: @Traveltrip_world8');
  }

  // POST request - from Telegram
  if (req.method === 'POST') {
    try {
      const update = req.body;
      const message = update.message || update.edited_message;
      if (!message) return res.status(200).send('OK');

      const chatId = message.chat.id;
      const text = message.text || message.caption || '';
      const isPhoto = !!message.photo;

      // 1. /start command - Instant Reply
      if (text.startsWith('/start')) {
        await sendMessage(BOT_TOKEN, chatId, 
          `🌍 Welcome to Traveltrip.world! ✈️\n\n` +
          `Best eSIM for 190+ Countries\n` +
          `Instant Activation | Cheapest Data\n\n` +
          `🛒 Website: https://traveltrip.world\n` +
          `💬 WhatsApp: +971524413931\n` +
          `📧 Email: Traveltripworld8@gmail.com\n` +
          `📢 Channel: https://t.me/tTraveltrip_World\n\n` +
          `Send me a photo + caption and I will auto-post to Channel!`
        );
        return res.status(200).send('OK');
      }

      // 2. If user sends photo + caption -> Auto-post to Channel
      if (isPhoto && (message.caption && message.caption.length > 3)) {
        const caption = message.caption;
        const photo = message.photo[message.photo.length - 1].file_id;

        // Forward to Channel @tTraveltrip_World
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: CHANNEL,
            photo: photo,
            caption: caption + '\n\n🌍 https://traveltrip.world | 📲 +971524413931 | @trave_ltripworld'
          })
        });

        await sendMessage(BOT_TOKEN, chatId, `✅ Posted to Channel ${CHANNEL}!\n\n📝 ${caption}\n\n🎉 Success!`);
        return res.status(200).send('OK');
      }

      // 3. If only text (not /start) -> Auto Reply
      if (text && !text.startsWith('/')) {
        let reply = '';
        const lower = text.toLowerCase();
        if (lower.includes('price') || lower.includes('1')) {
          reply = `💰 eSIM Price:\n🇦🇪 Dubai 5GB $5 | 10GB $8\n🇺🇸 USA 10GB $12\n🇪🇺 Europe 10GB $10\n\nBuy: https://traveltrip.world`;
        } else if (lower.includes('hi') || lower.includes('hello') || lower.includes('salam')) {
          reply = `Hello! 🌍 Welcome to Traveltrip.world!\n\nReply:\n1️⃣ Price\n2️⃣ How it works\n\nWebsite: https://traveltrip.world`;
        } else {
          reply = `Thanks! 🌍 Your message: "${text}"\n\nFor price reply 1\nWebsite: https://traveltrip.world\nWhatsApp: +971524413931`;
        }
        await sendMessage(BOT_TOKEN, chatId, reply);
        return res.status(200).send('OK');
      }

      return res.status(200).send('OK');
    } catch (e) {
      console.error(e);
      return res.status(200).send('OK');
    }
  }

  return res.status(200).send('OK');
}

async function sendMessage(token, chatId, text) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text: text })
  });
}
