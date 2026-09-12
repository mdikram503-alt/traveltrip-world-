// server/routes/auth-enhanced.mjs
// Enhanced authentication with Password Reset & Email Verification

import { Router } from 'express';
import { sendEmail } from '../integrations/email.mjs';
import { generateToken, verifyToken } from '../utils/tokens.mjs';
import { hashPassword, verifyPassword } from '../utils/crypto.mjs';

const router = Router();

// ✅ Password Reset Request
router.post('/auth/forgot-password', async (req, res) => {
  try {
    const { email } = req.body;
    
    if (!email) {
      return res.status(400).json({ error: 'Email required' });
    }

    // Find user by email
    const user = await db.query(
      'SELECT id, email, name FROM users WHERE email = ?',
      [email]
    );

    if (!user.length) {
      // Security: don't reveal if email exists
      return res.status(200).json({ 
        message: 'If email exists, reset link will be sent' 
      });
    }

    // Generate reset token (valid for 1 hour)
    const resetToken = generateToken(user[0].id, '1h');
    
    // Save reset token to database
    await db.query(
      'UPDATE users SET reset_token = ?, reset_token_expires = DATE_ADD(NOW(), INTERVAL 1 HOUR) WHERE id = ?',
      [resetToken, user[0].id]
    );

    // Send reset email
    const resetLink = `https://traveltrip.world/pages/reset-password.html?token=${resetToken}`;
    
    await sendEmail({
      to: email,
      subject: 'Reset Your Traveler eSIM Password',
      template: 'password-reset',
      data: {
        name: user[0].name,
        resetLink,
        expiresIn: '1 hour'
      }
    });

    res.json({ message: 'Password reset email sent' });
  } catch (error) {
    console.error('Forgot password error:', error);
    res.status(500).json({ error: 'Failed to process reset request' });
  }
});

// ✅ Password Reset Confirmation
router.post('/auth/reset-password', async (req, res) => {
  try {
    const { token, newPassword } = req.body;

    if (!token || !newPassword) {
      return res.status(400).json({ error: 'Token and password required' });
    }

    // Verify token and get user
    const decoded = verifyToken(token);
    if (!decoded) {
      return res.status(400).json({ error: 'Invalid or expired token' });
    }

    const user = await db.query(
      'SELECT id FROM users WHERE id = ? AND reset_token = ? AND reset_token_expires > NOW()',
      [decoded.userId, token]
    );

    if (!user.length) {
      return res.status(400).json({ error: 'Invalid or expired token' });
    }

    // Hash new password and update
    const hashedPassword = await hashPassword(newPassword);
    
    await db.query(
      'UPDATE users SET password = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?',
      [hashedPassword, user[0].id]
    );

    res.json({ message: 'Password reset successfully' });
  } catch (error) {
    console.error('Reset password error:', error);
    res.status(500).json({ error: 'Failed to reset password' });
  }
});

// ✅ Email Verification Request (on signup)
router.post('/auth/send-verification', async (req, res) => {
  try {
    const { email, userId } = req.body;

    if (!email || !userId) {
      return res.status(400).json({ error: 'Email and user ID required' });
    }

    // Generate verification token (valid for 24 hours)
    const verificationToken = generateToken(userId, '24h');

    // Save verification token
    await db.query(
      'UPDATE users SET verification_token = ?, email_verified = 0 WHERE id = ?',
      [verificationToken, userId]
    );

    // Send verification email
    const verificationLink = `https://traveltrip.world/pages/verify-email.html?token=${verificationToken}`;
    const user = await db.query('SELECT name FROM users WHERE id = ?', [userId]);

    await sendEmail({
      to: email,
      subject: 'Verify Your Traveler eSIM Account',
      template: 'email-verification',
      data: {
        name: user[0].name,
        verificationLink,
        expiresIn: '24 hours'
      }
    });

    res.json({ message: 'Verification email sent' });
  } catch (error) {
    console.error('Send verification error:', error);
    res.status(500).json({ error: 'Failed to send verification email' });
  }
});

// ✅ Email Verification Confirmation
router.post('/auth/verify-email', async (req, res) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(400).json({ error: 'Token required' });
    }

    // Verify token
    const decoded = verifyToken(token);
    if (!decoded) {
      return res.status(400).json({ error: 'Invalid or expired token' });
    }

    // Check if token matches
    const user = await db.query(
      'SELECT id FROM users WHERE id = ? AND verification_token = ?',
      [decoded.userId, token]
    );

    if (!user.length) {
      return res.status(400).json({ error: 'Invalid or expired token' });
    }

    // Mark email as verified
    await db.query(
      'UPDATE users SET email_verified = 1, verification_token = NULL WHERE id = ?',
      [user[0].id]
    );

    res.json({ message: 'Email verified successfully' });
  } catch (error) {
    console.error('Verify email error:', error);
    res.status(500).json({ error: 'Failed to verify email' });
  }
});

// ✅ Resend Verification Email
router.post('/auth/resend-verification', async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email required' });
    }

    const user = await db.query(
      'SELECT id, name FROM users WHERE email = ?',
      [email]
    );

    if (!user.length) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Generate new verification token
    const verificationToken = generateToken(user[0].id, '24h');
    
    await db.query(
      'UPDATE users SET verification_token = ? WHERE id = ?',
      [verificationToken, user[0].id]
    );

    // Send email
    const verificationLink = `https://traveltrip.world/pages/verify-email.html?token=${verificationToken}`;

    await sendEmail({
      to: email,
      subject: 'Verify Your Traveler eSIM Account',
      template: 'email-verification',
      data: {
        name: user[0].name,
        verificationLink,
        expiresIn: '24 hours'
      }
    });

    res.json({ message: 'Verification email resent' });
  } catch (error) {
    console.error('Resend verification error:', error);
    res.status(500).json({ error: 'Failed to resend verification email' });
  }
});

export default router;
