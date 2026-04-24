#!/usr/bin/env node

/**
 * CashClaw SEO Auditor - Technical Audit Script
 *
 * Usage:
 *   node audit.js --url "https://example.com" [--output audit.json]
 *
 * Fetches a URL, parses the HTML, and generates structured audit data
 * covering meta tags, headings, images, links, and performance signals.
 */

const { argv, exit } = require("process");
const { writeFileSync } = require("fs");

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

function parseArgs() {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--url" && argv[i + 1]) {
      args.url = argv[++i];
    } else if (argv[i] === "--output" && argv[i + 1]) {
      args.output = argv[++i];
    }
  }
  if (!args.url) {
    console.error("Usage: node audit.js --url <URL> [--output <file.json>]");
    exit(1);
  }
  return args;
}

// ---------------------------------------------------------------------------
// HTML helpers (lightweight, no external deps)
// ---------------------------------------------------------------------------

function extractTag(html, tag) {
  const re = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "gi");
  const matches = [];
  let m;
  while ((m = re.exec(html)) !== null) matches.push(m[1].trim());
  return matches;
}

function extractMeta(html, nameOrProperty) {
  // <meta name="..." content="..."> or <meta property="..." content="...">
  const re = new RegExp(
    `<meta[^>]*(?:name|property)=["']${nameOrProperty}["'][^>]*content=["']([^"']*)["']`,
    "i"
  );
  const alt = new RegExp(
    `<meta[^>]*content=["']([^"']*)["'][^>]*(?:name|property)=["']${nameOrProperty}["']`,
    "i"
  );
  const m = html.match(re) || html.match(alt);
  return m ? m[1] : null;
}

function extractTagAttr(html, tag, attr) {
  const re = new RegExp(`<${tag}[^>]*${attr}=["']([^"']*)["']`, "gi");
  const results = [];
  let m;
  while ((m = re.exec(html)) !== null) results.push(m[1]);
  return results;
}

function extractLinks(html) {
  const re = /<a[^>]*href=["']([^"']*)["'][^>]*>([\s\S]*?)<\/a>/gi;
  const links = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    links.push({ href: m[1], text: m[2].replace(/<[^>]*>/g, "").trim() });
  }
  return links;
}

function extractImages(html) {
  const re = /<img[^>]*>/gi;
  const images = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    const tag = m[0];
    const src = (tag.match(/src=["']([^"']*)["']/i) || [])[1] || "";
    const alt = (tag.match(/alt=["']([^"']*)["']/i) || [])[1] || "";
    const loading = (tag.match(/loading=["']([^"']*)["']/i) || [])[1] || "";
    images.push({ src, alt, loading });
  }
  return images;
}

function wordCount(html) {
  const text = html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text ? text.split(" ").length : 0;
}

// ---------------------------------------------------------------------------
// Audit checks
// ---------------------------------------------------------------------------

function check(name, pass, value, note) {
  return {
    name,
    status: pass === null ? "N/A" : pass ? "PASS" : "FAIL",
    value,
    note: note || "",
  };
}

function auditTechnical(url, html, headers, timing) {
  const results = [];

  // HTTPS
  results.push(
    check("HTTPS enabled", url.startsWith("https"), url)
  );

  // Response time
  results.push(
    check(
      "Server response time",
      timing < 500,
      `${timing}ms`,
      timing < 500 ? "Good" : "Slow - target < 500ms"
    )
  );

  // Viewport meta
  const hasViewport = /meta[^>]*name=["']viewport["']/i.test(html);
  results.push(check("Mobile viewport meta", hasViewport, hasViewport));

  // Canonical
  const canonical = (html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']*)["']/i) || [])[1];
  results.push(check("Canonical tag", !!canonical, canonical || "Missing"));

  // Language
  const lang = (html.match(/<html[^>]*lang=["']([^"']*)["']/i) || [])[1];
  results.push(check("HTML lang attribute", !!lang, lang || "Missing"));

  // Charset
  const hasCharset = /meta[^>]*charset/i.test(html);
  results.push(check("Charset declaration", hasCharset, hasCharset));

  // Compression
  const encoding = headers["content-encoding"] || "";
  const compressed = /gzip|br|deflate/i.test(encoding);
  results.push(check("Compression (gzip/br)", compressed, encoding || "None"));

  return results;
}

function auditOnPage(html) {
  const results = [];

  // Title
  const titles = extractTag(html, "title");
  const title = titles[0] || "";
  results.push(
    check(
      "Title tag exists",
      titles.length === 1 && title.length > 0,
      title || "Missing",
      title ? `${title.length} chars` : "No title tag found"
    )
  );
  results.push(
    check(
      "Title length (50-60 chars)",
      title.length >= 50 && title.length <= 60,
      `${title.length} chars`,
      title.length < 50 ? "Too short" : title.length > 60 ? "Too long" : "Good"
    )
  );

  // Meta description
  const desc = extractMeta(html, "description") || "";
  results.push(
    check("Meta description exists", desc.length > 0, desc || "Missing")
  );
  results.push(
    check(
      "Meta description length (150-160)",
      desc.length >= 150 && desc.length <= 160,
      `${desc.length} chars`
    )
  );

  // Headings
  const h1s = extractTag(html, "h1");
  results.push(
    check("H1 tag exists and unique", h1s.length === 1, `${h1s.length} H1 tags found`)
  );

  const h2s = extractTag(html, "h2");
  results.push(
    check("H2 tags present", h2s.length > 0, `${h2s.length} H2 tags`)
  );

  // Images
  const images = extractImages(html);
  const imagesWithAlt = images.filter((img) => img.alt.length > 0);
  const allHaveAlt = images.length === 0 || imagesWithAlt.length === images.length;
  results.push(
    check(
      "Images have alt text",
      allHaveAlt,
      `${imagesWithAlt.length}/${images.length} have alt`,
      allHaveAlt ? "Good" : "Add alt text to all images"
    )
  );

  const lazyLoaded = images.filter((img) => img.loading === "lazy");
  results.push(
    check(
      "Images use lazy loading",
      images.length === 0 || lazyLoaded.length > 0,
      `${lazyLoaded.length}/${images.length} lazy`
    )
  );

  // Open Graph
  const ogTitle = extractMeta(html, "og:title");
  const ogDesc = extractMeta(html, "og:description");
  const ogImage = extractMeta(html, "og:image");
  results.push(
    check("Open Graph tags", !!(ogTitle && ogDesc && ogImage), {
      title: ogTitle || "Missing",
      description: ogDesc || "Missing",
      image: ogImage || "Missing",
    })
  );

  // Twitter Card
  const twCard = extractMeta(html, "twitter:card");
  results.push(check("Twitter Card meta", !!twCard, twCard || "Missing"));

  // Word count
  const wc = wordCount(html);
  results.push(
    check("Content length (300+ words)", wc >= 300, `${wc} words`)
  );

  // Favicon
  const hasFavicon = /<link[^>]*rel=["'](?:shortcut )?icon["']/i.test(html);
  results.push(check("Favicon configured", hasFavicon, hasFavicon));

  return results;
}

function auditLinks(html, baseUrl) {
  const links = extractLinks(html);
  const internal = links.filter((l) => {
    try {
      const u = new URL(l.href, baseUrl);
      return u.hostname === new URL(baseUrl).hostname;
    } catch {
      return false;
    }
  });
  const external = links.filter((l) => !internal.includes(l));
  const emptyAnchors = links.filter((l) => l.text.length === 0);

  return {
    total: links.length,
    internal: internal.length,
    external: external.length,
    emptyAnchors: emptyAnchors.length,
    links: links.slice(0, 50), // cap at 50 for output size
  };
}

// ---------------------------------------------------------------------------
// Score calculation
// ---------------------------------------------------------------------------

function calcScore(checks) {
  let total = 0;
  let passed = 0;
  for (const c of checks) {
    if (c.status === "N/A") continue;
    total++;
    if (c.status === "PASS") passed++;
  }
  return total === 0 ? 100 : Math.round((passed / total) * 100);
}

function grade(score) {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const args = parseArgs();
  const url = args.url;

  console.log(`\n  CashClaw SEO Auditor`);
  console.log(`  Auditing: ${url}\n`);

  const startTime = Date.now();
  let html, headers, status;

  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "CashClawBot/1.0 (+https://cashclaw.ai) Mozilla/5.0 compatible",
        Accept: "text/html,application/xhtml+xml",
      },
      redirect: "follow",
    });
    status = response.status;
    headers = Object.fromEntries(response.headers.entries());
    html = await response.text();
  } catch (err) {
    console.error(`  Failed to fetch ${url}: ${err.message}`);
    exit(1);
  }

  const timing = Date.now() - startTime;

  console.log(`  Status: ${status}`);
  console.log(`  Response time: ${timing}ms`);
  console.log(`  Page size: ${(html.length / 1024).toFixed(1)}KB\n`);

  // Run audits
  const technical = auditTechnical(url, html, headers, timing);
  const onPage = auditOnPage(html);
  const linkData = auditLinks(html, url);

  const allChecks = [...technical, ...onPage];
  const overallScore = calcScore(allChecks);
  const technicalScore = calcScore(technical);
  const onPageScore = calcScore(onPage);

  const audit = {
    url,
    audited_at: new Date().toISOString(),
    response: {
      status,
      timing_ms: timing,
      page_size_bytes: html.length,
      content_type: headers["content-type"] || "",
    },
    scores: {
      overall: overallScore,
      overall_grade: grade(overallScore),
      technical: technicalScore,
      technical_grade: grade(technicalScore),
      on_page: onPageScore,
      on_page_grade: grade(onPageScore),
    },
    technical,
    on_page: onPage,
    links: linkData,
    images: extractImages(html).length,
    word_count: wordCount(html),
    headings: {
      h1: extractTag(html, "h1"),
      h2: extractTag(html, "h2"),
      h3: extractTag(html, "h3"),
    },
  };

  // Output
  const json = JSON.stringify(audit, null, 2);

  if (args.output) {
    writeFileSync(args.output, json, "utf-8");
    console.log(`  Report saved to: ${args.output}`);
  } else {
    console.log(json);
  }

  // Summary
  console.log(`\n  ---- Score Summary ----`);
  console.log(`  Overall:   ${overallScore}/100 (${grade(overallScore)})`);
  console.log(`  Technical: ${technicalScore}/100 (${grade(technicalScore)})`);
  console.log(`  On-Page:   ${onPageScore}/100 (${grade(onPageScore)})`);
  console.log(
    `  Issues:    ${allChecks.filter((c) => c.status === "FAIL").length} failures, ${allChecks.filter((c) => c.status === "PASS").length} passed\n`
  );
}

main().catch((err) => {
  console.error(`Fatal error: ${err.message}`);
  exit(1);
});
