// File: api/telegram-bot.js - Production-Ready Vercel Serverless Telegram Bot
// TravelTrip.world Official Telegram Bot (@travel_trip_world_bot)

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || process.env.TG_BOT_TOKEN || '';
const OFFICIAL_CHANNEL = '@tTraveltrip_World';
const WEBSITE_URL = 'https://traveltrip.world';
const WHATSAPP_URL = 'https://wa.me/971524413931?text=Assalamu%20Alaikum,%20ami%20traveltrip.world%20theke%20eSIM%20kitte%20chai';

export default async function handler(req, res) {
  // 1. Health check & status
  if (req.method === 'GET') {
    return res.status(200).json({
      status: 'active',
      bot: '@travel_trip_world_bot',
      name: 'TravelTrip.world Official Bot',
      channel: OFFICIAL_CHANNEL,
      website: WEBSITE_URL,
      time: new Date().toISOString()
    });
  }

  if (req.method !== 'POST') {
    return res.status(200).send('Method Not Allowed');
  }

  if (!BOT_TOKEN) {
    return res.status(503).json({ error: 'Telegram bot token is not configured' });
  }

  try {
    // 2. Parse request body safely (supports Object, String, Buffer, or Stream)
    let update = req.body;
    if (!update && req.readable) {
      const chunks = [];
      for await (const chunk of req) {
        chunks.push(chunk);
      }
      try {
        update = JSON.parse(Buffer.concat(chunks).toString('utf-8'));
      } catch (e) {
        update = null;
      }
    } else if (typeof update === 'string') {
      try {
        update = JSON.parse(update);
      } catch (e) {
        update = null;
      }
    } else if (Buffer.isBuffer(update)) {
      try {
        update = JSON.parse(update.toString('utf-8'));
      } catch (e) {
        update = null;
      }
    }

    if (!update || typeof update !== 'object') {
      return res.status(200).send('OK (Empty or invalid update)');
    }

    // 3. Handle Callback Queries (when users click inline buttons)
    if (update.callback_query) {
      const cb = update.callback_query;
      const cbChatId = cb.message && cb.message.chat ? cb.message.chat.id : cb.from.id;
      const data = cb.data || '';

      await answerCallbackQuery(cb.id);

      if (data === 'action_plans') {
        await sendPlansList(cbChatId);
      } else if (data === 'action_buy') {
        await sendBuyInstructions(cbChatId);
      } else if (data === 'action_support') {
        await sendSupportMessage(cbChatId);
      } else {
        await sendMainMenu(cbChatId, `✈️ You selected: <b>${data}</b>\n\nVisit our store to complete order:`);
      }
      return res.status(200).send('OK');
    }

    // 4. Handle Incoming Messages
    const message = update.message || update.edited_message || update.channel_post;
    if (!message || !message.chat) {
      return res.status(200).send('OK (No message content)');
    }

    const chatId = message.chat.id;
    const text = (message.text || message.caption || '').trim();
    const lower = text.toLowerCase();
    const isPhoto = !!message.photo;

    // A. Photo auto-forwarder to Channel (@tTraveltrip_World)
    if (isPhoto) {
      try {
        const photo = message.photo[message.photo.length - 1].file_id;
        const cap = message.caption 
          ? `${message.caption}\n\n🌍 ${WEBSITE_URL} | 📲 WhatsApp: +971524413931 | ${OFFICIAL_CHANNEL}`
          : `🌍 <b>TravelTrip.World</b> - ONE eSIM. THE WHOLE WORLD.\n\n📲 Website: ${WEBSITE_URL}\n✈️ Channel: ${OFFICIAL_CHANNEL}`;
        
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: OFFICIAL_CHANNEL,
            photo: photo,
            caption: cap,
            parse_mode: 'HTML'
          })
        });
        await sendMessage(chatId, `✅ <b>Photo Auto-Posted to Channel ${OFFICIAL_CHANNEL}!</b>\n\n${message.caption ? '📝 Caption: ' + message.caption : ''}`);
      } catch (err) {
        console.error('Channel post error:', err);
      }
      return res.status(200).send('OK');
    }

    // B. /post or /broadcast command to post text directly to channel
    if (lower.startsWith('/post') || lower.startsWith('/broadcast') || lower.startsWith('post:')) {
      const postText = text.replace(/^\/(post|broadcast)\s*/i, '').replace(/^post:\s*/i, '').trim();
      if (postText) {
        try {
          await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              chat_id: OFFICIAL_CHANNEL,
              text: `${postText}\n\n🌍 <a href="${WEBSITE_URL}">traveltrip.world</a> | 📲 WhatsApp: +971524413931 | ${OFFICIAL_CHANNEL}`,
              parse_mode: 'HTML'
            })
          });
          await sendMessage(chatId, `✅ <b>Text Auto-Posted to Channel ${OFFICIAL_CHANNEL}!</b>\n\n📝 ${postText}`);
        } catch (err) {
          console.error('Channel post error:', err);
          await sendMessage(chatId, `❌ Failed to post to channel: ${err.message}`);
        }
        return res.status(200).send('OK');
      } else {
        await sendMessage(chatId, `✍️ <b>How to post text:</b>\n\nType <code>/post Your Message Here</code> and send, it will automatically publish to <b>${OFFICIAL_CHANNEL}</b>!`);
        return res.status(200).send('OK');
      }
    }

    // C. /start or Hello greetings
    if (lower.startsWith('/start') || lower === 'hi' || lower === 'hello' || lower === 'salam') {
      await sendMainMenu(chatId);
      return res.status(200).send('OK');
    }

    // C. Plans & Pricing
    if (lower.startsWith('/plans') || lower.includes('plan') || lower.includes('price') || lower.includes('দাম') || lower.includes('1')) {
      await sendPlansList(chatId);
      return res.status(200).send('OK');
    }

    // D. Buy / Order / bKash
    if (lower.startsWith('/buy') || lower.includes('buy') || lower.includes('bkash') || lower.includes('nagad') || lower.includes('order') || lower.includes('2')) {
      await sendBuyInstructions(chatId);
      return res.status(200).send('OK');
    }

    // E. 24/7 Human WhatsApp Support
    if (lower.startsWith('/support') || lower.includes('support') || lower.includes('help') || lower.includes('whatsapp') || lower.includes('3')) {
      await sendSupportMessage(chatId);
      return res.status(200).send('OK');
    }

    // F. Website
    if (lower.startsWith('/website') || lower.includes('web') || lower.includes('site') || lower.includes('4')) {
      await sendMessage(chatId, 
        `🌐 <b>TravelTrip.world Official Platform</b>\n\n` +
        `• 190+ Countries Unlimited 5G Data\n` +
        `• Instant 30-Second QR Code Delivery\n` +
        `• No Passport, No ID Card, Gmail Only\n\n` +
        `👉 <a href="${WEBSITE_URL}">Click here to open TravelTrip.world</a>`,
        {
          reply_markup: {
            inline_keyboard: [
              [{ text: '🚀 Open TravelTrip.world', web_app: { url: WEBSITE_URL } }],
              [{ text: '💬 Chat on WhatsApp', url: WHATSAPP_URL }]
            ]
          }
        }
      );
      return res.status(200).send('OK');
    }

    // G. Default Fallback Reply (Never leaves user without response!)
    await sendMessage(chatId,
      `👋 Hello! Welcome to <b>TravelTrip.world Official Bot</b> 🌍\n\n` +
      `We provide instant 5G eSIM for <b>190+ Countries</b> with instant QR delivery in 30 seconds.\n\n` +
      `📌 <b>Quick Options:</b>\n` +
      `• Reply <b>1</b> for eSIM Plans & Prices\n` +
      `• Reply <b>2</b> for bKash / Nagad / Card Payment\n` +
      `• Reply <b>3</b> for 24/7 Human Support\n` +
      `• Reply <b>4</b> to Open Website`,
      getMainKeyboard()
    );

    return res.status(200).send('OK');
  } catch (error) {
    console.error('Bot execution error:', error);
    return res.status(200).send('OK');
  }
}

// ==============================================================================
// HELPER FUNCTIONS & UI TEMPLATES
// ==============================================================================

function getMainKeyboard() {
  return {
    reply_markup: {
      keyboard: [
        [{ text: '🛍️ Browse eSIM Plans' }, { text: '💳 Buy eSIM (bKash/Nagad)' }],
        [{ text: '🌍 190+ Countries' }, { text: '💬 24/7 Human Support' }],
        [{ text: '🚀 Open Website (TravelTrip.world)' }]
      ],
      resize_keyboard: true,
      persistent: true
    }
  };
}

async function sendMainMenu(chatId, prefix = '') {
  const intro = prefix ? `${prefix}\n\n` : '';
  const text = intro +
    `🌍 <b>Welcome to TravelTrip.world Official Bot!</b> ✈️\n\n` +
    `<i>ONE eSIM. THE WHOLE WORLD.</i>\n` +
    `⚡ 190+ Countries Instant 5G Data\n` +
    `⚡ QR Code in 30 Seconds to your Gmail\n` +
    `⚡ No ID Card • No Passport • 100% Safe\n` +
    `💳 Payment: <b>bKash, Nagad, Card & Apple Pay</b>\n\n` +
    `👇 <b>Choose an option below:</b>`;

  const inlineKeyboard = {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🛍️ Browse Plans', callback_data: 'action_plans' },
          { text: '💳 Buy eSIM', callback_data: 'action_buy' }
        ],
        [
          { text: '🚀 Open Store (WebApp)', web_app: { url: WEBSITE_URL } }
        ],
        [
          { text: '💬 WhatsApp (+971524413931)', url: WHATSAPP_URL },
          { text: '📢 Official Channel', url: 'https://t.me/tTraveltrip_World' }
        ]
      ]
    }
  };

  await sendMessage(chatId, text, inlineKeyboard);
}

async function sendPlansList(chatId) {
  const text =
    `🔥 <b>Popular 5G eSIM Plans & Prices:</b>\n\n` +
    `🇦🇪 <b>UAE / Dubai:</b> 5GB $5 | 10GB $8\n` +
    `🇧🇩 <b>Bangladesh:</b> 5GB $6 | 10GB $10\n` +
    `🌏 <b>Asia Bundle (18 Countries):</b> 5GB $13.50 | 10GB $22\n` +
    `🇪🇺 <b>Europe Bundle (33 Countries):</b> 5GB $14 | 10GB $24\n` +
    `🇺🇸 <b>USA:</b> 10GB $12\n` +
    `🇹🇭 <b>Thailand:</b> 50GB $9.90 (Unlimited 5G)\n` +
    `🇸🇦 <b>Saudi Arabia:</b> 5GB $9 | 10GB $16\n` +
    `🇴🇲 <b>Oman / Qatar:</b> 5GB $8 | 10GB $15\n\n` +
    `✨ <i>All plans include 5G speed, Gmail delivery in 30s, and FREE setup guide.</i>`;

  const inlineKeyboard = {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🛒 Select & Buy on Website', web_app: { url: `${WEBSITE_URL}/destinations` } }
        ],
        [
          { text: '💳 Pay via bKash / Nagad', callback_data: 'action_buy' },
          { text: '💬 Order on WhatsApp', url: WHATSAPP_URL }
        ]
      ]
    }
  };

  await sendMessage(chatId, text, inlineKeyboard);
}

async function sendBuyInstructions(chatId) {
  const text =
    `💳 <b>How to Buy eSIM with bKash, Nagad or Card:</b>\n\n` +
    `1️⃣ <b>Direct Online (Fastest):</b>\n` +
    `Open <a href="${WEBSITE_URL}/checkout">TravelTrip Checkout</a>, enter your Gmail & select bKash/Nagad or Card. Instant QR in 30 seconds!\n\n` +
    `2️⃣ <b>Via WhatsApp (Manual Assistance):</b>\n` +
    `Message our 24/7 agent at <b>+971524413931</b>. Send country name + bKash/Nagad payment screenshot. Your eSIM QR will be sent immediately!\n\n` +
    `✅ 100% Money-back Guarantee | 24/7 Human Concierge`;

  const inlineKeyboard = {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🛒 Go to Checkout', url: `${WEBSITE_URL}/checkout` }
        ],
        [
          { text: '💬 Pay via WhatsApp Concierge', url: WHATSAPP_URL }
        ]
      ]
    }
  };

  await sendMessage(chatId, text, inlineKeyboard);
}

async function sendSupportMessage(chatId) {
  const text =
    `💬 <b>TravelTrip 24/7 Human Support:</b>\n\n` +
    `Need help setting up your eSIM or have questions?\n\n` +
    `📱 <b>WhatsApp:</b> +971524413931\n` +
    `📧 <b>Email:</b> Traveltripworld8@gmail.com\n` +
    `🌐 <b>Website:</b> https://traveltrip.world\n` +
    `📢 <b>Telegram Channel:</b> @tTraveltrip_World\n\n` +
    `We reply within 2 minutes!`;

  const inlineKeyboard = {
    reply_markup: {
      inline_keyboard: [
        [{ text: '💬 Chat on WhatsApp Now', url: WHATSAPP_URL }],
        [{ text: '📢 Join Telegram Channel', url: 'https://t.me/tTraveltrip_World' }]
      ]
    }
  };

  await sendMessage(chatId, text, inlineKeyboard);
}

async function sendMessage(chatId, text, extra = {}) {
  const payload = {
    chat_id: chatId,
    text: text,
    parse_mode: 'HTML',
    disable_web_page_preview: false,
    ...extra
  };

  try {
    const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.ok) {
      console.error('Telegram API error:', data);
      // If HTML entity parsing fails, retry with raw plain text
      if (data.description && data.description.includes('parse entities')) {
        delete payload.parse_mode;
        await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }
    }
    return data;
  } catch (err) {
    console.error('Network error in sendMessage:', err);
  }
}

async function answerCallbackQuery(callbackQueryId) {
  try {
    await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/answerCallbackQuery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ callback_query_id: callbackQueryId })
    });
  } catch (e) {}
}
