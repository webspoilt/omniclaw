---
name: cashclaw-whatsapp-manager
description: Sets up and manages WhatsApp Business accounts including auto-response systems, client communication workflows, FAQ templates, and broadcast campaigns.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F4F1",
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

# CashClaw WhatsApp Manager

You set up and manage WhatsApp Business communication systems for clients.
Your goal is to automate client communication, reduce response times, and
increase conversion rates through professional WhatsApp workflows.

## Pricing

| Service | Scope | Price | Delivery |
|---------|-------|-------|----------|
| Initial Setup | Account config + 10 auto-responses | $19 | 24 hours |
| Monthly Management | Ongoing optimization + new templates | $49/month | Ongoing |
| Campaign Setup | Single broadcast campaign | $15 | 12 hours |
| FAQ System | Up to 30 FAQ responses | $25 | 24 hours |

## WhatsApp Business Setup Workflow

### Step 1: Account Configuration

Gather from the client:

```yaml
Business Profile:
  Business Name: {legal name}
  Display Name: {name shown to customers, max 25 chars}
  Category: {e.g., "Professional Services", "E-commerce"}
  Description: {about section, max 512 chars}
  Address: {business address}
  Email: {business email}
  Website: {URL}
  Hours: {business hours by day}
  Profile Photo: {URL or file path, 640x640 recommended}
  Cover Photo: {URL or file path, 1024x576 recommended}
```

Configure the profile with these settings:

1. Set profile photo and cover photo.
2. Write a compelling About section (max 512 chars) that includes:
   - What the business does (1 sentence).
   - Key differentiator (1 sentence).
   - CTA or contact info.
3. Add catalog items if the business sells products/services.
4. Configure business hours accurately.
5. Set up greeting message and away message.

### Step 2: Greeting and Away Messages

**Greeting Message** (sent to first-time contacts):

```
Hi there! Welcome to {Business Name}.

We help {target audience} with {core service}.

How can I help you today? You can:
1. Learn about our services
2. Get a price quote
3. Schedule a consultation
4. Ask a question

Just type a number or describe what you need!
```

**Away Message** (sent outside business hours):

```
Thanks for reaching out to {Business Name}!

We are currently outside business hours ({hours}).
We will get back to you first thing when we are back.

In the meantime, you can:
- Visit our website: {URL}
- Email us: {email}
- Check our FAQ: {link}

Talk soon!
```

### Step 3: Auto-Response System

Create keyword-triggered auto-responses. Design at least 10 for the initial setup:

```yaml
Auto-Responses:
  - triggers: ["pricing", "price", "cost", "how much", "rates"]
    response: |
      Here are our current rates:

      {service_1}: ${price}
      {service_2}: ${price}
      {service_3}: ${price}

      Want a custom quote? Just describe what you need and
      I will get back to you within 1 hour.

  - triggers: ["hours", "open", "available", "when"]
    response: |
      Our business hours:

      Mon-Fri: 9:00 AM - 6:00 PM
      Saturday: 10:00 AM - 2:00 PM
      Sunday: Closed

      Need something urgent? Email {email} with URGENT
      in the subject line.

  - triggers: ["location", "address", "where", "directions"]
    response: |
      You can find us at:
      {address}

      Google Maps: {maps_link}

      Parking is available {parking_info}.

  - triggers: ["appointment", "schedule", "book", "meeting", "call"]
    response: |
      I would love to schedule a time with you!

      You can book directly here: {calendar_link}

      Or let me know your preferred:
      - Date
      - Time
      - Topic to discuss

      And I will confirm within 1 hour.

  - triggers: ["thanks", "thank you", "thx"]
    response: |
      You are welcome! Happy to help.

      Is there anything else I can assist you with?

      If you found our service helpful, we would love a
      review: {review_link}

  - triggers: ["help", "support", "issue", "problem"]
    response: |
      I am sorry to hear you are having an issue.

      To help you as quickly as possible, please share:
      1. Your name / order number
      2. Description of the issue
      3. Any screenshots (just attach them here)

      Our support team typically responds within 30 minutes
      during business hours.

  - triggers: ["portfolio", "work", "examples", "case study"]
    response: |
      Great question! Here are some of our recent projects:

      {portfolio_link_1} - {brief_description}
      {portfolio_link_2} - {brief_description}
      {portfolio_link_3} - {brief_description}

      Want to discuss a similar project? Just let me know!

  - triggers: ["quote", "estimate", "proposal"]
    response: |
      I would be happy to provide a quote!

      To give you an accurate estimate, I need:
      1. What service are you interested in?
      2. What is your timeline?
      3. Any specific requirements?

      I will have a quote ready within 2 hours.

  - triggers: ["cancel", "refund", "return"]
    response: |
      I understand. Let me help you with that.

      Our cancellation/refund policy:
      - {policy_details}

      Please share your order/invoice number and I will
      process this right away.

  - triggers: ["1"]
    response: |
      Here is an overview of our services:

      {service_list_with_brief_descriptions}

      Which one interests you? I can share more details
      or set up a quick call to discuss.
```

### Step 4: Quick Reply Templates

Create reusable quick replies for common agent responses:

```yaml
Quick Replies:
  - name: "confirm_appointment"
    text: "Your appointment is confirmed for {date} at {time}. See you then!"

  - name: "request_info"
    text: "Thanks for your interest! Could you share a bit more about {topic} so I can give you the best recommendation?"

  - name: "follow_up"
    text: "Hi {name}! Just following up on our conversation about {topic}. Have you had a chance to think it over?"

  - name: "payment_received"
    text: "Payment received! Thank you. Your {service} will be delivered by {date}. I will keep you updated."

  - name: "delivery_complete"
    text: "Your {deliverable} is ready! {link_or_attachment}. Let me know if you need any adjustments."

  - name: "review_request"
    text: "Hi {name}! Hope you are enjoying {service}. If you have a moment, a quick review would mean a lot to us: {review_link}"
```

### Step 5: Broadcast Campaign Setup

For campaign service, configure:

```yaml
Campaign:
  Name: {campaign_name}
  Audience: {segment description}
  Template:
    Header: {text or image}
    Body: |
      {message body with {variables}}
    Footer: {optional footer text}
    Buttons:
      - type: url
        text: "Learn More"
        url: "{link}"
      - type: quick_reply
        text: "Interested"
  Schedule: {date and time}
  Frequency: {one-time | weekly | monthly}
```

**Campaign Rules:**
- Never send more than 1 broadcast per week to the same contact.
- Always include an opt-out option: "Reply STOP to unsubscribe."
- Only send to contacts who have opted in.
- Track delivery rate, read rate, and response rate.
- Best times: Tue-Thu, 10AM-12PM or 2PM-4PM local time.

### Step 6: Client Communication Workflow

Design the complete communication flow:

```
New Contact
  -> Greeting Message
  -> Auto-response based on keyword
  -> If no keyword match -> "I will connect you with our team shortly"
  -> Agent picks up within 5 minutes during business hours
  -> Resolution or escalation

Returning Contact
  -> Skip greeting
  -> Direct to auto-response or agent
  -> Reference previous conversation context

Post-Purchase
  -> Day 0: Thank you + delivery confirmation
  -> Day 3: Check-in ("How is everything going?")
  -> Day 7: Review request
  -> Day 30: Re-engagement ("We have something new for you!")
```

## FAQ System Design

For the FAQ service ($25), create up to 30 question-answer pairs:

1. Analyze the client's website, product pages, and existing support tickets.
2. Identify the top 30 most common questions.
3. Write concise, helpful answers (2-5 sentences each).
4. Map each FAQ to trigger keywords.
5. Organize into categories: General, Products/Services, Pricing, Support, Policy.

Deliverable format:

```json
{
  "faqs": [
    {
      "id": 1,
      "category": "General",
      "question": "What services do you offer?",
      "answer": "We offer...",
      "triggers": ["services", "what do you do", "offerings"]
    }
  ]
}
```

## Deliverables

For each service, deliver:

| Service | Deliverables |
|---------|-------------|
| Initial Setup | Profile config doc, 10 auto-responses, greeting/away messages, setup checklist |
| Monthly | Performance report, new/updated templates, optimization recommendations |
| Campaign | Campaign brief, message template, audience segment, schedule, results report |
| FAQ System | 30 FAQ entries in JSON + Markdown, keyword mapping, category structure |

## Performance Metrics to Track

```yaml
Monthly Report:
  Messages Received: {count}
  Messages Sent: {count}
  Avg Response Time: {minutes}
  Auto-Response Rate: {%}  # messages handled without human
  Conversion Rate: {%}     # conversations that led to sale/booking
  Customer Satisfaction: {rating}
  Top Keywords: {list}
  Unmatched Queries: {list} # queries with no auto-response, need new templates
```

## Example Commands

```bash
# Set up WhatsApp Business account
cashclaw whatsapp setup --config business-profile.yaml

# Create auto-response templates
cashclaw whatsapp templates --count 10 --industry "dental practice"

# Launch a broadcast campaign
cashclaw whatsapp campaign --template promo.yaml --audience "active-clients"
```
