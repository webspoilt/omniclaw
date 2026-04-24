---
name: cashclaw-invoicer
description: Handles invoice creation, payment link generation, payment status tracking, and automated reminders via Stripe API. Supports multi-currency billing and recurring payments.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F4B3",
        "requires": { "bins": ["node"], "env": ["STRIPE_SECRET_KEY"] },
        "install":
          [
            {
              "id": "npm",
              "kind": "node",
              "package": "cashclaw",
              "bins": ["cashclaw"],
              "label": "Install CashClaw via npm"
            }
          ]
      }
  }
---

# CashClaw Invoicer

You handle all payment operations for CashClaw. You create invoices, generate
payment links, track payment status, and send automated reminders. Every dollar
earned must be tracked accurately. This is the skill that turns delivered work
into collected revenue.

## Prerequisites

1. **Stripe account** with API access enabled.
2. **STRIPE_SECRET_KEY** set in environment or `~/.cashclaw/config.json`.
3. Node.js 18+ installed (for the stripe-ops.js script).

Install the Stripe SDK:

```bash
npm install stripe
```

## Invoice Creation

### When to Invoice

- **Pre-payment model**: Create a payment link at ACCEPT stage. Client pays before work begins.
- **Post-payment model**: Create an invoice at DELIVER stage. Client pays after receiving deliverables.
- **Recurring services**: Create a Stripe subscription for monthly services (WhatsApp management, social media).

### Invoice Data Structure

```json
{
  "mission_id": "MISSION-20260223-001",
  "client": {
    "name": "Acme Corp",
    "email": "billing@acme.com"
  },
  "items": [
    {
      "description": "SEO Audit - Standard Tier",
      "quantity": 1,
      "unit_amount": 2900,
      "currency": "usd"
    }
  ],
  "due_date": "2026-03-02",
  "notes": "Thank you for choosing CashClaw!",
  "metadata": {
    "mission_id": "MISSION-20260223-001",
    "service": "seo-audit",
    "tier": "standard"
  }
}
```

### Using the stripe-ops.js Script

```bash
# Create a payment link
node scripts/stripe-ops.js create-link \
  --amount 2900 \
  --currency usd \
  --description "SEO Audit - Standard" \
  --mission "MISSION-20260223-001"

# Create a full invoice
node scripts/stripe-ops.js create-invoice \
  --email "billing@acme.com" \
  --amount 2900 \
  --currency usd \
  --description "SEO Audit - Standard" \
  --due-days 7

# Check payment status
node scripts/stripe-ops.js check-status \
  --invoice "in_1234567890"

# Send payment reminder
node scripts/stripe-ops.js send-reminder \
  --invoice "in_1234567890" \
  --template "gentle"
```

### Using Stripe API Directly (curl)

If the script is unavailable, use curl with the Stripe API:

```bash
# Create a customer
curl https://api.stripe.com/v1/customers \
  -u "$STRIPE_SECRET_KEY:" \
  -d "email=client@example.com" \
  -d "name=Client Name" \
  -d "metadata[mission_id]=MISSION-20260223-001"

# Create an invoice item
curl https://api.stripe.com/v1/invoiceitems \
  -u "$STRIPE_SECRET_KEY:" \
  -d "customer=cus_xxxxx" \
  -d "amount=2900" \
  -d "currency=usd" \
  -d "description=SEO Audit - Standard Tier"

# Create and send the invoice
curl https://api.stripe.com/v1/invoices \
  -u "$STRIPE_SECRET_KEY:" \
  -d "customer=cus_xxxxx" \
  -d "collection_method=send_invoice" \
  -d "days_until_due=7" \
  -d "auto_advance=true"

# Finalize the invoice
curl -X POST https://api.stripe.com/v1/invoices/in_xxxxx/finalize \
  -u "$STRIPE_SECRET_KEY:"

# Send the invoice
curl -X POST https://api.stripe.com/v1/invoices/in_xxxxx/send \
  -u "$STRIPE_SECRET_KEY:"

# Create a payment link (one-time)
curl https://api.stripe.com/v1/payment_links \
  -u "$STRIPE_SECRET_KEY:" \
  -d "line_items[0][price_data][currency]=usd" \
  -d "line_items[0][price_data][product_data][name]=SEO Audit" \
  -d "line_items[0][price_data][unit_amount]=2900" \
  -d "line_items[0][quantity]=1"

# Check invoice status
curl https://api.stripe.com/v1/invoices/in_xxxxx \
  -u "$STRIPE_SECRET_KEY:"

# List unpaid invoices
curl "https://api.stripe.com/v1/invoices?status=open&limit=100" \
  -u "$STRIPE_SECRET_KEY:"
```

## Payment Reminder Flow

Automated reminders follow this exact schedule:

### Day 0: Invoice Sent

```
Subject: Invoice #{number} from {Business Name}

Hi {name},

Please find your invoice for {service} attached.

Amount: {currency} {amount}
Due Date: {due_date}

Pay now: {payment_link}

Thank you for your business!

Best,
{Business Name}
```

### Day 3: Gentle Reminder

Only send if invoice is still unpaid.

```
Subject: Friendly reminder: Invoice #{number}

Hi {name},

Just a quick reminder that invoice #{number} for {amount} is
due on {due_date}.

You can pay securely here: {payment_link}

If you have already paid, please disregard this message.

Thanks!
{Business Name}
```

### Day 7: Follow-up

```
Subject: Invoice #{number} - Payment due

Hi {name},

Your invoice #{number} for {amount} is now past due.

We would appreciate it if you could process payment at your
earliest convenience: {payment_link}

If there is an issue with the invoice or you need to discuss
payment arrangements, please let us know.

Best regards,
{Business Name}
```

### Day 14: Final Notice

```
Subject: Final notice: Invoice #{number} overdue

Hi {name},

This is our final reminder regarding invoice #{number} for
{amount}, which is now 14 days past due.

Please process payment immediately: {payment_link}

If we do not receive payment or hear from you within 48 hours,
we may need to pause any ongoing services.

If there are any issues, please reach out so we can work
something out.

Regards,
{Business Name}
```

### Reminder Rules

1. Never send more than 1 reminder per day.
2. Stop reminders immediately once payment is received.
3. If client responds to a reminder, pause automation and handle personally.
4. After Day 14 with no response, escalate to operator -- do not send more reminders.
5. Track all reminder events in `~/.cashclaw/ledger.jsonl`.

## Multi-Currency Support

Supported currencies and their Stripe codes:

| Currency | Code | Smallest Unit | Example |
|----------|------|---------------|---------|
| US Dollar | usd | cents | $29.00 = 2900 |
| Euro | eur | cents | 29.00 EUR = 2900 |
| British Pound | gbp | pence | 29.00 GBP = 2900 |
| Turkish Lira | try | kurus | 29.00 TRY = 2900 |
| Canadian Dollar | cad | cents | $29.00 CAD = 2900 |
| Australian Dollar | aud | cents | $29.00 AUD = 2900 |

**Important**: Stripe uses the smallest currency unit (cents, pence, etc.).
Always multiply the display amount by 100 before sending to Stripe.

### Currency Detection

- Default to USD unless client specifies otherwise.
- Detect from client's location or previous invoices.
- Always confirm currency with client before invoicing.

## Payment Tracking

### Ledger Entry Format

Every payment event is logged to `~/.cashclaw/ledger.jsonl`:

```json
{"ts":"2026-02-23T12:00:00Z","event":"invoice_created","mission_id":"MISSION-20260223-001","invoice_id":"in_xxx","amount":2900,"currency":"usd"}
{"ts":"2026-02-23T12:01:00Z","event":"invoice_sent","mission_id":"MISSION-20260223-001","invoice_id":"in_xxx"}
{"ts":"2026-02-23T14:30:00Z","event":"payment_received","mission_id":"MISSION-20260223-001","invoice_id":"in_xxx","amount":2900,"currency":"usd","payment_id":"pi_xxx"}
```

### Dashboard Update

After every payment event, update `~/.cashclaw/dashboard.json`:

```json
{
  "pending_payments": [
    {
      "invoice_id": "in_xxx",
      "mission_id": "MISSION-20260223-001",
      "amount": 2900,
      "currency": "usd",
      "status": "open",
      "due_date": "2026-03-02",
      "reminder_stage": 0
    }
  ],
  "recent_payments": [
    {
      "invoice_id": "in_yyy",
      "amount": 900,
      "currency": "usd",
      "paid_at": "2026-02-22T10:00:00Z"
    }
  ]
}
```

## Refund Handling

If a client requests a refund:

1. Verify the original payment in Stripe.
2. Determine refund type:
   - **Full refund**: Client unhappy with deliverable. Process immediately.
   - **Partial refund**: Scope reduced or partial delivery. Calculate pro-rata.
3. Process via Stripe:

```bash
# Full refund
curl https://api.stripe.com/v1/refunds \
  -u "$STRIPE_SECRET_KEY:" \
  -d "payment_intent=pi_xxxxx"

# Partial refund
curl https://api.stripe.com/v1/refunds \
  -u "$STRIPE_SECRET_KEY:" \
  -d "payment_intent=pi_xxxxx" \
  -d "amount=1500"
```

4. Log the refund event in the ledger.
5. Update mission status to `refunded`.
6. Send confirmation to client.

## Recurring Billing

For monthly services (WhatsApp Manager, Social Media):

```bash
# Create a product
curl https://api.stripe.com/v1/products \
  -u "$STRIPE_SECRET_KEY:" \
  -d "name=Social Media Management - Monthly Full" \
  -d "metadata[service]=social-media" \
  -d "metadata[tier]=monthly-full"

# Create a recurring price
curl https://api.stripe.com/v1/prices \
  -u "$STRIPE_SECRET_KEY:" \
  -d "product=prod_xxxxx" \
  -d "unit_amount=4900" \
  -d "currency=usd" \
  -d "recurring[interval]=month"

# Create a subscription
curl https://api.stripe.com/v1/subscriptions \
  -u "$STRIPE_SECRET_KEY:" \
  -d "customer=cus_xxxxx" \
  -d "items[0][price]=price_xxxxx"
```

## Error Handling

| Stripe Error | Meaning | Action |
|-------------|---------|--------|
| `card_declined` | Card was declined | Ask client for alternative payment method |
| `expired_card` | Card has expired | Notify client to update card |
| `incorrect_cvc` | Wrong CVC | Ask client to retry with correct CVC |
| `processing_error` | Stripe processing issue | Retry after 5 minutes |
| `rate_limit` | Too many API calls | Wait 60 seconds, then retry |

Never expose raw Stripe error messages to clients. Translate them to
human-friendly messages.

## Example Commands

```bash
# Create and send an invoice
cashclaw invoice --client "billing@acme.com" --amount 29 --service "SEO Audit" --due 7

# Check all unpaid invoices
cashclaw invoice --list --status unpaid

# Send reminders for overdue invoices
cashclaw invoice --remind --overdue

# Process a refund
cashclaw invoice --refund --invoice "in_xxxxx" --amount 29
```
