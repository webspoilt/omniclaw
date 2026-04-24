#!/usr/bin/env node

/**
 * CashClaw Invoicer - Stripe Operations Script
 *
 * Usage:
 *   node stripe-ops.js <command> [options]
 *
 * Commands:
 *   create-link     Create a Stripe payment link
 *   create-invoice  Create and send a Stripe invoice
 *   check-status    Check payment status of an invoice
 *   send-reminder   Send a payment reminder
 *   list-unpaid     List all unpaid invoices
 *   refund          Process a refund
 *
 * Requires: STRIPE_SECRET_KEY environment variable or ~/.cashclaw/config.json
 */

const { argv, exit, env } = require("process");
const { readFileSync, writeFileSync, existsSync, appendFileSync } = require("fs");
const { join } = require("path");
const { homedir } = require("os");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

function getStripeKey() {
  // 1. Environment variable
  if (env.STRIPE_SECRET_KEY) return env.STRIPE_SECRET_KEY;

  // 2. Config file
  const configPath = join(homedir(), ".cashclaw", "config.json");
  if (existsSync(configPath)) {
    try {
      const config = JSON.parse(readFileSync(configPath, "utf-8"));
      if (config.stripe_secret_key) return config.stripe_secret_key;
    } catch {
      // ignore parse errors
    }
  }

  console.error("Error: STRIPE_SECRET_KEY not found.");
  console.error("Set it via environment variable or in ~/.cashclaw/config.json");
  exit(1);
}

function getStripe() {
  try {
    const Stripe = require("stripe");
    return new Stripe(getStripeKey(), { apiVersion: "2024-12-18.acacia" });
  } catch (err) {
    if (err.code === "MODULE_NOT_FOUND") {
      console.error('Error: stripe package not installed. Run: npm install stripe');
      exit(1);
    }
    throw err;
  }
}

// ---------------------------------------------------------------------------
// Ledger logging
// ---------------------------------------------------------------------------

function logEvent(event) {
  const ledgerPath = join(homedir(), ".cashclaw", "ledger.jsonl");
  const entry = { ts: new Date().toISOString(), ...event };
  try {
    appendFileSync(ledgerPath, JSON.stringify(entry) + "\n", "utf-8");
  } catch {
    // If directory doesn't exist, skip logging
    console.log(`  [log] ${JSON.stringify(entry)}`);
  }
}

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

function parseArgs() {
  const args = { command: argv[2] };
  for (let i = 3; i < argv.length; i++) {
    const key = argv[i].replace(/^--/, "").replace(/-/g, "_");
    const val = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
    args[key] = val;
  }
  return args;
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

async function createPaymentLink(stripe, args) {
  const amount = parseInt(args.amount, 10);
  const currency = args.currency || "usd";
  const description = args.description || "CashClaw Service";
  const missionId = args.mission || "unknown";

  if (!amount || isNaN(amount)) {
    console.error("Error: --amount required (in smallest currency unit, e.g., 2900 for $29)");
    exit(1);
  }

  console.log(`\n  Creating payment link...`);
  console.log(`  Amount: ${(amount / 100).toFixed(2)} ${currency.toUpperCase()}`);
  console.log(`  Description: ${description}\n`);

  const link = await stripe.paymentLinks.create({
    line_items: [
      {
        price_data: {
          currency,
          product_data: {
            name: description,
            metadata: { mission_id: missionId },
          },
          unit_amount: amount,
        },
        quantity: 1,
      },
    ],
    metadata: { mission_id: missionId },
  });

  logEvent({
    event: "payment_link_created",
    mission_id: missionId,
    link_id: link.id,
    url: link.url,
    amount,
    currency,
  });

  console.log(`  Payment link created!`);
  console.log(`  URL: ${link.url}`);
  console.log(`  Link ID: ${link.id}\n`);

  return link;
}

async function createInvoice(stripe, args) {
  const email = args.email;
  const amount = parseInt(args.amount, 10);
  const currency = args.currency || "usd";
  const description = args.description || "CashClaw Service";
  const dueDays = parseInt(args.due_days || "7", 10);
  const missionId = args.mission || "unknown";

  if (!email) {
    console.error("Error: --email required");
    exit(1);
  }
  if (!amount || isNaN(amount)) {
    console.error("Error: --amount required (in smallest currency unit)");
    exit(1);
  }

  console.log(`\n  Creating invoice...`);
  console.log(`  Client: ${email}`);
  console.log(`  Amount: ${(amount / 100).toFixed(2)} ${currency.toUpperCase()}`);
  console.log(`  Due: ${dueDays} days\n`);

  // Find or create customer
  const customers = await stripe.customers.list({ email, limit: 1 });
  let customer;
  if (customers.data.length > 0) {
    customer = customers.data[0];
    console.log(`  Found existing customer: ${customer.id}`);
  } else {
    customer = await stripe.customers.create({
      email,
      metadata: { source: "cashclaw" },
    });
    console.log(`  Created new customer: ${customer.id}`);
  }

  // Create invoice item
  await stripe.invoiceItems.create({
    customer: customer.id,
    amount,
    currency,
    description,
  });

  // Create invoice
  const invoice = await stripe.invoices.create({
    customer: customer.id,
    collection_method: "send_invoice",
    days_until_due: dueDays,
    auto_advance: true,
    metadata: { mission_id: missionId },
  });

  // Finalize
  const finalized = await stripe.invoices.finalizeInvoice(invoice.id);

  // Send
  await stripe.invoices.sendInvoice(finalized.id);

  logEvent({
    event: "invoice_created",
    mission_id: missionId,
    invoice_id: finalized.id,
    amount,
    currency,
    customer_id: customer.id,
  });

  logEvent({
    event: "invoice_sent",
    mission_id: missionId,
    invoice_id: finalized.id,
  });

  console.log(`  Invoice created and sent!`);
  console.log(`  Invoice ID: ${finalized.id}`);
  console.log(`  Invoice Number: ${finalized.number}`);
  console.log(`  Hosted URL: ${finalized.hosted_invoice_url}`);
  console.log(`  PDF: ${finalized.invoice_pdf}\n`);

  return finalized;
}

async function checkPaymentStatus(stripe, args) {
  const invoiceId = args.invoice;
  if (!invoiceId) {
    console.error("Error: --invoice required (e.g., in_1234567890)");
    exit(1);
  }

  console.log(`\n  Checking status for: ${invoiceId}\n`);

  const invoice = await stripe.invoices.retrieve(invoiceId);

  const status = {
    id: invoice.id,
    number: invoice.number,
    status: invoice.status,
    amount_due: invoice.amount_due,
    amount_paid: invoice.amount_paid,
    amount_remaining: invoice.amount_remaining,
    currency: invoice.currency,
    due_date: invoice.due_date
      ? new Date(invoice.due_date * 1000).toISOString()
      : null,
    created: new Date(invoice.created * 1000).toISOString(),
    paid: invoice.paid,
    hosted_url: invoice.hosted_invoice_url,
    customer_email: invoice.customer_email,
  };

  console.log(`  Status: ${status.status}`);
  console.log(`  Paid: ${status.paid}`);
  console.log(
    `  Amount Due: ${(status.amount_due / 100).toFixed(2)} ${status.currency.toUpperCase()}`
  );
  console.log(
    `  Amount Paid: ${(status.amount_paid / 100).toFixed(2)} ${status.currency.toUpperCase()}`
  );
  console.log(
    `  Amount Remaining: ${(status.amount_remaining / 100).toFixed(2)} ${status.currency.toUpperCase()}`
  );
  if (status.due_date) console.log(`  Due Date: ${status.due_date}`);
  console.log(`  Customer: ${status.customer_email}`);
  console.log();

  return status;
}

async function sendReminder(stripe, args) {
  const invoiceId = args.invoice;
  const template = args.template || "gentle";

  if (!invoiceId) {
    console.error("Error: --invoice required");
    exit(1);
  }

  console.log(`\n  Sending ${template} reminder for: ${invoiceId}\n`);

  const invoice = await stripe.invoices.retrieve(invoiceId);

  if (invoice.paid) {
    console.log("  Invoice is already paid. No reminder needed.\n");
    return;
  }

  // Stripe does not have a native "send reminder" endpoint, so we re-send the invoice
  try {
    await stripe.invoices.sendInvoice(invoiceId);
    console.log("  Reminder sent successfully (invoice re-sent).\n");
  } catch (err) {
    // If invoice cannot be re-sent (already sent recently), log it
    console.log(`  Could not re-send invoice: ${err.message}`);
    console.log("  Consider sending a manual reminder email.\n");
  }

  logEvent({
    event: "reminder_sent",
    invoice_id: invoiceId,
    template,
    amount: invoice.amount_due,
    currency: invoice.currency,
  });
}

async function listUnpaid(stripe) {
  console.log(`\n  Listing unpaid invoices...\n`);

  const invoices = await stripe.invoices.list({
    status: "open",
    limit: 100,
  });

  if (invoices.data.length === 0) {
    console.log("  No unpaid invoices found.\n");
    return [];
  }

  console.log(
    `  ${"ID".padEnd(30)} ${"Amount".padEnd(12)} ${"Due".padEnd(12)} ${"Customer".padEnd(30)}`
  );
  console.log("  " + "-".repeat(84));

  for (const inv of invoices.data) {
    const amount = `${(inv.amount_due / 100).toFixed(2)} ${inv.currency.toUpperCase()}`;
    const due = inv.due_date
      ? new Date(inv.due_date * 1000).toISOString().split("T")[0]
      : "N/A";
    console.log(
      `  ${inv.id.padEnd(30)} ${amount.padEnd(12)} ${due.padEnd(12)} ${(inv.customer_email || "N/A").padEnd(30)}`
    );
  }
  console.log(`\n  Total unpaid: ${invoices.data.length}\n`);

  return invoices.data;
}

async function processRefund(stripe, args) {
  const paymentIntent = args.payment_intent;
  const amount = args.amount ? parseInt(args.amount, 10) : undefined;

  if (!paymentIntent) {
    console.error("Error: --payment-intent required (e.g., pi_xxxxx)");
    exit(1);
  }

  console.log(`\n  Processing refund for: ${paymentIntent}`);
  if (amount) console.log(`  Partial refund: ${(amount / 100).toFixed(2)}`);
  else console.log(`  Full refund`);
  console.log();

  const refundData = { payment_intent: paymentIntent };
  if (amount) refundData.amount = amount;

  const refund = await stripe.refunds.create(refundData);

  logEvent({
    event: "refund_processed",
    payment_intent: paymentIntent,
    refund_id: refund.id,
    amount: refund.amount,
    currency: refund.currency,
    status: refund.status,
  });

  console.log(`  Refund processed!`);
  console.log(`  Refund ID: ${refund.id}`);
  console.log(`  Amount: ${(refund.amount / 100).toFixed(2)} ${refund.currency.toUpperCase()}`);
  console.log(`  Status: ${refund.status}\n`);

  return refund;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const args = parseArgs();

  if (!args.command) {
    console.log(`
  CashClaw Stripe Operations

  Commands:
    create-link     Create a payment link
    create-invoice  Create and send an invoice
    check-status    Check invoice payment status
    send-reminder   Send a payment reminder
    list-unpaid     List all unpaid invoices
    refund          Process a refund

  Examples:
    node stripe-ops.js create-link --amount 2900 --description "SEO Audit"
    node stripe-ops.js create-invoice --email "client@co.com" --amount 2900
    node stripe-ops.js check-status --invoice "in_xxxxx"
    node stripe-ops.js send-reminder --invoice "in_xxxxx" --template gentle
    node stripe-ops.js list-unpaid
    node stripe-ops.js refund --payment-intent "pi_xxxxx"
`);
    exit(0);
  }

  const stripe = getStripe();

  switch (args.command) {
    case "create-link":
      await createPaymentLink(stripe, args);
      break;
    case "create-invoice":
      await createInvoice(stripe, args);
      break;
    case "check-status":
      await checkPaymentStatus(stripe, args);
      break;
    case "send-reminder":
      await sendReminder(stripe, args);
      break;
    case "list-unpaid":
      await listUnpaid(stripe);
      break;
    case "refund":
      await processRefund(stripe, args);
      break;
    default:
      console.error(`Unknown command: ${args.command}`);
      console.error('Run without arguments to see available commands.');
      exit(1);
  }
}

main().catch((err) => {
  console.error(`\n  Stripe Error: ${err.message}`);
  if (err.type === "StripeAuthenticationError") {
    console.error("  Check your STRIPE_SECRET_KEY.");
  }
  exit(1);
});
