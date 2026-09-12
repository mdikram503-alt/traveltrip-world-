// server/templates/email-templates.mjs
// Professional email templates for Traveler eSIM

export const emailTemplates = {
  // ✅ Password Reset Email
  passwordReset: (data) => ({
    subject: 'Reset Your Traveler eSIM Password',
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
          .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: white; padding: 30px; }
          .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
          .footer { color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🔐 Password Reset</h1>
          </div>
          <div class="content">
            <p>Hi ${data.name},</p>
            <p>We received a request to reset your password for your Traveler eSIM account.</p>
            <p><strong>⏰ This link expires in ${data.expiresIn}</strong></p>
            <center>
              <a href="${data.resetLink}" class="button">Reset Password</a>
            </center>
            <p>Or copy this link:</p>
            <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 12px;">
              ${data.resetLink}
            </p>
            <p><strong>Didn't request this?</strong> Your account is secure. Ignore this email if you didn't request a password reset.</p>
            <div class="footer">
              <p>© 2026 Traveler eSIM. All rights reserved.</p>
              <p>Traveler eSIM | Ajman, UAE | support@traveltrip.world</p>
            </div>
          </div>
        </div>
      </body>
      </html>
    `,
  }),

  // ✅ Email Verification
  emailVerification: (data) => ({
    subject: 'Verify Your Traveler eSIM Email Address',
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
          .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: white; padding: 30px; }
          .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
          .code-box { background: #f5f5f5; padding: 15px; text-align: center; font-size: 24px; letter-spacing: 2px; font-weight: bold; border-radius: 5px; margin: 20px 0; font-family: monospace; }
          .footer { color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>✉️ Verify Your Email</h1>
          </div>
          <div class="content">
            <p>Hi ${data.name},</p>
            <p>Welcome to Traveler eSIM! Please verify your email address to complete your account setup.</p>
            <p><strong>⏰ Verification link expires in ${data.expiresIn}</strong></p>
            <center>
              <a href="${data.verificationLink}" class="button">Verify Email Address</a>
            </center>
            <p>Or click this link:</p>
            <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 12px;">
              ${data.verificationLink}
            </p>
            <p>Once verified, you'll be able to purchase eSIM plans and manage your account.</p>
            <div class="footer">
              <p>© 2026 Traveler eSIM. All rights reserved.</p>
              <p>Traveler eSIM | Ajman, UAE | support@traveltrip.world</p>
            </div>
          </div>
        </div>
      </body>
      </html>
    `,
  }),

  // ✅ Order Confirmation with QR Code
  orderConfirmation: (data) => ({
    subject: `Your eSIM Order Confirmed - ${data.orderId}`,
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
          .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: white; padding: 30px; }
          .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745; }
          .order-details { background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }
          .order-details-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
          .qr-section { text-align: center; margin: 30px 0; }
          .qr-section img { max-width: 300px; border: 2px solid #667eea; border-radius: 5px; padding: 10px; }
          .instructions { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2196F3; }
          .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 15px 0; }
          .footer { color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>✅ Order Confirmed!</h1>
          </div>
          <div class="content">
            <p>Hi ${data.customerName},</p>
            
            <div class="success">
              <strong>🎉 Your eSIM is ready!</strong> Your plan is activated and ready to use.
            </div>

            <div class="order-details">
              <div class="order-details-row">
                <span><strong>Order ID:</strong></span>
                <span>${data.orderId}</span>
              </div>
              <div class="order-details-row">
                <span><strong>Destination:</strong></span>
                <span>${data.country}</span>
              </div>
              <div class="order-details-row">
                <span><strong>Plan:</strong></span>
                <span>${data.planName}</span>
              </div>
              <div class="order-details-row">
                <span><strong>Data:</strong></span>
                <span>${data.dataAmount}</span>
              </div>
              <div class="order-details-row">
                <span><strong>Duration:</strong></span>
                <span>${data.duration}</span>
              </div>
              <div class="order-details-row">
                <span><strong>Total Paid:</strong></span>
                <span><strong>$${data.totalAmount}</strong></span>
              </div>
            </div>

            <div class="instructions">
              <h3>📱 How to Install Your eSIM:</h3>
              <ol>
                <li>Open your phone's <strong>Settings</strong> app</li>
                <li>Go to <strong>Mobile/Cellular</strong> settings</li>
                <li>Tap <strong>Add eSIM</strong> or <strong>Mobile Plan</strong></li>
                <li>Choose <strong>Scan QR Code</strong></li>
                <li>Scan the QR code below</li>
                <li>Follow the prompts to complete activation</li>
              </ol>
            </div>

            <div class="qr-section">
              <h3>QR Code for Activation:</h3>
              <img src="${data.qrCodeUrl}" alt="eSIM QR Code">
              <p style="font-size: 12px; color: #666;">Scan this QR code with your phone to install your eSIM</p>
            </div>

            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
              <strong>💡 Tip:</strong> If you're having trouble scanning, you can manually enter your activation code: <code>${data.activationCode}</code>
            </div>

            <center>
              <a href="https://traveltrip.world/pages/account.html" class="button">View Order Details</a>
            </center>

            <p><strong>Need help?</strong> Check our <a href="https://traveltrip.world/pages/help.html">Help Center</a> or contact us at support@traveltrip.world</p>

            <div class="footer">
              <p>© 2026 Traveler eSIM. All rights reserved.</p>
              <p>Traveler eSIM | Ajman, UAE | support@traveltrip.world</p>
            </div>
          </div>
        </div>
      </body>
      </html>
    `,
  }),

  // ✅ Order Status Update
  orderStatusUpdate: (data) => ({
    subject: `eSIM Status Update - ${data.status}`,
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
          .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: white; padding: 30px; }
          .status-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 15px 0; }
          .status-pending { background: #fff3cd; color: #856404; }
          .status-active { background: #d4edda; color: #155724; }
          .status-expired { background: #f8d7da; color: #721c24; }
          .footer { color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>📊 eSIM Status Update</h1>
          </div>
          <div class="content">
            <p>Hi ${data.customerName},</p>
            <p>Your eSIM order #${data.orderId} has been updated:</p>
            <center>
              <div class="status-badge status-${data.status.toLowerCase()}">
                ${data.status}
              </div>
            </center>
            <p>${data.message}</p>
            <center>
              <a href="https://traveltrip.world/pages/account.html" style="display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0;">View Your eSIM</a>
            </center>
            <div class="footer">
              <p>© 2026 Traveler eSIM. All rights reserved.</p>
              <p>Traveler eSIM | Ajman, UAE | support@traveltrip.world</p>
            </div>
          </div>
        </div>
      </body>
      </html>
    `,
  }),
};

export default emailTemplates;
