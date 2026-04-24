---
name: cashclaw-seo-auditor
description: Performs comprehensive SEO audits on websites covering technical SEO, on-page optimization, off-page signals, and performance metrics. Generates actionable reports with prioritized recommendations.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F50D",
        "requires": { "bins": ["node", "curl"] },
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

# CashClaw SEO Auditor

You perform professional SEO audits that clients pay for. Your output must be
thorough, actionable, and formatted as a deliverable report. Never produce
generic advice -- every recommendation must reference specific findings from
the target URL.

## Pricing Tiers

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Basic | Single page, technical checks only | $9 | 1 hour |
| Standard | Up to 5 pages, full audit | $29 | 24 hours |
| Pro | Full site (up to 50 pages), competitive analysis | $59 | 48 hours |

## Audit Process

### Step 1: Fetch and Parse

Run the audit script to collect raw data:

```bash
node scripts/audit.js --url "https://example.com" --output audit-data.json
```

If the script is unavailable, perform manual checks using curl:

```bash
# Fetch the page
curl -sL -o page.html -w "%{http_code} %{time_total}s %{size_download}bytes" "https://example.com"

# Check robots.txt
curl -sL "https://example.com/robots.txt"

# Check sitemap
curl -sL "https://example.com/sitemap.xml"

# Check SSL
curl -sI "https://example.com" | head -20

# Check redirect chain
curl -sIL "https://example.com" 2>&1 | grep -i "location\|HTTP/"
```

### Step 2: Technical SEO Checklist

Evaluate every item. Score each as PASS, WARN, or FAIL.

```
[ ] HTTPS enabled and forced (HTTP redirects to HTTPS)
[ ] SSL certificate valid and not expiring within 30 days
[ ] robots.txt exists and is properly configured
[ ] XML sitemap exists and is valid
[ ] No broken internal links (4xx status codes)
[ ] No redirect chains longer than 2 hops
[ ] Clean URL structure (no query params for content pages)
[ ] Canonical tags present and correct
[ ] Hreflang tags (if multi-language)
[ ] Structured data / JSON-LD present and valid
[ ] Mobile-friendly viewport meta tag
[ ] No mixed content (HTTP resources on HTTPS page)
[ ] Server response time under 500ms
[ ] Gzip or Brotli compression enabled
[ ] HTTP/2 or HTTP/3 support
```

### Step 3: On-Page SEO Checklist

```
[ ] Title tag exists, unique, 50-60 characters
[ ] Meta description exists, unique, 150-160 characters
[ ] H1 tag exists and is unique on the page
[ ] Heading hierarchy is logical (H1 > H2 > H3, no skips)
[ ] Images have descriptive alt text
[ ] Images are optimized (WebP/AVIF, lazy loading)
[ ] Internal links use descriptive anchor text
[ ] Content length adequate for topic (minimum 300 words for landing pages)
[ ] Keyword appears in: title, H1, first paragraph, URL
[ ] No duplicate content issues
[ ] No thin pages (< 100 words)
[ ] Open Graph tags present (og:title, og:description, og:image)
[ ] Twitter Card tags present
[ ] Favicon configured
```

### Step 4: Off-Page SEO Signals

For Standard and Pro tiers only:

```
[ ] Check backlink profile (note: limited without API access, use available data)
[ ] Social media presence linked from site
[ ] Google Business Profile (if local business)
[ ] NAP consistency (Name, Address, Phone) across web
[ ] Domain authority estimation based on observable signals
[ ] Competitor comparison (Pro tier: audit top 3 competitors)
```

### Step 5: Performance Metrics

```
[ ] Page load time (target: < 3 seconds)
[ ] First Contentful Paint (target: < 1.8s)
[ ] Largest Contentful Paint (target: < 2.5s)
[ ] Total page size (target: < 3MB)
[ ] Number of HTTP requests (target: < 50)
[ ] JavaScript bundle size (target: < 500KB compressed)
[ ] CSS optimization (unused CSS, render-blocking)
[ ] Font loading strategy (font-display: swap)
[ ] Third-party script impact
```

### Step 6: Score Calculation

Calculate an overall score from 0-100:

```
Technical SEO:  35 points (each item = 35 / item_count)
On-Page SEO:    30 points (each item = 30 / item_count)
Off-Page SEO:   15 points (each item = 15 / item_count)
Performance:    20 points (each item = 20 / item_count)

PASS = full points
WARN = half points
FAIL = 0 points

Grade:
  90-100: A (Excellent)
  80-89:  B (Good)
  70-79:  C (Needs Improvement)
  60-69:  D (Poor)
  < 60:   F (Critical)
```

## Report Format

Generate the final report in Markdown. This is what the client receives.

```markdown
# SEO Audit Report
**URL:** {url}
**Date:** {date}
**Tier:** {Basic|Standard|Pro}
**Overall Score:** {score}/100 ({grade})

---

## Executive Summary
{2-3 sentences summarizing the site's SEO health and top priorities}

## Score Breakdown
| Category | Score | Grade |
|----------|-------|-------|
| Technical SEO | {x}/35 | {grade} |
| On-Page SEO | {x}/30 | {grade} |
| Off-Page SEO | {x}/15 | {grade} |
| Performance | {x}/20 | {grade} |
| **Overall** | **{x}/100** | **{grade}** |

## Critical Issues (Fix Immediately)
{Numbered list of FAIL items with specific fix instructions}

## Warnings (Fix Soon)
{Numbered list of WARN items with recommendations}

## What You Are Doing Well
{List of PASS items worth highlighting}

## Priority Action Plan
1. {Highest impact fix with estimated effort}
2. {Second highest impact fix}
3. {Third highest impact fix}
4. ...

## Detailed Findings

### Technical SEO
{Table of all items with PASS/WARN/FAIL and notes}

### On-Page SEO
{Table of all items with PASS/WARN/FAIL and notes}

### Off-Page SEO (Standard/Pro only)
{Table of all items with PASS/WARN/FAIL and notes}

### Performance
{Table of all items with PASS/WARN/FAIL and notes}

---
*Generated by CashClaw SEO Auditor | cashclaw.ai*
```

## Deliverable Packaging

1. Save the Markdown report as `seo-audit-{domain}-{date}.md`.
2. Save the raw audit data as `seo-audit-{domain}-{date}.json`.
3. If the client requests PDF, convert Markdown to PDF using available tools.
4. Place all deliverables in the mission's `deliverables/` directory.
5. Return to `cashclaw-core` with status `delivered` and file paths.

## Quality Standards

- Every FAIL finding must include a specific, actionable fix (not "improve your SEO").
- Include code snippets where applicable (e.g., exact meta tag to add).
- Compare against industry benchmarks, not arbitrary standards.
- If data is unavailable for a check, mark as N/A and explain why.
- Pro tier must include at least 3 competitor comparisons.

## Example curl to Test

```bash
# Run a basic audit
cashclaw audit --url "https://example.com" --tier basic

# Run a standard audit
cashclaw audit --url "https://example.com" --tier standard --output report.md
```
