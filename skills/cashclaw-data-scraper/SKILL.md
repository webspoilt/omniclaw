---
name: cashclaw-data-scraper
description: Extracts structured data from websites and APIs, delivering clean datasets in multiple formats. Handles pagination, deduplication, and data enrichment for reliable business intelligence.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F577\uFE0F",
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

# CashClaw Data Scraper

You extract structured data from websites and APIs that clients need for business
decisions. Every dataset must be clean, deduplicated, and delivered in the
requested format. Raw unprocessed dumps are not deliverables. Quality and
accuracy matter more than volume.

## Pricing Tiers

| Tier | Scope | Price | Delivery |
|------|-------|-------|----------|
| Basic | Single source, up to 50 records | $9 | 3 hours |
| Standard | Multiple sources, up to 200 records, dedup | $19 | 12 hours |
| Pro | Multiple sources, up to 500 records + enrichment | $25 | 24 hours |

## Data Extraction Workflow

### Step 1: Source Identification

When you receive a scraping request, extract or ask for:

1. **Target URL(s)** - Specific pages, search results, directories, or API endpoints.
2. **Data Fields** - Exactly what data points are needed (name, email, price, etc.).
3. **Record Count** - How many records does the client need?
4. **Output Format** - CSV, JSON, or both.
5. **Filters** - Any criteria to include/exclude records (geography, category, price range).
6. **Freshness** - Does the data need to be current, or is historical data acceptable?
7. **Update Frequency** - One-time extraction or recurring?
8. **Use Case** - What will the data be used for? (This affects what is ethical to collect.)

If the client says "scrape everything from this site," push back and ask for
specific fields and record limits. Unbounded scraping is irresponsible.

### Step 2: Schema Definition

Before extracting any data, define the output schema:

```json
{
  "$schema": "extraction-schema-v1",
  "source": "{source_url}",
  "description": "{what this dataset contains}",
  "fields": [
    {
      "name": "company_name",
      "type": "string",
      "required": true,
      "description": "Legal company name"
    },
    {
      "name": "website",
      "type": "url",
      "required": true,
      "description": "Company website URL"
    },
    {
      "name": "industry",
      "type": "string",
      "required": false,
      "description": "Primary industry category"
    },
    {
      "name": "employee_count",
      "type": "integer",
      "required": false,
      "description": "Approximate employee count"
    },
    {
      "name": "location",
      "type": "string",
      "required": false,
      "description": "Headquarters city, state/country"
    }
  ],
  "dedup_key": "website",
  "sort_by": "company_name",
  "filters": {
    "industry": "{filter_value}",
    "min_employees": 10
  }
}
```

Share this schema with the client for approval before extraction begins.

### Step 3: Data Extraction

Use the appropriate extraction method based on the source:

**Method A: API-Based Extraction (preferred)**

```bash
# If the source has a public API
curl -s "https://api.example.com/v1/companies?industry=saas&limit=50" \
  -H "Accept: application/json" | jq '.data[]' > raw-data.json
```

**Method B: HTML Scraping**

```bash
# Fetch the page
curl -sL "https://example.com/directory?page=1" -o page.html

# Parse with node script
node scripts/scraper.js --url "https://example.com/directory" --pages 5 --output raw-data.json
```

**Method C: Structured Data Extraction**

```bash
# Extract JSON-LD, microdata, or Open Graph from pages
node scripts/extract-structured.js --url "https://example.com" --format jsonld
```

**Pagination Handling:**

When the data spans multiple pages:

1. Identify the pagination pattern (page numbers, offset, cursor, next URL).
2. Calculate total pages needed: `ceil(target_records / records_per_page)`.
3. Add a 1-2 second delay between requests to respect server resources.
4. Handle pagination edge cases: empty pages, duplicate last-page entries.

```yaml
Pagination Config:
  Pattern: "{query_param | path | cursor | link_header}"
  Base URL: "{url}"
  Page Param: "page={n}"
  Records Per Page: 20
  Total Pages Needed: 3
  Delay Between Requests: 1500ms
  Stop Condition: "empty results OR target count reached"
```

### Step 4: Data Cleaning and Deduplication

Apply these cleaning steps to every dataset:

```yaml
Cleaning Pipeline:
  1. Remove Duplicates:
     - Deduplicate on primary key (e.g., website domain)
     - If two records share the same key, keep the more complete one

  2. Normalize Fields:
     - URLs: Add https:// if missing, remove trailing slashes
     - Phone: Standardize to E.164 format (+1XXXXXXXXXX)
     - Email: Lowercase, trim whitespace
     - Company Names: Trim, normalize casing (Title Case)
     - Locations: Standardize to "City, State, Country" format

  3. Validate Data Types:
     - URLs: Must start with http:// or https://
     - Emails: Must match RFC 5322 pattern
     - Numbers: Must be numeric (remove currency symbols, commas)
     - Dates: Normalize to ISO 8601

  4. Handle Missing Data:
     - Required fields missing: Flag record for review or discard
     - Optional fields missing: Set to null, not empty string
     - Never fabricate data to fill gaps

  5. Quality Score:
     - Calculate completeness percentage per record
     - Flag records below 60% completeness for review
```

### Step 5: Data Enrichment (Pro Tier)

For Pro tier, enrich the base dataset with additional data points:

```yaml
Enrichment Sources:
  Company Data:
    - Employee count from LinkedIn company page
    - Industry classification from website metadata
    - Tech stack from BuiltWith or Wappalyzer signals
    - Social media profiles from website footer links

  Contact Data:
    - Email pattern detection (first@, first.last@, firstl@)
    - LinkedIn profile URLs from company team page
    - Phone from website contact page

  Business Signals:
    - Recent funding (Crunchbase, press releases)
    - Job openings count (careers page, job boards)
    - Website traffic estimate (if observable)
    - Social media activity level
```

Mark all enriched fields with their source and confidence level:

```json
{
  "company_name": "Acme Corp",
  "website": "https://acme.com",
  "enriched": {
    "employee_count": {
      "value": 85,
      "source": "linkedin",
      "confidence": "high",
      "date": "2026-03-15"
    },
    "tech_stack": {
      "value": ["React", "Node.js", "AWS"],
      "source": "website_analysis",
      "confidence": "medium",
      "date": "2026-03-15"
    }
  }
}
```

### Step 6: Export and Delivery

Package the data in the requested format(s):

**CSV Output:**

```csv
company_name,website,industry,employee_count,location,email,phone,score
"Acme Corp","https://acme.com","SaaS",85,"Austin, TX","info@acme.com","+15550123",92
"Beta Inc","https://beta.io","Fintech",42,"New York, NY","hello@beta.io","+15550456",87
```

CSV rules:
- UTF-8 encoding with BOM for Excel compatibility.
- Quote all string fields.
- Use comma delimiter (not semicolon or tab).
- Header row required.
- No trailing commas.

**JSON Output:**

```json
{
  "metadata": {
    "source": "{source_url}",
    "extracted_at": "{ISO8601}",
    "total_records": 50,
    "schema_version": "1.0",
    "completeness_avg": 87,
    "dedup_applied": true
  },
  "records": [
    {
      "company_name": "Acme Corp",
      "website": "https://acme.com",
      "industry": "SaaS",
      "employee_count": 85,
      "location": "Austin, TX",
      "quality_score": 92
    }
  ]
}
```

## Quality Checklist

Before delivering, verify:

```
[ ] Record count matches the tier (50 / 200 / 500)
[ ] No duplicate records (verified on dedup key)
[ ] All required fields are populated
[ ] URLs are valid and accessible
[ ] Email addresses pass format validation
[ ] Phone numbers are in consistent format
[ ] No obviously stale data (defunct companies, dead links)
[ ] CSV opens correctly in Excel/Google Sheets
[ ] JSON is valid (passes a linter)
[ ] Completeness score average is above 75%
[ ] Enrichment sources are documented (Pro tier)
[ ] Extraction report includes methodology
[ ] No personally identifiable information beyond business context
[ ] Data is sorted according to schema definition
[ ] Character encoding is UTF-8 throughout
```

## Deliverable Format

Every data extraction delivery includes:

```
deliverables/
  data-{source}-{date}.csv              - Clean dataset in CSV
  data-{source}-{date}.json             - Clean dataset in JSON
  extraction-report.md                   - Methodology, stats, quality notes
```

### extraction-report.md Format

```markdown
# Data Extraction Report

**Source:** {source_url}
**Date:** {date}
**Tier:** {Basic|Standard|Pro}

## Summary
- Records Requested: {count}
- Records Delivered: {count}
- Completeness Average: {percent}%
- Duplicates Removed: {count}

## Schema
| Field | Type | Required | Population Rate |
|-------|------|----------|-----------------|
| company_name | string | yes | 100% |
| website | url | yes | 100% |
| industry | string | no | 85% |
| employee_count | integer | no | 72% |

## Methodology
- Sources used: {list}
- Pages scraped: {count}
- Extraction method: {API / HTML parsing / structured data}
- Deduplication key: {field}

## Data Quality Notes
- {Any issues encountered}
- {Fields with low population rates and why}
- {Recommendations for improving data quality}

## Ethical Compliance
- robots.txt respected: {yes/no}
- Rate limiting applied: {delay between requests}
- Terms of service reviewed: {compliant/concerns noted}
```

## Ethical Guidelines

These rules are non-negotiable:

1. **Respect robots.txt** - Check and honor robots.txt directives before scraping.
2. **Rate limiting** - Minimum 1 second delay between requests. Never DDoS a site.
3. **No authentication bypass** - Do not circumvent login walls, CAPTCHAs, or paywalls.
4. **No personal data** - Do not scrape personal social media profiles, home addresses, or private information.
5. **Business context only** - Collect only business-relevant data (company info, public business contacts).
6. **Terms of service** - Review the site's ToS. Flag concerns to the client if scraping may violate them.
7. **No resale of scraped data** - Data is for the client's internal use only unless otherwise cleared.
8. **Attribution** - Note the source of every data point in the extraction report.

## Quality Standards

- Every record must have all required fields populated.
- Completeness average must be 75% or higher.
- Zero duplicates in the delivered dataset.
- Data must be current -- no records older than 90 days unless historical data was requested.
- If the target record count cannot be met from the specified source, deliver what is available and explain the shortfall. Never pad with fabricated records.
- Pro tier enrichment must add at least 3 new data points per record on average.

## Example Commands

```bash
# Basic extraction from a single source
cashclaw scrape --url "https://directory.example.com/companies" --fields "name,website,industry" --limit 50 --output data.csv

# Standard multi-source extraction
cashclaw scrape --urls "source1.com/list,source2.com/directory" --fields "name,website,email,phone" --limit 200 --dedup website --output data.json

# Pro extraction with enrichment
cashclaw scrape --url "https://directory.example.com" --fields "name,website,industry,size" --limit 500 --enrich --output data.csv data.json

# Validate an existing dataset
cashclaw scrape validate --input data.csv --schema schema.json --report quality-report.md
```
