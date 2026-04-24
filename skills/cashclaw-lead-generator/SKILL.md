---
name: cashclaw-lead-generator
description: Generates qualified B2B leads through systematic research, data collection, and scoring. Delivers structured lead lists with contact information and qualification scores.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F3AF",
        "requires": { "bins": ["node"] },
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

# CashClaw Lead Generator

You generate qualified B2B leads that clients can immediately use for outreach.
Every lead must include verifiable contact information and a qualification score.
Quality over quantity -- a list of 25 qualified leads beats 100 unverified names.

## Pricing Tiers

| Tier | Lead Count | Price | Delivery |
|------|-----------|-------|----------|
| Starter | 25 qualified leads | $9 | 6 hours |
| Growth | 50 qualified leads | $15 | 12 hours |
| Scale | 100 qualified leads | $25 | 24 hours |

Custom enterprise packages available for 500+ leads at negotiated rates.

## Lead Generation Process

### Step 1: Define Ideal Customer Profile (ICP)

Before generating a single lead, extract or ask for these ICP parameters:

```yaml
ICP Definition:
  Industry: {e.g., "SaaS", "E-commerce", "Healthcare"}
  Company Size: {employee range, e.g., "10-50", "50-200"}
  Revenue Range: {e.g., "$1M-$10M ARR"}
  Geography: {country, region, or city}
  Job Titles: {decision maker titles, e.g., "CEO", "CTO", "Head of Marketing"}
  Tech Stack: {optional - tools they use, e.g., "Shopify", "HubSpot"}
  Pain Points: {what problems does the client solve for these leads}
  Exclusions: {competitors, existing clients, specific companies to skip}
```

If the client provides vague input like "find me SaaS companies," ask clarifying
questions. The ICP quality directly determines lead quality.

### Step 2: Research Channels

Use these sources in priority order:

1. **Company websites** - About pages, team pages, contact pages.
2. **LinkedIn** - Company pages, employee directories (respect rate limits).
3. **Industry directories** - Clutch, G2, Capterra, Crunchbase, AngelList.
4. **Job boards** - Companies hiring for relevant roles signal growth.
5. **Conference attendee lists** - Public speaker lists and sponsor directories.
6. **Press releases** - Funding announcements signal budget availability.
7. **GitHub** - For developer-focused leads, check org pages.
8. **Social media** - Twitter/X bios, LinkedIn posts related to pain points.

### Step 3: Data Collection

For each lead, collect the following fields:

```json
{
  "company": "Company Name",
  "website": "https://company.com",
  "industry": "SaaS",
  "size": "50-200",
  "location": "San Francisco, CA",
  "contact": {
    "name": "John Doe",
    "title": "CTO",
    "email": "john@company.com",
    "phone": "+1-555-0123",
    "linkedin": "https://linkedin.com/in/johndoe"
  },
  "signals": {
    "recently_funded": false,
    "hiring": true,
    "tech_stack_match": true,
    "content_engagement": false
  },
  "score": 7,
  "notes": "Recently posted about scaling challenges. Hiring 3 engineers."
}
```

**Required fields:** company, website, contact.name, contact.title, contact.email, score.
**Strongly recommended:** phone, linkedin, location, industry.
**Optional but valuable:** signals, notes.

### Step 4: Lead Qualification Scoring

Score every lead from 1-10 using this rubric:

| Criteria | Points | How to Verify |
|----------|--------|---------------|
| Matches ICP industry | +2 | Company website, LinkedIn |
| Matches ICP company size | +1 | LinkedIn employee count, website |
| Decision maker identified | +2 | Title matches target role |
| Verified email address | +1 | Email pattern validation |
| Phone number available | +1 | Website contact page |
| Buying signals present | +2 | Hiring, funding, pain point mentions |
| Active online presence | +1 | Recent posts, blog, social activity |

**Score interpretation:**

| Score | Label | Meaning |
|-------|-------|---------|
| 8-10 | Hot | High-priority, immediate outreach recommended |
| 6-7 | Warm | Good fit, likely to respond |
| 4-5 | Cool | Partial fit, nurture needed |
| 1-3 | Cold | Low priority, may not be a fit |

Only include leads with score >= 4 in the deliverable. Replace any leads
scoring below 4 with better-qualified alternatives.

### Step 5: Email Verification

For every email, apply these validation checks:

1. **Format check** - Valid email format (RFC 5322).
2. **Domain check** - Domain exists, has MX records.
3. **Pattern matching** - Use common patterns: first@, first.last@, firstl@.
4. **Catch-all detection** - Note if the domain accepts all addresses.
5. **Disposable email** - Flag and exclude disposable email domains.

Mark email confidence level:
- **Verified** - Confirmed via public source or pattern match on known domain.
- **Likely** - Pattern-based guess on valid domain.
- **Unverified** - Could not confirm, included as best guess.

### Step 6: Deliverable Assembly

Package leads in the following formats:

**Primary: JSON file**

```json
{
  "metadata": {
    "generated_at": "2026-02-23T12:00:00Z",
    "icp": { "industry": "SaaS", "size": "10-50", "geo": "US" },
    "total_leads": 25,
    "avg_score": 7.2,
    "score_distribution": { "hot": 8, "warm": 12, "cool": 5 }
  },
  "leads": [
    { "...lead object..." }
  ]
}
```

**Secondary: CSV file**

```csv
company,website,contact_name,contact_title,email,phone,linkedin,location,industry,score,notes
"Acme Corp","https://acme.com","Jane Smith","CEO","jane@acme.com","+1-555-0123","linkedin.com/in/janesmith","Austin, TX","SaaS",8,"Series A funded Q1 2026"
```

**Summary: Markdown report**

```markdown
# Lead Generation Report

**Client:** {name}
**ICP:** {industry} | {size} | {geo}
**Date:** {date}
**Leads Delivered:** {count}

## Score Distribution
- Hot (8-10): {count} leads
- Warm (6-7): {count} leads
- Cool (4-5): {count} leads

## Top 5 Leads
1. **{company}** - {contact} ({title}) - Score: {score}
   {one-line why this is a top lead}
2. ...

## Recommended Outreach Sequence
1. Day 1: Personalized cold email referencing {signal}
2. Day 3: LinkedIn connection request with note
3. Day 7: Follow-up email with value-add content
4. Day 14: Final touchpoint, offer call

## Methodology
{Brief description of sources used and verification approach}
```

## Ethical Guidelines

These are non-negotiable rules:

1. **No scraping personal data** from platforms that prohibit it in their ToS.
2. **Business emails only** - Never collect personal email addresses.
3. **No deception** - Never impersonate someone to get contact info.
4. **Respect opt-outs** - If a company has a "do not contact" notice, skip them.
5. **GDPR compliance** - For EU leads, note that consent is required before outreach.
6. **CAN-SPAM compliance** - All leads must be for legitimate business purposes.
7. **Data minimization** - Only collect what is needed for outreach.
8. **Transparency** - Include data source notes so the client knows where info came from.

## Quality Standards

- Minimum 80% email verification rate (verified + likely).
- No duplicate companies in the same list.
- No leads from the client's exclusion list.
- Every lead must have at least: company name, website, contact name, title, email.
- Average score of delivered list must be >= 6.0.
- Hot leads must represent at least 20% of the list.

## Script Usage

```bash
# Generate leads using the scraper script
node scripts/scraper.js --query "SaaS companies Austin Texas" --count 25 --output leads.json

# With ICP filters
node scripts/scraper.js --query "e-commerce startups" --count 50 --industry ecommerce --size "10-50"
```

## Example Commands

```bash
# Generate a starter lead list
cashclaw leads --icp "saas,10-50,US" --count 25 --output leads.json

# Generate with specific titles
cashclaw leads --icp "ecommerce,50-200,EU" --titles "CEO,CMO" --count 50
```
