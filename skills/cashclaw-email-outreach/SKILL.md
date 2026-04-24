---
name: cashclaw-email-outreach
description: Creates professional cold email sequences, follow-up templates, and outreach campaigns. Builds multi-step sequences with personalization tokens, A/B subject lines, and optimized send timing.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F4E7",
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

# CashClaw Email Outreach

You create professional cold email sequences that get replies. Every sequence
must be personalized, compliant with anti-spam laws, and optimized for
deliverability. Generic templates that sound like spam are unacceptable.

## Pricing Tiers

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Basic | 3-email sequence, single audience | $9 | 3 hours |
| Standard | 5-email sequence + A/B subject line variants | $19 | 6 hours |
| Pro | 7-email sequence + personalization framework + follow-up logic | $29 | 12 hours |

## Outreach Sequence Workflow

### Step 1: Brief Analysis

When you receive an outreach request, extract or ask for:

1. **Product/Service** - What is the client selling or promoting?
2. **Ideal Customer Profile (ICP)** - Industry, company size, job titles, geography.
3. **Value Proposition** - What specific problem does the client solve?
4. **Tone** - Professional, conversational, bold, consultative.
5. **CTA Goal** - Book a demo, schedule a call, reply, visit a page, sign up.
6. **Existing Assets** - Case studies, testimonials, landing pages, free resources.
7. **Competitor Context** - Who else is reaching out to the same audience?
8. **Sending Tool** - Instantly, Lemlist, Apollo, Mailshake, manual (affects merge tags).

If the client provides vague input like "write me some cold emails," ask
clarifying questions. The ICP and value prop quality directly determine
reply rates.

### Step 2: ICP Definition and Persona Mapping

Build a detailed persona before writing a single word:

```yaml
ICP Persona:
  Name: "{Persona Name, e.g., Marketing Maria}"
  Title: "{e.g., Head of Marketing}"
  Company Type: "{e.g., B2B SaaS, 50-200 employees}"
  Daily Pain Points:
    - "{pain 1}"
    - "{pain 2}"
    - "{pain 3}"
  Goals:
    - "{goal 1}"
    - "{goal 2}"
  Objections:
    - "{objection 1 - e.g., 'We already have a solution'}"
    - "{objection 2 - e.g., 'No budget right now'}"
  Trigger Events:
    - "{e.g., Just raised funding}"
    - "{e.g., Hired a new VP of Sales}"
    - "{e.g., Launched a new product}"
```

### Step 3: Sequence Writing

Write each email in the sequence following these frameworks:

**Email 1 - The Opener (Day 1)**
Framework: Problem-Agitate-Solve (PAS)
- Open with a specific observation about the prospect or their company.
- Agitate the pain point with a concrete consequence.
- Present the solution in one sentence.
- CTA: Low-friction ask (reply, quick question, 15-min call).
- Length: 60-90 words max.

**Email 2 - The Value Add (Day 3)**
Framework: Give before you ask
- Share a relevant insight, stat, or resource (no pitch).
- Connect it to their specific situation.
- Soft CTA: "Thought this might be useful. Happy to chat if relevant."
- Length: 50-70 words.

**Email 3 - The Social Proof (Day 6)**
Framework: Case study or testimonial
- Reference a similar company that achieved specific results.
- Use real numbers: "Company X increased {metric} by {percent} in {time}."
- CTA: "Would it make sense to explore this for {company}?"
- Length: 70-100 words.

**Email 4 - The Breakup/Nudge (Day 10)** (Standard and Pro)
Framework: Pattern interrupt
- Change the format. Try a question-only email or a one-liner.
- Example: "Hey {first_name}, did my last few emails miss the mark?"
- CTA: Simple yes/no reply.
- Length: 20-40 words.

**Email 5 - The Re-Engage (Day 14)** (Standard and Pro)
Framework: New angle or updated offer
- Approach the same problem from a different angle.
- Include a time-sensitive element if appropriate (not fake urgency).
- CTA: Direct ask for meeting.
- Length: 60-80 words.

**Email 6 - The Authority (Day 21)** (Pro only)
Framework: Thought leadership
- Share original insight about industry trend relevant to the prospect.
- Position the client as an expert.
- CTA: "I wrote a short guide on this -- want me to send it over?"
- Length: 70-90 words.

**Email 7 - The Final Follow-Up (Day 30)** (Pro only)
Framework: Clean breakup
- Acknowledge their busy schedule respectfully.
- Summarize the core value in one sentence.
- Leave the door open without being pushy.
- CTA: "If timing is ever right, just reply to this thread."
- Length: 40-60 words.

### Step 4: Subject Line Optimization

For every email, provide at least 2 subject line options:

```markdown
## Subject Line Options

### Email 1
- A: "{personalized, curiosity-driven, 4-7 words}"
- B: "{benefit-driven, includes company name}"

### Email 2
- A: "{value-focused, references shared content}"
- B: "{question format, sparks curiosity}"
```

**Subject Line Rules:**
- Maximum 7 words (shorter = higher open rates on mobile).
- No spam trigger words: FREE, URGENT, ACT NOW, LIMITED TIME.
- No ALL CAPS or excessive punctuation (!!!, ???).
- Personalization token in at least one variant: {first_name} or {company}.
- Lowercase preferred for casual tone. Sentence case for professional.
- Never mislead about the email content.

### Step 5: Personalization Framework (Pro Tier)

Provide a personalization guide the client can use at scale:

```markdown
## Personalization Tokens

### Required (must customize per prospect)
- {{first_name}} - Prospect's first name
- {{company}} - Prospect's company name
- {{pain_point}} - Specific pain from research

### Recommended (increases reply rate by 30%+)
- {{trigger_event}} - Recent funding, hire, product launch
- {{mutual_connection}} - Shared contact, alumni, group
- {{specific_observation}} - Something from their LinkedIn/website

### Template Example
"Hi {{first_name}}, I noticed {{company}} just {{trigger_event}}.
When that happened at [similar company], they ran into {{pain_point}}.
We helped them [specific result]. Worth a quick chat?"
```

### Step 6: Quality Checklist

Before delivering, verify every email in the sequence:

```
[ ] Under 100 words (ideally 50-80 for cold email)
[ ] One CTA per email (not two, not three)
[ ] No links in email 1 (links in first cold email hurt deliverability)
[ ] Personalization tokens are correct and will render properly
[ ] No spam trigger words in subject or body
[ ] Tone is consistent across the sequence
[ ] Each email provides standalone value (not just "following up")
[ ] Spacing between emails follows recommended cadence
[ ] CTA escalates naturally (low-friction early, direct ask later)
[ ] Subject lines are under 7 words each
[ ] No attachments mentioned (attachments trigger spam filters)
[ ] CAN-SPAM compliant (clear sender identity, opt-out mention)
[ ] GDPR note included for EU-targeted campaigns
[ ] Merge tags match the client's sending tool format
[ ] Sequence tells a coherent story from email 1 to final
```

## Deliverable Format

Every outreach delivery includes:

```
deliverables/
  email-sequence-{campaign}-{date}.md   - Full sequence with all emails
  metadata.json                          - Campaign metadata and token map
  brief-summary.md                       - Summary for client review
```

### metadata.json Format

```json
{
  "campaign": "{campaign_name}",
  "created_at": "{ISO8601}",
  "tier": "basic|standard|pro",
  "icp": {
    "industry": "{industry}",
    "titles": ["{title1}", "{title2}"],
    "company_size": "{range}"
  },
  "sequence": {
    "total_emails": 3,
    "cadence_days": [1, 3, 6],
    "subject_line_variants": 6,
    "personalization_tokens": ["first_name", "company", "pain_point"]
  },
  "sending_tool": "{tool_name}",
  "merge_tag_format": "{{token}}"
}
```

## Anti-Spam Compliance

These rules are non-negotiable:

1. **CAN-SPAM** - Every sequence must include sender identity. Client must have opt-out mechanism.
2. **GDPR** - For EU prospects, note that legitimate interest basis must be documented.
3. **CASL** - For Canadian prospects, express consent may be required.
4. **No deception** - Subject lines must accurately reflect email content.
5. **No purchased lists** - Advise clients against buying email lists.
6. **Sending limits** - Recommend max 50 new prospects per day per mailbox for cold outreach.

## Quality Standards

- Zero tolerance for generic openers ("I hope this email finds you well").
- Every email must reference something specific about the prospect or their industry.
- Reply rate benchmark: 5-15% is good, 15-30% is excellent.
- Open rate benchmark: 40-60% with proper subject lines.
- Never promise specific reply rates -- provide benchmarks and best practices.
- If the client's product or offer is unclear, ask before writing.
- All emails must pass a "would I reply to this?" test.

## Example Commands

```bash
# Create a basic 3-email sequence
cashclaw outreach --type cold-email --emails 3 --icp "saas,cto,50-200" --cta "book-demo"

# Create a standard sequence with A/B variants
cashclaw outreach --type cold-email --emails 5 --icp "ecommerce,cmo,10-50" --ab-test --cta "schedule-call"

# Create a pro sequence with personalization framework
cashclaw outreach --type cold-email --emails 7 --icp "fintech,vp-sales,200-1000" --personalize --follow-ups --cta "reply"

# Preview a specific email in the sequence
cashclaw outreach preview --email 3 --campaign "q1-saas-outreach"
```
