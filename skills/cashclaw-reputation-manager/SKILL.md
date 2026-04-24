---
name: cashclaw-reputation-manager
description: Monitors online reviews, generates professional response drafts, and creates reputation reports. Covers review aggregation, sentiment analysis, and strategic response planning across major platforms.
metadata:
  {
    "openclaw":
      {
        "emoji": "\u2B50",
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

# CashClaw Reputation Manager

You manage online reputation professionally. Every audit must be thorough,
every response draft must be empathetic and strategic, and every report must
give the client a clear picture of their online standing. Generic "thank you
for your feedback" responses are unacceptable -- every reply must address the
specific review content.

## Pricing Tiers

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Basic | Reputation audit only (snapshot report) | $19 | 6 hours |
| Standard | Audit + response drafts for all negative/neutral reviews | $35 | 12 hours |
| Pro | Full monthly monitoring + responses + strategy recommendations | $49 | 48 hours |

## Reputation Management Workflow

### Step 1: Platform Discovery

Identify all platforms where the client has a public presence:

```yaml
Platform Checklist:
  General Review Sites:
    - [ ] Google Business Profile
    - [ ] Yelp
    - [ ] Trustpilot
    - [ ] Better Business Bureau (BBB)

  Industry-Specific:
    - [ ] G2 (SaaS/Software)
    - [ ] Capterra (Software)
    - [ ] TripAdvisor (Hospitality)
    - [ ] Healthgrades (Healthcare)
    - [ ] Avvo (Legal)
    - [ ] Zillow (Real Estate)
    - [ ] Clutch (Agencies)
    - [ ] Product Hunt (Tech products)

  Social Media:
    - [ ] Facebook Reviews/Recommendations
    - [ ] LinkedIn Company Page
    - [ ] Twitter/X mentions
    - [ ] Instagram comments
    - [ ] Reddit mentions

  App Stores (if applicable):
    - [ ] Apple App Store
    - [ ] Google Play Store

  Other:
    - [ ] Industry forums
    - [ ] Glassdoor (employer brand)
    - [ ] Indeed (employer brand)
```

Document which platforms are active, which have unclaimed profiles, and which
have no presence. An unclaimed Google Business Profile is a critical finding.

### Step 2: Review Aggregation

Collect all reviews from discovered platforms:

```json
{
  "platform": "Google",
  "review_id": "{unique_id}",
  "author": "{reviewer_name}",
  "date": "{ISO8601}",
  "rating": 4,
  "rating_max": 5,
  "text": "{full review text}",
  "response_exists": false,
  "response_text": null,
  "sentiment": "positive",
  "topics": ["customer_service", "product_quality"],
  "priority": "low",
  "action_needed": "none"
}
```

**Aggregation Rules:**
- Collect ALL reviews, not just recent ones (last 12 months minimum).
- For platforms with hundreds of reviews, focus on the last 50 plus all 1-2 star reviews.
- Record whether the business has responded to each review.
- Flag reviews that mention specific employees, legal threats, or false claims.

### Step 3: Sentiment Analysis

Categorize every review and calculate aggregate scores:

```markdown
## Sentiment Breakdown

### Overall Scores
| Platform | Avg Rating | Total Reviews | Response Rate |
|----------|-----------|---------------|---------------|
| Google | 4.2/5 | 127 | 45% |
| Yelp | 3.8/5 | 43 | 12% |
| Trustpilot | 4.5/5 | 89 | 78% |
| **Weighted Average** | **4.2/5** | **259** | **45%** |

### Sentiment Distribution
| Sentiment | Count | Percentage |
|-----------|-------|------------|
| Positive (4-5 stars) | 198 | 76% |
| Neutral (3 stars) | 31 | 12% |
| Negative (1-2 stars) | 30 | 12% |

### Topic Analysis
| Topic | Mentions | Avg Sentiment |
|-------|----------|---------------|
| Customer Service | 89 | Positive |
| Product Quality | 72 | Positive |
| Pricing | 45 | Mixed |
| Delivery/Speed | 38 | Negative |
| Support Response Time | 29 | Negative |
```

**Sentiment Classification Rules:**
- 5 stars with positive text = Positive
- 4 stars = Positive (unless text is mostly negative)
- 3 stars = Neutral
- 2 stars = Negative
- 1 star = Negative
- Text overrides star rating when they conflict

### Step 4: Response Drafting (Standard and Pro)

Write professional response drafts for every unanswered negative and neutral review.

**Response Framework by Rating:**

**1-2 Star Reviews (Negative):**

```markdown
Structure:
1. Acknowledge - Thank them for the feedback (not generic).
2. Empathize - Show you understand why they are frustrated.
3. Address - Respond to the specific issue they raised.
4. Resolve - Offer a concrete next step (not "call us").
5. Offline - Move the conversation to a private channel.

Tone: Professional, empathetic, never defensive.
Length: 60-120 words.
```

Example:

```
Hi {name}, thank you for sharing your experience. I understand how
frustrating it must be to {specific issue from review}. That is not
the standard we hold ourselves to. Our {role} team has looked into
this and {specific action taken or explanation}. I would like to make
this right -- could you reach out to me directly at {email} so we
can resolve this for you? - {Manager Name}, {Title}
```

**3 Star Reviews (Neutral):**

```markdown
Structure:
1. Thank - Genuine appreciation for balanced feedback.
2. Highlight - Acknowledge what they liked.
3. Address - Respond to the criticism constructively.
4. Invite - Ask them to give you another chance.

Tone: Warm, constructive, forward-looking.
Length: 50-90 words.
```

**4-5 Star Reviews (Positive):**

```markdown
Structure:
1. Thank - Specific, not generic.
2. Reinforce - Reference something specific they mentioned.
3. Invite - Encourage them to share or return.

Tone: Grateful, personal, brief.
Length: 30-60 words.
```

**Response Rules (apply to every response):**

```yaml
ALWAYS:
  - Address the reviewer by name
  - Reference specific details from their review
  - Take ownership of mistakes (never blame the customer)
  - Provide a concrete resolution path
  - Sign with a real person's name and title
  - Respond within 24-48 hours of the review

NEVER:
  - Use the same template for multiple responses
  - Be defensive or argumentative
  - Share private customer details publicly
  - Offer compensation publicly (do this offline)
  - Accuse the reviewer of lying
  - Use corporate jargon ("we value your feedback" alone is insufficient)
  - Respond to fake reviews without flagging them first
```

### Step 5: Reputation Report Assembly

Generate the comprehensive report:

```markdown
# Online Reputation Report

**Brand:** {brand_name}
**Date:** {date}
**Tier:** {Basic|Standard|Pro}
**Platforms Analyzed:** {count}

---

## Executive Summary
{3-5 sentences: overall health, critical findings, top recommendation}

## Reputation Score Card
| Metric | Score | Benchmark | Status |
|--------|-------|-----------|--------|
| Overall Rating | 4.2/5 | 4.0+ | GOOD |
| Response Rate | 45% | 80%+ | NEEDS WORK |
| Sentiment Ratio | 76% positive | 70%+ | GOOD |
| Review Volume (monthly) | 12 | 15+ | FAIR |
| Platform Coverage | 4/8 | 6/8 | NEEDS WORK |

## Platform-by-Platform Analysis
{Detailed breakdown per platform}

## Sentiment Analysis
{Topic analysis with trends}

## Critical Reviews Requiring Immediate Response
{Top 5 most urgent unanswered negative reviews with draft responses}

## Response Drafts (Standard/Pro)
{All drafted responses organized by platform and priority}

## Trend Analysis (Pro)
{Rating trend over time: improving, stable, declining}
{Seasonal patterns if observable}
{Impact of response strategy on subsequent reviews}

## Strategic Recommendations
1. {Highest-impact recommendation}
2. {Second recommendation}
3. {Third recommendation}
4. {Fourth recommendation}
5. {Fifth recommendation}

## Action Plan
| Action | Priority | Effort | Expected Impact |
|--------|----------|--------|-----------------|
| {action1} | High | Low | +0.3 rating |
| {action2} | High | Medium | +15% response rate |
| {action3} | Medium | Low | +5 reviews/month |

---
*Generated by CashClaw Reputation Manager | cashclaw.ai*
```

## Quality Checklist

Before delivering, verify:

```
[ ] All major review platforms have been checked
[ ] Review counts and ratings match the actual platform data
[ ] Sentiment analysis covers the last 12 months minimum
[ ] Every response draft addresses the specific review content
[ ] No two response drafts use the same opening line
[ ] Response drafts are signed with a name and title placeholder
[ ] Negative review responses include a concrete resolution step
[ ] No private customer information in response drafts
[ ] Topic analysis includes at least 5 identified themes
[ ] Recommendations are specific and actionable
[ ] Executive summary can stand alone as a decision document
[ ] Platform coverage is complete (no major platform missed)
[ ] Unclaimed profiles are flagged as critical findings
[ ] Response rate calculation is accurate
[ ] Report formatting is consistent throughout
```

## Deliverable Format

Every reputation management delivery includes:

```
deliverables/
  reputation-report-{brand}-{date}.md   - Full reputation analysis
  review-responses.md                    - All drafted responses (Standard/Pro)
  brief-summary.md                       - Executive summary for quick review
```

### review-responses.md Format

```markdown
# Review Response Drafts

**Brand:** {brand_name}
**Date:** {date}
**Total Responses Drafted:** {count}

## Priority: HIGH (respond within 24 hours)

### Google - 1 Star - {reviewer_name} - {date}
**Review:** "{review text excerpt}"
**Draft Response:**
> {response draft}

### Yelp - 2 Stars - {reviewer_name} - {date}
**Review:** "{review text excerpt}"
**Draft Response:**
> {response draft}

## Priority: MEDIUM (respond within 48 hours)

### Google - 3 Stars - {reviewer_name} - {date}
**Review:** "{review text excerpt}"
**Draft Response:**
> {response draft}

## Priority: LOW (respond within 1 week)

### Trustpilot - 4 Stars - {reviewer_name} - {date}
**Review:** "{review text excerpt}"
**Draft Response:**
> {response draft}
```

## Monthly Monitoring Setup (Pro Tier)

For Pro tier clients, set up ongoing monitoring:

```yaml
Monitoring Config:
  Brand: "{brand_name}"
  Check Frequency: "weekly"
  Platforms:
    - google_business
    - yelp
    - trustpilot
    - facebook
    - g2

  Alerts:
    new_negative_review: "immediate"
    rating_drop_threshold: 0.2
    new_platform_mention: "daily_digest"

  Monthly Deliverables:
    - Updated reputation scorecard
    - New review response drafts
    - Trend analysis (month-over-month)
    - Competitor reputation comparison
    - Adjusted strategy recommendations
```

## Quality Standards

- Every response draft must be unique -- no copy-paste templates across reviews.
- Sentiment classification must be verifiable against the actual review text.
- Never inflate ratings or misrepresent review counts. Report what you find.
- If a platform has no reviews, report it as zero, not as missing data.
- Fake review detection: Flag reviews with suspicious patterns (burst of 5-star reviews, generic language, reviewer with no other activity) but never accuse publicly.
- Response drafts must be ready to post -- not outlines, not bullet points.
- Pro tier trend analysis must cover at least 6 months of data if available.
- Recommendations must be prioritized by effort-to-impact ratio.

## Example Commands

```bash
# Run a basic reputation audit
cashclaw reputation --brand "Acme Corp" --url "https://acme.com" --tier basic

# Audit with response drafts
cashclaw reputation --brand "Acme Corp" --url "https://acme.com" --tier standard --responses

# Full pro monitoring setup
cashclaw reputation --brand "Acme Corp" --url "https://acme.com" --tier pro --monitor monthly

# Generate responses for new reviews only
cashclaw reputation respond --brand "Acme Corp" --since "2026-03-01" --output responses.md

# Check reputation score trend
cashclaw reputation trend --brand "Acme Corp" --months 6
```
