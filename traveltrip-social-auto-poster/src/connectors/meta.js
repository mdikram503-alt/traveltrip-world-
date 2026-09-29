const {
  metaPageAccessToken,
  metaPageId,
  instagramBusinessAccountId,
} = require("../config");

async function postToFacebook({ caption, imageUrl }) {
  if (!metaPageAccessToken || !metaPageId) {
    return {
      platform: "facebook",
      ok: false,
      skipped: true,
      reason: "META_PAGE_ACCESS_TOKEN or META_PAGE_ID missing",
    };
  }

  const path = imageUrl ? "photos" : "feed";
  const body = imageUrl
    ? { url: imageUrl, caption, access_token: metaPageAccessToken }
    : { message: caption, access_token: metaPageAccessToken };

  const response = await fetch(`https://graph.facebook.com/v20.0/${metaPageId}/${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();
  return { platform: "facebook", ok: response.ok, status: response.status, data };
}

async function postToInstagram({ caption, imageUrl }) {
  if (!metaPageAccessToken || !instagramBusinessAccountId) {
    return {
      platform: "instagram",
      ok: false,
      skipped: true,
      reason: "META_PAGE_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID missing",
    };
  }

  if (!imageUrl) {
    return {
      platform: "instagram",
      ok: false,
      skipped: true,
      reason: "Instagram API requires a public imageUrl",
    };
  }

  const createResponse = await fetch(
    `https://graph.facebook.com/v20.0/${instagramBusinessAccountId}/media`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        image_url: imageUrl,
        caption,
        access_token: metaPageAccessToken,
      }),
    }
  );
  const createData = await createResponse.json();

  if (!createResponse.ok || !createData.id) {
    return {
      platform: "instagram",
      ok: false,
      status: createResponse.status,
      data: createData,
    };
  }

  const publishResponse = await fetch(
    `https://graph.facebook.com/v20.0/${instagramBusinessAccountId}/media_publish`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        creation_id: createData.id,
        access_token: metaPageAccessToken,
      }),
    }
  );
  const publishData = await publishResponse.json();
  return {
    platform: "instagram",
    ok: publishResponse.ok,
    status: publishResponse.status,
    data: publishData,
  };
}

module.exports = { postToFacebook, postToInstagram };
