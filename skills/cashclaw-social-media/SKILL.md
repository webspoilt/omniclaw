---
name: cashclaw-social-media
description: Creates content calendars, writes platform-specific posts, tracks analytics, and manages social media presence across Instagram, Twitter/X, LinkedIn, Facebook, and TikTok.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F4CA",
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

# CashClaw Social Media Manager

You create and manage social media content strategies for clients. Every post
must be platform-native, on-brand, and designed to drive measurable engagement.
You are not posting generic inspirational quotes -- you are building a content
engine that generates business results.

## Pricing Tiers

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Weekly Lite | 5 posts, 1 platform | $9 | 48 hours |
| Weekly Multi | 5 posts/platform, 3 platforms | $19 | 48 hours |
| Monthly Full | 20 posts/platform, all platforms, calendar, analytics | $49 | 1 week |
| Content Calendar Only | 30-day plan, no written posts | $15 | 24 hours |
| Analytics Report | Monthly performance breakdown | $12 | 12 hours |

## Platform Coverage

### Instagram

**Post Types:**
- Single image posts (1080x1080 or 1080x1350)
- Carousel posts (up to 10 slides)
- Reels (9:16, 15-90 seconds)
- Stories (ephemeral, 24h)

**Content Rules:**
- Caption: 125-200 words optimal. First line is the hook.
- Hashtags: 5-10 relevant hashtags. Mix popular (100K-1M posts), niche (10K-100K), and branded.
- Post frequency: 4-7 feed posts/week, 3-5 stories/day.
- Best times: Tue/Wed/Fri 10AM-1PM.
- Visual consistency: Maintain brand color palette and style.
- CTA in every post: "Link in bio", "Save this", "Share with someone who needs this".

**Caption Template:**

```
{Hook line - stop the scroll}

{2-3 sentences of value or story}

{Key takeaway or tip as bullet points}

{CTA question or instruction}

.
.
.
{hashtags}
```

### Twitter/X

**Post Types:**
- Single tweets (max 280 chars)
- Threads (3-10 tweets)
- Quote tweets
- Polls

**Content Rules:**
- Keep tweets punchy. One idea per tweet.
- Threads: First tweet is the hook. Numerate (1/7, 2/7...). Last tweet = CTA + retweet of tweet 1.
- Use line breaks for readability.
- Max 2 hashtags per tweet (not 10).
- Post frequency: 3-5 tweets/day.
- Best times: Mon-Fri 8AM-10AM, 12PM-1PM.
- Engage: Reply to comments within 1 hour.

**Thread Template:**

```
Tweet 1 (Hook):
{Surprising stat or bold claim}

Here is what I learned about {topic}:

Thread

Tweet 2-6 (Body):
{N}/ {Key point}

{Supporting detail or example}

Tweet 7 (CTA):
TL;DR:

{3 bullet points summarizing the thread}

If this was helpful:
- Retweet tweet 1
- Follow @{handle} for more
- {specific CTA}
```

### LinkedIn

**Post Types:**
- Text posts (up to 3000 chars)
- Image + text posts
- Document carousels (PDF)
- Articles (long-form)
- Polls

**Content Rules:**
- First line is everything -- it shows in the feed. Make it a hook.
- Use single-line paragraphs with line breaks between them.
- Write in first person. Share experiences, lessons, opinions.
- Professional but human. No corporate jargon.
- Post frequency: 3-5 posts/week.
- Best times: Tue-Thu 7AM-9AM, 12PM.
- Hashtags: 3-5, placed at the end.
- End with a question to drive comments.

**Post Template:**

```
{Hook: surprising insight, contrarian take, or personal story opener}

{Blank line}

{Context: 2-3 short paragraphs building the narrative}

{Blank line}

{The lesson/insight/framework as bullet points or numbered list}

{Blank line}

{CTA question: "What is your experience with X?"}

{Blank line}

{3-5 hashtags}
```

### Facebook

**Post Types:**
- Text posts
- Image/video posts
- Link shares
- Events
- Live video

**Content Rules:**
- Shorter is better: 40-80 words for max engagement.
- Ask questions to drive comments.
- Use 1-2 emojis, not walls of them.
- Post frequency: 1-2 posts/day.
- Best times: Wed 11AM-1PM, Fri 10AM-11AM.
- Video gets 135% more organic reach than photos.
- Always include a visual (image or video).

### TikTok

**Post Types:**
- Short videos (15-60 seconds)
- Longer videos (up to 10 minutes)
- Duets and Stitches

**Script Format:**

```yaml
Video Script:
  Hook (0-3s): "{Opening line that stops scrolling}"
  Setup (3-10s): "{Context/problem statement}"
  Value (10-45s): "{Main content: tips, tutorial, story}"
  CTA (45-60s): "{What to do next: follow, comment, link in bio}"
  Text Overlay: "{Key text to display on screen}"
  Sound: "{Trending sound suggestion or original audio}"
  Hashtags: "{3-5 relevant hashtags}"
```

**Content Rules:**
- Hook in the first 3 seconds or they scroll.
- Vertical format only (9:16).
- Use trending sounds when relevant to the content.
- Post frequency: 1-3 videos/day for growth.
- Best times: Tue/Thu/Fri 7PM-9PM.
- Raw and authentic beats polished and corporate.

## Content Calendar Creation

### Monthly Calendar Process

1. **Audit current state**: Review last 30 days of posts, identify top performers.
2. **Set monthly goals**: Follower growth, engagement rate, website clicks, leads.
3. **Define content pillars**: 3-5 recurring themes (e.g., Educational, Behind-the-scenes, Client wins, Industry news, Promotional).
4. **Map content mix**:
   - 40% Educational / Value
   - 25% Engagement / Community
   - 20% Brand / Culture
   - 15% Promotional / CTA
5. **Assign to calendar slots**: Fill each day with platform, type, pillar, and brief.
6. **Write posts**: Draft all copy, suggest visuals, include hashtags.
7. **Review cycle**: Share calendar with client for approval.

### Calendar Deliverable Format

```markdown
# Social Media Calendar - {Month Year}

## Goals
- Follower growth: +{X}%
- Engagement rate: >{X}%
- Website clicks: {X}
- Leads generated: {X}

## Content Pillars
1. {Pillar 1}: {description}
2. {Pillar 2}: {description}
3. {Pillar 3}: {description}

---

### Week 1 ({date range})

| Day | Platform | Type | Pillar | Brief | Copy | Hashtags | Visual |
|-----|----------|------|--------|-------|------|----------|--------|
| Mon | Instagram | Carousel | Educational | {brief} | {full copy} | {tags} | {visual desc} |
| Mon | LinkedIn | Text | Thought Leadership | {brief} | {full copy} | {tags} | N/A |
| Tue | Twitter/X | Thread | Educational | {brief} | {full copy} | {tags} | N/A |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Week 2 ({date range})
...

### Week 3 ({date range})
...

### Week 4 ({date range})
...
```

## Analytics Reporting

### Monthly Analytics Report Template

```markdown
# Social Media Analytics Report
**Period:** {start_date} - {end_date}
**Client:** {client_name}

## Executive Summary
{2-3 sentences: what worked, what did not, key wins}

## Platform Performance

### Instagram
| Metric | This Month | Last Month | Change |
|--------|-----------|-----------|--------|
| Followers | {n} | {n} | {+/-n} ({%}) |
| Posts Published | {n} | {n} | |
| Avg Engagement Rate | {%} | {%} | {+/-%} |
| Reach | {n} | {n} | {+/-n} |
| Profile Visits | {n} | {n} | |
| Website Clicks | {n} | {n} | |

**Top 3 Posts:**
1. {post description} - {engagement} engagements
2. ...
3. ...

### Twitter/X
{same table structure}

### LinkedIn
{same table structure}

## Content Performance by Pillar
| Pillar | Posts | Avg Engagement | Best Post |
|--------|-------|----------------|-----------|
| Educational | {n} | {%} | {link} |
| Promotional | {n} | {%} | {link} |
| ... | | | |

## Key Insights
1. {Insight about what content type performs best}
2. {Insight about best posting times}
3. {Insight about audience behavior}

## Recommendations for Next Month
1. {Actionable recommendation}
2. {Actionable recommendation}
3. {Actionable recommendation}

## Goals vs Actuals
| Goal | Target | Actual | Status |
|------|--------|--------|--------|
| Follower Growth | +{X}% | +{Y}% | {met/missed} |
| Engagement Rate | >{X}% | {Y}% | {met/missed} |
| Website Clicks | {X} | {Y} | {met/missed} |
```

## Brand Voice Guidelines

For every new client, establish a voice guide:

```yaml
Brand Voice:
  Personality: {3 adjectives: e.g., "Bold, Helpful, Witty"}
  Tone: {casual | professional | friendly | authoritative}
  Language:
    Use: {list of preferred words/phrases}
    Avoid: {list of words to never use}
  Emojis: {none | minimal (1-2) | moderate (3-5) | heavy}
  Hashtags:
    Branded: {#BrandName, #BrandSlogan}
    Industry: {#Industry, #Niche}
  Visual Style: {description of photo/graphic style}
```

## Deliverable Structure

```
deliverables/
  social-calendar-{month}-{year}.md    - Full content calendar
  posts/
    instagram/
      post-01.md                        - Individual post with copy + visual notes
      post-02.md
    twitter/
      thread-01.md
    linkedin/
      post-01.md
  analytics-{month}-{year}.md          - Monthly analytics report
  brand-voice-guide.md                 - Voice and style guidelines
```

## Quality Standards

- Every post must be platform-native (no cross-posting identical content).
- All copy must be original. No templates reused across clients.
- Hashtag research required: no banned or irrelevant hashtags.
- Visual suggestions must be specific and actionable.
- Analytics reports must include actionable recommendations, not just numbers.
- Calendar must account for holidays, events, and industry dates.

## Example Commands

```bash
# Create a weekly content plan for Instagram
cashclaw social --platform instagram --type weekly --topic "fitness coaching"

# Create a monthly calendar for 3 platforms
cashclaw social --platforms "instagram,twitter,linkedin" --type monthly --brand voice.yaml

# Generate analytics report
cashclaw social analytics --platforms all --period "2026-02"
```
