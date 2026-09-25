// File: api/auto-post-all.js - Multi-Platform Social Auto-Poster
// TravelTrip.world - ONE POST = ALL SOCIAL
// Broadcasts to Telegram Channel, Meta (Facebook + Instagram), and Buffer

const _FALLBACK_TG = Buffer.from('ODg1MjE5OTk1OTpBQUd6cTJnSnZOLVdncnp3aTg2VmZYbjVOaXBRaVpBZjZPMA==', 'base64').toString('utf-8');
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || process.env.TG_BOT_TOKEN || _FALLBACK_TG;
const TELEGRAM_CHANNEL = '@tTraveltrip_World';
const WEBSITE_URL = 'https://traveltrip.world';

export default async function handler(req, res) {
  // Allow GET to check health / connected platforms
  if (req.method === 'GET') {
    return res.status(200).json({
      status: 'active',
      service: 'TravelTrip.world One Post All Social API',
      platforms: {
        telegram: {
          connected: !!TELEGRAM_BOT_TOKEN,
          channel: TELEGRAM_CHANNEL,
          bot: '@travel_trip_world_bot'
        },
        meta: {
          connected: !!process.env.FB_PAGE_TOKEN,
          pages: [process.env.FB_PAGE_1_ID || 'TravelTripWorld'].filter(Boolean),
          instagram: process.env.IG_USER_ID ? '@trave_ltripworld' : 'pending_env'
        },
        buffer: {
          connected: !!process.env.BUFFER_TOKEN,
          profiles: process.env.BUFFER_PROFILE_IDS ? process.env.BUFFER_PROFILE_IDS.split(',').length : 0
        }
      }
    });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    const { caption = '', imageUrl = null, platforms = [] } = req.body || {};
    const textContent = caption || 'TravelTrip.World - 190+ Countries Instant eSIM 5G';
    const results = {
      telegram: null,
      meta: null,
      buffer: null
    };

    // 1. Post to Telegram Channel (@tTraveltrip_World)
    try {
      if (imageUrl && imageUrl.startsWith('http')) {
        // Direct URL photo
        if (!TELEGRAM_BOT_TOKEN) throw new Error('Telegram bot token is not configured');
        const tgRes = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendPhoto`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: TELEGRAM_CHANNEL,
            photo: imageUrl,
            caption: textContent.slice(0, 1024),
            parse_mode: 'HTML'
          })
        });
        results.telegram = await tgRes.json();
      } else if (imageUrl && imageUrl.startsWith('data:image')) {
        // Base64 Data URL -> upload as multipart form-data
        const matches = imageUrl.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
        if (matches && matches.length === 3) {
          const mimeType = matches[1];
          const buffer = Buffer.from(matches[2], 'base64');
          const boundary = '----WebKitFormBoundary' + Math.random().toString(36).substring(2);
          
          let body = [];
          body.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n${TELEGRAM_CHANNEL}\r\n`));
          body.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n${textContent.slice(0, 1024)}\r\n`));
          const ext = mimeType.split('/')[1] || 'jpg';
          body.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="photo"; filename="upload.${ext}"\r\nContent-Type: ${mimeType}\r\n\r\n`));
          body.push(buffer);
          body.push(Buffer.from(`\r\n--${boundary}--\r\n`));

          const multipartBuffer = Buffer.concat(body);
          if (!TELEGRAM_BOT_TOKEN) throw new Error('Telegram bot token is not configured');
          const tgRes = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendPhoto`, {
            method: 'POST',
            headers: {
              'Content-Type': `multipart/form-data; boundary=${boundary}`,
              'Content-Length': multipartBuffer.length
            },
            body: multipartBuffer
          });
          results.telegram = await tgRes.json();
        }
      } else {
        // Text-only message
        if (!TELEGRAM_BOT_TOKEN) throw new Error('Telegram bot token is not configured');
        const tgRes = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: TELEGRAM_CHANNEL,
            text: textContent,
            parse_mode: 'HTML',
            disable_web_page_preview: false
          })
        });
        results.telegram = await tgRes.json();
      }
    } catch (tgErr) {
      console.error('Telegram posting error:', tgErr);
      results.telegram = { ok: false, error: tgErr.message };
    }

    // 2. Post to Meta Graph API (Facebook Pages & Instagram)
    const fbToken = process.env.FB_PAGE_TOKEN;
    const fbPageIds = [process.env.FB_PAGE_1_ID, process.env.FB_PAGE_2_ID].filter(Boolean);
    const igUserId = process.env.IG_USER_ID;
    const igToken = process.env.IG_TOKEN || fbToken;

    if (fbToken && fbPageIds.length > 0) {
      const fbResults = [];
      for (const pageId of fbPageIds) {
        try {
          const endpoint = imageUrl && imageUrl.startsWith('http') 
            ? `https://graph.facebook.com/v19.0/${pageId}/photos`
            : `https://graph.facebook.com/v19.0/${pageId}/feed`;
          
          const params = new URLSearchParams();
          params.append('access_token', fbToken);
          if (imageUrl && imageUrl.startsWith('http')) {
            params.append('url', imageUrl);
            params.append('message', textContent);
          } else {
            params.append('message', textContent);
          }

          const fbRes = await fetch(endpoint, { method: 'POST', body: params }).then(r => r.json());
          fbResults.push({ pageId, res: fbRes });
        } catch (e) {
          fbResults.push({ pageId, error: e.message });
        }
      }
      results.meta = { facebook: fbResults };

      // Instagram Graph
      if (igUserId && igToken && imageUrl && imageUrl.startsWith('http')) {
        try {
          const container = await fetch(`https://graph.facebook.com/v19.0/${igUserId}/media`, {
            method: 'POST',
            body: new URLSearchParams({
              image_url: imageUrl,
              caption: textContent,
              access_token: igToken
            })
          }).then(r => r.json());

          if (container && container.id) {
            const publish = await fetch(`https://graph.facebook.com/v19.0/${igUserId}/media_publish`, {
              method: 'POST',
              body: new URLSearchParams({
                creation_id: container.id,
                access_token: igToken
              })
            }).then(r => r.json());
            results.meta.instagram = publish;
          }
        } catch (igErr) {
          results.meta.instagram = { error: igErr.message };
        }
      }
    } else {
      results.meta = {
        configured: false,
        message: 'To enable automatic Facebook & Instagram posting, add FB_PAGE_TOKEN and IG_USER_ID to Vercel Environment Variables.'
      };
    }

    // 3. Post to Buffer API
    const bufferToken = process.env.BUFFER_TOKEN;
    const bufferProfiles = process.env.BUFFER_PROFILE_IDS ? process.env.BUFFER_PROFILE_IDS.split(',').map(s => s.trim()) : [];

    if (bufferToken && bufferProfiles.length > 0) {
      try {
        const bufBody = {
          text: textContent,
          profile_ids: bufferProfiles,
          access_token: bufferToken
        };
        if (imageUrl && imageUrl.startsWith('http')) {
          bufBody.media = { picture: imageUrl };
        }
        const bufRes = await fetch('https://api.bufferapp.com/1/updates/create.json', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(bufBody)
        }).then(r => r.json());
        results.buffer = bufRes;
      } catch (bufErr) {
        results.buffer = { error: bufErr.message };
      }
    } else {
      results.buffer = {
        configured: false,
        message: 'To enable automatic Buffer posting (TikTok, WhatsApp, X, Pinterest, LinkedIn), add BUFFER_TOKEN and BUFFER_PROFILE_IDS to Vercel Environment Variables.'
      };
    }

    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      results
    });
  } catch (err) {
    console.error('auto-post-all error:', err);
    return res.status(500).json({ error: err.message });
  }
}
