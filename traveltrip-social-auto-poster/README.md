# TravelTrip Social Auto Poster

One API endpoint posts the same TravelTrip content to configured channels.

## Deploy on Render

Use these settings:

- Build command: `npm install`
- Start command: `npm start`
- Port: `10000`

Required environment variables:

- `ADMIN_KEY`: any strong private password/key
- `BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHANNEL_ID`: `@tTraveltrip_World`
- `WEBSITE_URL`: `https://traveltrip.world`

## Post Content

Send a POST request to `/post`:

```bash
curl -X POST "https://YOUR-RENDER-URL/post" \
  -H "content-type: application/json" \
  -H "x-admin-key: YOUR_ADMIN_KEY" \
  -d '{
    "caption": "TravelTrip World new eSIM offer",
    "imageUrl": "https://example.com/post-image.jpg"
  }'
```

For Telegram, `imageUrl` may be omitted and it will send text only.

## Current Channels

- Telegram: implemented
- Facebook Page: ready after Meta `META_PAGE_ID` and `META_PAGE_ACCESS_TOKEN`
- Instagram: ready after Meta `INSTAGRAM_BUSINESS_ACCOUNT_ID` and `META_PAGE_ACCESS_TOKEN`
- LinkedIn, X, Pinterest: scaffolded and safely skipped until API approval/credentials are added
- Threads, WhatsApp Channel, TikTok, Snapchat: reported as manual/API-limited

## Saved TravelTrip Accounts

- Instagram: `trave_ltripworld`, `trave.ltripworld`
- Threads: `trave_ltripworld`
- Facebook pages: `https://www.facebook.com/share/19NeszaHUy/`, `https://www.facebook.com/share/1EGE852aeb/`
- WhatsApp Channel: `https://whatsapp.com/channel/0029VbDFOpd17EmwZMkdO50l`
- Pinterest: `https://pin.it/A0wZ84guk`
- TikTok: `@traveltrip.world8`
- Snapchat: `Traveltripworld`
- X: `@traveltripakm`
- LinkedIn: `Traveltrip.world`
- Email: `Traveltripworld8@gmail.com`
- WhatsApp Business: `+971524413931`
