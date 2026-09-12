// server/routes/paypal.mjs
// Complete PayPal integration for eSIM store

import { Router } from 'express';
import fetch from 'node-fetch';

const router = Router();

const PAYPAL_API_BASE = process.env.PAYPAL_MODE === 'live' 
  ? 'https://api.paypal.com'
  : 'https://api.sandbox.paypal.com';

const PAYPAL_CLIENT_ID = process.env.PAYPAL_CLIENT_ID;
const PAYPAL_CLIENT_SECRET = process.env.PAYPAL_CLIENT_SECRET;

// ✅ Get PayPal Access Token
async function getPayPalToken() {
  try {
    const auth = Buffer.from(`${PAYPAL_CLIENT_ID}:${PAYPAL_CLIENT_SECRET}`).toString('base64');
    
    const response = await fetch(`${PAYPAL_API_BASE}/v1/oauth2/token`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'grant_type=client_credentials',
    });

    const data = await response.json();
    
    if (!data.access_token) {
      throw new Error('Failed to get PayPal token');
    }

    return data.access_token;
  } catch (error) {
    console.error('PayPal token error:', error);
    throw error;
  }
}

// ✅ Create PayPal Order
router.post('/paypal/create-order', async (req, res) => {
  try {
    const { items, customerId, email } = req.body;

    if (!items || !items.length) {
      return res.status(400).json({ error: 'Items required' });
    }

    // Calculate total
    const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2);

    const token = await getPayPalToken();

    const orderData = {
      intent: 'CAPTURE',
      purchase_units: [
        {
          amount: {
            currency_code: 'USD',
            value: total,
            breakdown: {
              item_total: {
                currency_code: 'USD',
                value: total,
              },
            },
          },
          items: items.map(item => ({
            name: item.name,
            quantity: item.quantity.toString(),
            unit_amount: {
              currency_code: 'USD',
              value: item.price.toString(),
            },
            sku: item.sku,
            description: item.description,
          })),
          shipping: {
            name: {
              full_name: 'Digital Delivery',
            },
            address: {
              address_line_1: 'Digital Product',
              admin_area_2: 'Online',
              postal_code: '00000',
              country_code: 'US',
            },
          },
        },
      ],
      payer: {
        email_address: email,
      },
      application_context: {
        brand_name: 'Traveler eSIM',
        return_url: 'https://traveltrip.world/pages/checkout.html?status=success',
        cancel_url: 'https://traveltrip.world/pages/checkout.html?status=cancel',
        user_action: 'PAY_NOW',
        landing_page: 'BILLING',
      },
    };

    const response = await fetch(`${PAYPAL_API_BASE}/v2/checkout/orders`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(orderData),
    });

    const order = await response.json();

    if (!order.id) {
      throw new Error('Failed to create PayPal order');
    }

    // Save order to database
    const dbResult = await db.query(
      `INSERT INTO orders 
       (order_id, customer_id, email, status, payment_method, total_amount, items) 
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [order.id, customerId, email, 'PENDING', 'paypal', total, JSON.stringify(items)]
    );

    res.json({
      id: order.id,
      status: order.status,
      links: order.links,
    });
  } catch (error) {
    console.error('Create PayPal order error:', error);
    res.status(500).json({ error: 'Failed to create order' });
  }
});

// ✅ Capture PayPal Order
router.post('/paypal/capture-order', async (req, res) => {
  try {
    const { orderId } = req.body;

    if (!orderId) {
      return res.status(400).json({ error: 'Order ID required' });
    }

    const token = await getPayPalToken();

    const response = await fetch(`${PAYPAL_API_BASE}/v2/checkout/orders/${orderId}/capture`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const capturedOrder = await response.json();

    if (capturedOrder.status !== 'COMPLETED') {
      throw new Error(`Order capture failed: ${capturedOrder.status}`);
    }

    // Update order status in database
    await db.query(
      'UPDATE orders SET status = ?, payment_status = ? WHERE order_id = ?',
      ['PAID', 'CAPTURED', orderId]
    );

    // Trigger eSIM provisioning
    const order = await db.query('SELECT * FROM orders WHERE order_id = ?', [orderId]);
    if (order.length) {
      await provisionESIM(order[0]);
    }

    res.json({
      id: capturedOrder.id,
      status: capturedOrder.status,
      message: 'Order captured successfully. eSIM provisioning started.',
    });
  } catch (error) {
    console.error('Capture PayPal order error:', error);
    res.status(500).json({ error: 'Failed to capture order' });
  }
});

// ✅ PayPal Webhook Handler
router.post('/webhook/paypal', async (req, res) => {
  try {
    const { event_type, resource } = req.body;

    console.log('PayPal webhook received:', event_type);

    switch (event_type) {
      case 'CHECKOUT.ORDER.COMPLETED':
        // Order approved but not yet captured
        await db.query(
          'UPDATE orders SET status = ? WHERE order_id = ?',
          ['APPROVED', resource.id]
        );
        break;

      case 'CHECKOUT.ORDER.APPROVED':
        // Order approved
        break;

      case 'PAYMENT.CAPTURE.COMPLETED':
        // Payment captured successfully
        await db.query(
          'UPDATE orders SET status = ?, payment_status = ? WHERE order_id = ?',
          ['PAID', 'CAPTURED', resource.id]
        );

        // Trigger eSIM provisioning
        const order = await db.query('SELECT * FROM orders WHERE order_id = ?', [resource.id]);
        if (order.length) {
          await provisionESIM(order[0]);
        }
        break;

      case 'PAYMENT.CAPTURE.DENIED':
        // Payment failed
        await db.query(
          'UPDATE orders SET status = ?, payment_status = ? WHERE order_id = ?',
          ['FAILED', 'DENIED', resource.id]
        );
        break;

      case 'PAYMENT.CAPTURE.REFUNDED':
        // Refund issued
        await db.query(
          'UPDATE orders SET status = ?, payment_status = ? WHERE order_id = ?',
          ['REFUNDED', 'REFUNDED', resource.id]
        );
        break;
    }

    res.json({ received: true });
  } catch (error) {
    console.error('PayPal webhook error:', error);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
});

// ✅ Provision eSIM via ResellPortal
async function provisionESIM(order) {
  try {
    const items = JSON.parse(order.items);
    
    for (const item of items) {
      // Call ResellPortal API to provision eSIM
      const response = await fetch('https://panel.resellportal.com/wp-json/resellportal/v1/orders', {
        method: 'POST',
        headers: {
          'X-API-Key': process.env.RESELLPORTAL_API_KEY,
          'X-API-Secret': process.env.RESELLPORTAL_API_SECRET,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: item.sku,
          package: item.package,
          client_email: order.email,
          skip_client_email: false, // Send QR to customer
        }),
      });

      if (!response.ok) {
        throw new Error(`ResellPortal API error: ${response.status}`);
      }

      const data = await response.json();

      // Save eSIM details
      await db.query(
        `INSERT INTO esims 
         (order_id, email, country, package, status, qr_code, activation_code)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [order.order_id, order.email, item.country, item.package, 'PROVISIONED', 
         data.qr_code, data.activation_code]
      );
    }

    // Mark order as completed
    await db.query(
      'UPDATE orders SET status = ? WHERE order_id = ?',
      ['DELIVERED', order.order_id]
    );

    console.log(`eSIM provisioned for order ${order.order_id}`);
  } catch (error) {
    console.error('eSIM provisioning error:', error);
    
    // Mark as review required
    await db.query(
      'UPDATE orders SET status = ? WHERE order_id = ?',
      ['REVIEW_REQUIRED', order.order_id]
    );
  }
}

export default router;
