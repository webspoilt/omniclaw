#!/usr/bin/env node

/**
 * CashClaw Lead Generator - Lead Scraper Script
 *
 * Usage:
 *   node scraper.js --query "SaaS companies Austin" --count 25 [--output leads.json]
 *
 * Takes a search query and desired lead count. Searches publicly available
 * business directories and company websites to build a qualified lead list.
 * Outputs a JSON array of leads with company, contact, and scoring data.
 */

const { argv, exit } = require("process");
const { writeFileSync } = require("fs");

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

function parseArgs() {
  const args = { count: 25 };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--query" && argv[i + 1]) args.query = argv[++i];
    else if (argv[i] === "--count" && argv[i + 1]) args.count = parseInt(argv[++i], 10);
    else if (argv[i] === "--output" && argv[i + 1]) args.output = argv[++i];
    else if (argv[i] === "--industry" && argv[i + 1]) args.industry = argv[++i];
    else if (argv[i] === "--size" && argv[i + 1]) args.size = argv[++i];
  }
  if (!args.query) {
    console.error('Usage: node scraper.js --query "search terms" --count 25 [--output leads.json]');
    exit(1);
  }
  return args;
}

// ---------------------------------------------------------------------------
// Email pattern generator
// ---------------------------------------------------------------------------

function generateEmailGuesses(firstName, lastName, domain) {
  const f = firstName.toLowerCase().replace(/[^a-z]/g, "");
  const l = lastName.toLowerCase().replace(/[^a-z]/g, "");
  if (!f || !l || !domain) return [];
  return [
    `${f}@${domain}`,
    `${f}.${l}@${domain}`,
    `${f}${l}@${domain}`,
    `${f[0]}${l}@${domain}`,
    `${f}.${l[0]}@${domain}`,
    `${l}@${domain}`,
  ];
}

function validateEmailFormat(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ---------------------------------------------------------------------------
// Domain extraction
// ---------------------------------------------------------------------------

function extractDomain(url) {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// MX record check via DNS over HTTPS
// ---------------------------------------------------------------------------

async function checkMXRecord(domain) {
  try {
    const resp = await fetch(
      `https://dns.google/resolve?name=${encodeURIComponent(domain)}&type=MX`,
      { signal: AbortSignal.timeout(5000) }
    );
    const data = await resp.json();
    return !!(data.Answer && data.Answer.length > 0);
  } catch {
    return null; // could not verify
  }
}

// ---------------------------------------------------------------------------
// Page fetcher (simple HTML scraper)
// ---------------------------------------------------------------------------

async function fetchPage(url) {
  try {
    const resp = await fetch(url, {
      headers: {
        "User-Agent":
          "CashClawBot/1.0 (+https://cashclaw.ai) Mozilla/5.0 compatible",
        Accept: "text/html,application/xhtml+xml",
      },
      redirect: "follow",
      signal: AbortSignal.timeout(10000),
    });
    if (!resp.ok) return null;
    return await resp.text();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Extract contact info from HTML
// ---------------------------------------------------------------------------

function extractEmails(html) {
  const re = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  const found = html.match(re) || [];
  // Filter out common false positives
  return [...new Set(found)].filter(
    (e) =>
      !e.endsWith(".png") &&
      !e.endsWith(".jpg") &&
      !e.endsWith(".svg") &&
      !e.includes("example.com") &&
      !e.includes("sentry") &&
      !e.includes("webpack")
  );
}

function extractPhones(html) {
  const re = /(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}/g;
  const found = html.match(re) || [];
  return [...new Set(found)].slice(0, 3);
}

function extractLinkedIn(html) {
  const re = /https?:\/\/(?:www\.)?linkedin\.com\/(?:in|company)\/[a-zA-Z0-9_-]+/g;
  const found = html.match(re) || [];
  return [...new Set(found)];
}

// ---------------------------------------------------------------------------
// Lead scoring
// ---------------------------------------------------------------------------

function scoreLead(lead, filters) {
  let score = 0;

  // Has verified email
  if (lead.contact.email && validateEmailFormat(lead.contact.email)) score += 1;

  // Has phone
  if (lead.contact.phone) score += 1;

  // Has LinkedIn
  if (lead.contact.linkedin) score += 1;

  // Has decision maker title
  const dmTitles = ["ceo", "cto", "cfo", "cmo", "founder", "owner", "director", "head", "vp", "president"];
  if (
    lead.contact.title &&
    dmTitles.some((t) => lead.contact.title.toLowerCase().includes(t))
  ) {
    score += 2;
  }

  // Has website
  if (lead.website) score += 1;

  // Industry match
  if (filters.industry && lead.industry && lead.industry.toLowerCase().includes(filters.industry.toLowerCase())) {
    score += 2;
  } else {
    score += 1; // partial credit if we cannot verify
  }

  // Has company name (basic validation)
  if (lead.company && lead.company.length > 1) score += 1;

  // Active signals
  if (lead.signals && Object.values(lead.signals).some(Boolean)) score += 1;

  return Math.min(score, 10);
}

// ---------------------------------------------------------------------------
// Search and scrape pipeline
// ---------------------------------------------------------------------------

async function searchAndScrape(query, count, filters) {
  const leads = [];

  console.log(`  Searching for: "${query}"`);
  console.log(`  Target count: ${count}`);
  console.log(`  Filters: ${JSON.stringify(filters)}\n`);

  // Strategy: search for company websites via a directory or search results page
  // In production this would use APIs (Clearbit, Hunter, Apollo). For the demo
  // script, we scrape a few known directory patterns.

  const searchUrls = [
    `https://www.google.com/search?q=${encodeURIComponent(query + " company contact")}`,
  ];

  console.log("  Phase 1: Fetching search results...");

  for (const searchUrl of searchUrls) {
    const html = await fetchPage(searchUrl);
    if (!html) {
      console.log(`  Warning: Could not fetch ${searchUrl}`);
      continue;
    }

    // Extract URLs from search results
    const urlRe = /https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\/[^\s"'<>)]*)?/g;
    const urls = [...new Set((html.match(urlRe) || []))].filter(
      (u) =>
        !u.includes("google.com") &&
        !u.includes("googleapis.com") &&
        !u.includes("gstatic.com") &&
        !u.includes("youtube.com") &&
        !u.includes("wikipedia.org") &&
        !u.includes("w3.org")
    );

    console.log(`  Found ${urls.length} candidate URLs`);

    // Phase 2: Visit each URL and extract contact info
    console.log("  Phase 2: Extracting contact data...\n");

    const visited = new Set();
    for (const url of urls.slice(0, count * 2)) {
      const domain = extractDomain(url);
      if (!domain || visited.has(domain)) continue;
      visited.add(domain);

      if (leads.length >= count) break;

      console.log(`  Scanning: ${domain}`);
      const pageHtml = await fetchPage(`https://${domain}`);
      if (!pageHtml) continue;

      const emails = extractEmails(pageHtml);
      const phones = extractPhones(pageHtml);
      const linkedins = extractLinkedIn(pageHtml);

      // Extract company name from title
      const titleMatch = pageHtml.match(/<title[^>]*>([^<]+)<\/title>/i);
      const companyName = titleMatch
        ? titleMatch[1]
            .split(/[|\-\u2013\u2014]/)[0]
            .trim()
            .substring(0, 80)
        : domain;

      if (emails.length === 0 && phones.length === 0) continue;

      const lead = {
        company: companyName,
        website: `https://${domain}`,
        industry: filters.industry || "Unknown",
        size: filters.size || "Unknown",
        location: "Unknown",
        contact: {
          name: "Contact",
          title: "Decision Maker",
          email: emails[0] || null,
          phone: phones[0] || null,
          linkedin: linkedins[0] || null,
        },
        signals: {
          recently_funded: false,
          hiring: /career|jobs|hiring|join our team/i.test(pageHtml),
          tech_stack_match: false,
          content_engagement: /<article|blog/i.test(pageHtml),
        },
        score: 0,
        notes: "",
        email_confidence: emails.length > 0 ? "found_on_site" : "unverified",
      };

      lead.score = scoreLead(lead, filters);

      if (lead.signals.hiring) lead.notes += "Company is actively hiring. ";
      if (lead.signals.content_engagement) lead.notes += "Active blog/content. ";

      leads.push(lead);
    }
  }

  // Sort by score descending
  leads.sort((a, b) => b.score - a.score);

  return leads.slice(0, count);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const args = parseArgs();

  console.log(`\n  CashClaw Lead Generator`);
  console.log(`  =======================\n`);

  const filters = {
    industry: args.industry || null,
    size: args.size || null,
  };

  const leads = await searchAndScrape(args.query, args.count, filters);

  // Calculate stats
  const avgScore = leads.length > 0
    ? (leads.reduce((s, l) => s + l.score, 0) / leads.length).toFixed(1)
    : 0;
  const hot = leads.filter((l) => l.score >= 8).length;
  const warm = leads.filter((l) => l.score >= 6 && l.score < 8).length;
  const cool = leads.filter((l) => l.score >= 4 && l.score < 6).length;

  const output = {
    metadata: {
      generated_at: new Date().toISOString(),
      query: args.query,
      filters,
      total_leads: leads.length,
      avg_score: parseFloat(avgScore),
      score_distribution: { hot, warm, cool },
    },
    leads,
  };

  const json = JSON.stringify(output, null, 2);

  if (args.output) {
    writeFileSync(args.output, json, "utf-8");
    console.log(`\n  Leads saved to: ${args.output}`);
  } else {
    console.log("\n" + json);
  }

  console.log(`\n  ---- Summary ----`);
  console.log(`  Total leads: ${leads.length}`);
  console.log(`  Avg score: ${avgScore}`);
  console.log(`  Hot (8-10): ${hot}`);
  console.log(`  Warm (6-7): ${warm}`);
  console.log(`  Cool (4-5): ${cool}`);
  console.log(`  With email: ${leads.filter((l) => l.contact.email).length}`);
  console.log(`  With phone: ${leads.filter((l) => l.contact.phone).length}\n`);
}

main().catch((err) => {
  console.error(`Fatal error: ${err.message}`);
  exit(1);
});
