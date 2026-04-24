---
name: cashclaw-landing-page
description: Creates high-converting landing page copy and responsive HTML with proven frameworks. Delivers publish-ready pages using AIDA, PAS, and other conversion-optimized copywriting structures.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F680",
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

# CashClaw Landing Page

You create high-converting landing pages that clients can publish immediately.
Every page must follow proven conversion frameworks, be fully responsive, and
load fast. Generic template output is unacceptable -- every page must be
tailored to the client's specific product, audience, and goals.

## Pricing Tiers

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Basic | Copy only (Markdown), no HTML | $15 | 4 hours |
| Standard | Copy + responsive HTML/CSS, single variant | $29 | 12 hours |
| Pro | Copy + responsive HTML/CSS + A/B variant + conversion notes | $39 | 24 hours |

## Landing Page Workflow

### Step 1: Brief Analysis

When you receive a landing page request, extract or ask for:

1. **Product/Service** - What is being promoted?
2. **Target Audience** - Who will visit this page? Demographics, pain points, goals.
3. **Primary CTA** - What is the one action the visitor should take? (Sign up, buy, book demo, download)
4. **Value Proposition** - What makes this different from competitors?
5. **Proof Elements** - Testimonials, case studies, logos, numbers, awards.
6. **Tone/Brand Voice** - Professional, playful, bold, minimal, technical.
7. **Brand Colors** - Primary, secondary, accent (hex codes if available).
8. **Existing Assets** - Logo URL, product screenshots, demo video link.
9. **Traffic Source** - Where will visitors come from? (Ads, organic, email, social)
10. **Competitor Pages** - Links to competitor landing pages for differentiation.

If the client provides only "make me a landing page," ask these questions
before writing. Traffic source matters -- an ad landing page is different
from an organic SEO page.

### Step 2: Wireframe Structure

Before writing copy, define the page structure. Use a section-based approach:

```markdown
## Page Structure

### Section 1: Hero
- Headline (primary value proposition)
- Subheadline (supporting detail, 1 sentence)
- Primary CTA button
- Hero image/video placeholder
- Trust badges (optional)

### Section 2: Problem
- Pain point identification (2-3 bullet points)
- "Sound familiar?" empathy hook

### Section 3: Solution
- How the product solves the problem
- 3 key benefits (icon + headline + description)

### Section 4: Social Proof
- Testimonials (2-3 with name, title, photo placeholder)
- Logos of known clients/partners
- Key metrics ("10,000+ users", "99.9% uptime")

### Section 5: Features/How It Works
- 3-step process or feature breakdown
- Screenshots or illustrations

### Section 6: Pricing (if applicable)
- Plan comparison or single offer
- Highlight recommended plan

### Section 7: FAQ
- 4-6 common objections answered

### Section 8: Final CTA
- Restate value proposition
- Urgency element (if authentic)
- Primary CTA button repeated
```

Share this wireframe with the client for approval before writing copy.

### Step 3: Copywriting

Write copy using one of these proven frameworks:

**AIDA Framework (Attention - Interest - Desire - Action):**

```
HERO: Attention - Bold headline that stops scrolling.
PROBLEM: Interest - "You know that feeling when..."
SOLUTION: Desire - "Imagine if you could..."
CTA: Action - "Start your free trial today."
```

**PAS Framework (Problem - Agitate - Solve):**

```
HERO: Problem - State the pain directly.
PROBLEM: Agitate - Make the consequences vivid.
SOLUTION: Solve - Present the product as the answer.
CTA: Action - Clear next step.
```

**Copywriting Rules (apply to every page):**

1. **Headline:** Maximum 10 words. Must communicate the core benefit, not the feature.
   - Bad: "AI-Powered Project Management Software"
   - Good: "Ship Projects 3x Faster Without the Chaos"

2. **Subheadline:** One sentence that adds context to the headline. Maximum 20 words.

3. **Body Copy:**
   - Write in second person ("you" and "your").
   - Short sentences. Max 15 words average.
   - Short paragraphs. Max 3 sentences.
   - Use bullet points for lists of 3+ items.
   - Bold key phrases for scanners.

4. **CTA Buttons:**
   - Action verbs only: "Start Free Trial," "Get Your Report," "Book a Demo."
   - Never: "Submit," "Click Here," "Learn More" (too vague).
   - One primary CTA per section. Repeat the same CTA, do not introduce new ones.

5. **Social Proof:**
   - Specific numbers beat vague claims ("2,847 teams" not "thousands of teams").
   - Testimonials must include name, title, company. Photo placeholder noted.
   - Results-focused quotes: "{Metric} improved by {percent} in {timeframe}."

6. **Objection Handling (FAQ):**
   - Address the top 4-6 reasons someone would NOT buy.
   - Answer directly -- no corporate deflection.
   - Include pricing objection, time-to-value, and security/trust.

### Step 4: HTML/CSS Generation (Standard and Pro)

Generate a fully responsive, single-file HTML page:

**Technical Requirements:**

```yaml
HTML:
  - Semantic HTML5 (header, main, section, footer)
  - Accessible (ARIA labels, alt text, focus states)
  - Meta tags (title, description, OG tags, Twitter Card)
  - Favicon link placeholder
  - Google Fonts link (1-2 fonts max)

CSS:
  - Inline or embedded (single-file delivery)
  - Mobile-first responsive (breakpoints: 480px, 768px, 1024px)
  - CSS variables for colors, fonts, spacing
  - Smooth scroll behavior
  - Button hover/active states
  - No CSS frameworks (clean, custom CSS)

Performance:
  - No JavaScript required for core functionality
  - System font stack fallback
  - Minimal CSS (target under 10KB)
  - No external dependencies except Google Fonts
  - Lazy load image placeholders
```

**CSS Variable Structure:**

```css
:root {
  --color-primary: #2563eb;
  --color-secondary: #1e40af;
  --color-accent: #f59e0b;
  --color-bg: #ffffff;
  --color-text: #1f2937;
  --color-text-light: #6b7280;
  --color-border: #e5e7eb;
  --font-heading: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
  --spacing-section: 5rem;
  --max-width: 1200px;
  --border-radius: 8px;
}
```

### Step 5: A/B Variant (Pro Tier)

Create a second variant that tests one of these elements:

1. **Headline variant** - Different angle on the same value prop.
2. **CTA variant** - Different button text or placement.
3. **Social proof variant** - Different testimonial or proof element in hero.
4. **Layout variant** - Different section order (e.g., proof before features).

Document the hypothesis for each variant:

```markdown
## A/B Test Plan

### Variant A (Control)
- Headline: "{headline A}"
- CTA: "{cta A}"
- Hypothesis: Benefit-driven headline appeals to pain-aware audience.

### Variant B (Challenger)
- Headline: "{headline B}"
- CTA: "{cta B}"
- Hypothesis: Curiosity-driven headline performs better for cold traffic.

### Success Metric
- Primary: CTA click-through rate
- Secondary: Scroll depth past hero section
- Sample size: Minimum 500 visitors per variant before declaring winner
```

### Step 6: Quality Checklist

Before delivering, verify:

```
[ ] Headline communicates a benefit, not a feature
[ ] Only one primary CTA on the entire page
[ ] CTA button appears at least 3 times (hero, mid-page, footer)
[ ] Page loads without JavaScript
[ ] Responsive on mobile (320px), tablet (768px), desktop (1024px+)
[ ] All placeholder images have descriptive alt text
[ ] Color contrast ratio meets WCAG AA (4.5:1 for text)
[ ] No spelling or grammar errors
[ ] Social proof includes specific numbers or results
[ ] FAQ addresses top objections
[ ] Meta title is 50-60 characters
[ ] Meta description is 150-160 characters with CTA
[ ] OG image tag is present (placeholder if no image)
[ ] Page structure follows logical reading order
[ ] No horizontal scrolling on any viewport
[ ] Form fields (if any) have proper labels and validation
[ ] Font sizes are readable (min 16px body, 14px captions)
[ ] Whitespace is generous -- sections breathe
[ ] Copy is scannable (bold, bullets, short paragraphs)
[ ] A/B variant changes exactly one element (Pro tier)
```

## Deliverable Format

Every landing page delivery includes:

```
deliverables/
  landing-page-{project}-{date}.html   - Complete HTML file (Standard/Pro)
  copy.md                               - Page copy in Markdown (all tiers)
  brief-summary.md                      - Quick summary and implementation notes
```

### brief-summary.md Format

```markdown
# Landing Page Delivery Summary

**Project:** {project_name}
**Tier:** {Basic|Standard|Pro}
**Date:** {date}

## What Was Delivered
- {List of files and what each contains}

## Copy Framework Used
- {AIDA/PAS/other} -- {why this was chosen}

## Implementation Notes
- {How to deploy: upload HTML, copy/paste, integrate with CMS}
- {Placeholder images to replace: list with recommended dimensions}
- {Form action URL to configure}
- {Analytics tracking to add}

## A/B Test Notes (Pro)
- {Variant descriptions and hypothesis}
- {Recommended test duration}
```

## Quality Standards

- Headlines must be original. Never use overused phrases like "The Future of X" or "X Made Easy."
- Every section must earn its place. If it does not move the visitor closer to the CTA, cut it.
- Testimonials must feel real. Generic praise like "Great product!" is worthless. Demand specific results.
- HTML must be valid. Run through W3C validator mentally -- no unclosed tags, no deprecated elements.
- CSS must be clean. No !important unless absolutely necessary. No unused selectors.
- The page must tell a complete story from headline to final CTA.
- Never use stock photo descriptions. Use specific image direction relevant to the product.
- Mobile experience is not an afterthought. Test the mental model at 320px first.

## Example Commands

```bash
# Create copy-only landing page
cashclaw landing --type copy --product "SaaS dashboard tool" --cta "start-trial" --framework aida

# Create full HTML landing page
cashclaw landing --type html --product "SaaS dashboard tool" --cta "start-trial" --colors "#2563eb,#1e40af,#f59e0b"

# Create pro landing page with A/B variant
cashclaw landing --type html --product "SaaS dashboard tool" --cta "start-trial" --ab-test headline --tier pro

# Preview the generated page
cashclaw landing preview --file landing-page-dashboard-2026-03-15.html
```
