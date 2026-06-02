# Real-World API Configuration Examples

This file contains actual working configurations for common public APIs and patterns.

## Example 1: GitHub API (Paginated by Page Number)

### API Details
- **Endpoint:** `https://api.github.com/repos/{owner}/{repo}/commits`
- **Pagination:** Uses `page` parameter (not token)
- **Authentication:** Optional personal token
- **Date Field:** `commit.committer.date`
- **Record Count:** `X-RateLimit-Remaining` header

### Pipeline Configuration

**1. Web Activity URL:**
```
https://api.github.com/repos/microsoft/fabric/commits?since=@{variables('minDate')}&until=@{variables('maxDate')}&page=@{variables('pageNumber')}&per_page=100
```

**2. Initialize pageNumber instead of pageToken:**
```
Set pageNumber to 1
Increment it each iteration: @add(variables('pageNumber'), 1)
```

**3. Date Extraction:**
```
MinDate: @min(activity('Call Web API').output[*].commit.committer.date)
MaxDate: @max(activity('Call Web API').output[*].commit.committer.date)
```

**4. Stop Condition:**
```
@equals(length(activity('Call Web API').output), 0)
```
Stop loop when empty array returned.

**5. Authentication (Optional):**
```
Headers:
- Authorization: token @{variables('githubToken')}
- Accept: application/vnd.github.v3+json
```

---

## Example 2: Stripe API (Cursor-Based Pagination)

### API Details
- **Endpoint:** `https://api.stripe.com/v1/charges`
- **Pagination:** Cursor-based with `starting_after`
- **Authentication:** API key required
- **Date Field:** `created` (Unix timestamp)
- **Response Format:** Wrapped in `data` object

### Pipeline Configuration

**1. Web Activity URL:**
```
https://api.stripe.com/v1/charges?created[gte]=@{ticks(variables('minDate'))}&limit=100&starting_after=@{variables('cursorId')}
```

**2. Authentication (Required):**
```
Headers:
- Authorization: Bearer @{variables('stripeApiKey')}
- Content-Type: application/x-www-form-urlencoded
```

**3. Date Extraction:**
```
MinDate: @min(activity('Call Web API').output.data[*].created)
MaxDate: @max(activity('Call Web API').output.data[*].created)
```

**4. Cursor Extraction:**
```
Extract cursor: @activity('Call Web API').output.data[-1].id
```

**5. Stop Condition:**
```
@equals(activity('Call Web API').output.has_more, false)
```

---

## Example 3: Microsoft Graph API (ISO 8601 Dates, Delta Query)

### API Details
- **Endpoint:** `https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages`
- **Pagination:** `@odata.nextLink` (skip token)
- **Authentication:** OAuth 2.0 / MSI
- **Date Field:** `receivedDateTime`
- **Delta Query:** Available for changes

### Pipeline Configuration

**1. Web Activity URL:**
```
https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$filter=receivedDateTime ge @{variables('minDate')} and receivedDateTime le @{variables('maxDate')}&$top=100&$skiptoken=@{variables('skipToken')}
```

**2. Authentication (MSI):**
```
authentication: {
  type: "MSI",
  resource: "https://graph.microsoft.com"
}
```

**3. Date Extraction:**
```
MinDate: @min(activity('Call Web API').output.value[*].receivedDateTime)
MaxDate: @max(activity('Call Web API').output.value[*].receivedDateTime)
```

**4. Skip Token Extraction:**
```
@activity('Call Web API').output['@odata.nextLink']
(Extract the @skiptoken parameter from URL)
```

**5. Stop Condition:**
```
@empty(activity('Call Web API').output['@odata.nextLink'])
```

---

## Example 4: AWS CloudTrail API via REST (Limit/Offset)

### API Details
- **Endpoint:** `https://your-api-gateway.execute-api.region.amazonaws.com/stage/events`
- **Pagination:** Offset-based (not token)
- **Authentication:** API Key
- **Date Field:** `eventTime`
- **Response:** Wrapped in `events` object

### Pipeline Configuration

**1. Variables Setup:**
```
offset = 0
pageSize = 50
totalRecords = 0
hasMore = true
```

**2. Web Activity URL:**
```
https://your-api-gateway.execute-api.region.amazonaws.com/stage/events?startTime=@{variables('minDate')}&endTime=@{variables('maxDate')}&offset=@{variables('offset')}&limit=@{variables('pageSize')}
```

**3. Date Extraction:**
```
MinDate: @min(activity('Call Web API').output.events[*].eventTime)
MaxDate: @max(activity('Call Web API').output.events[*].eventTime)
```

**4. Offset Update:**
```
@add(variables('offset'), variables('pageSize'))
```

**5. Stop Condition:**
```
@less(length(activity('Call Web API').output.events), variables('pageSize'))
```

---

## Example 5: JSON API Standard (Meta & Links Object)

### API Details
- **Endpoint:** `https://api.example.com/articles`
- **Pagination:** Via `links.next` URL
- **Date Field:** `attributes.createdAt`
- **Format:** JSON:API specification

### Pipeline Configuration

**1. Web Activity URL:**
```
https://api.example.com/articles?filter[createdAt][gte]=@{variables('minDate')}&filter[createdAt][lte]=@{variables('maxDate')}&page[size]=100&page[number]=@{variables('pageNumber')}
```

**2. Date Extraction:**
```
MinDate: @min(activity('Call Web API').output.data[*].attributes.createdAt)
MaxDate: @max(activity('Call Web API').output.data[*].attributes.createdAt)
```

**3. Next Link Extraction:**
```
@activity('Call Web API').output.links.next
```

**4. Stop Condition:**
```
@empty(activity('Call Web API').output.links.next)
```

---

## Example 6: GraphQL API (Date Ranges with Cursors)

### API Details
- **Endpoint:** `https://api.example.com/graphql`
- **Method:** POST
- **Pagination:** Cursor-based with `hasNextPage`
- **Date Field:** `node.createdAt`

### Pipeline Configuration

**1. Web Activity:**
```
Method: POST
URL: https://api.example.com/graphql
```

**2. Body (GraphQL Query):**
```graphql
{
  search(first: 100, after: "@{variables('cursor')}", 
    query: "created:@{variables('minDate')}..@{variables('maxDate')}") {
    edges {
      node {
        id
        createdAt
        ... other fields
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**3. Date Extraction:**
```
MinDate: @min(activity('Call Web API').output.data.search.edges[*].node.createdAt)
MaxDate: @max(activity('Call Web API').output.data.search.edges[*].node.createdAt)
```

**4. Cursor Extraction:**
```
@activity('Call Web API').output.data.search.pageInfo.endCursor
```

**5. Stop Condition:**
```
@equals(activity('Call Web API').output.data.search.pageInfo.hasNextPage, false)
```

---

## Example 7: REST API with Time-Based Pagination

### API Details
- **Endpoint:** `https://events.example.com/logs`
- **Pagination:** By last record timestamp
- **Date Field:** `timestamp`
- **Batch Size:** 1000 records fixed

### Pipeline Configuration

**1. Track Last ID:**
```
Variables:
- lastTimestamp = @variables('minDate')
- lastRecordId = ""
```

**2. Web Activity URL:**
```
https://events.example.com/logs?since=@{variables('lastTimestamp')}&after_id=@{variables('lastRecordId')}&limit=1000
```

**3. Timestamp Update:**
```
@if(
  greater(length(activity('Call Web API').output.records), 0),
  activity('Call Web API').output.records[-1].timestamp,
  variables('lastTimestamp')
)
```

**4. Record ID Update:**
```
@if(
  greater(length(activity('Call Web API').output.records), 0),
  activity('Call Web API').output.records[-1].id,
  ''
)
```

**5. Stop Condition:**
```
@less(length(activity('Call Web API').output.records), 1000)
```

---

## Common Expression Patterns

### Extract nested date with fallback
```
@if(
  not(empty(activity('Call Web API').output.data[0].timestamp)),
  @min(activity('Call Web API').output.data[*].timestamp),
  @min(activity('Call Web API').output.data[*].createdAt)
)
```

### Handle both array and object response
```
@if(
  equals(typeof(activity('Call Web API').output.data), 'array'),
  length(activity('Call Web API').output.data),
  1
)
```

### Format dates for different APIs
```
# ISO 8601
@formatDateTime(variables('minDate'), 'yyyy-MM-ddTHH:mm:ssZ')

# Unix Timestamp (seconds)
@ticks(variables('minDate'))

# Custom format
@formatDateTime(variables('minDate'), 'yyyyMMdd-HHmmss')

# With timezone
@formatDateTime(variables('minDate'), 'o')
```

### Safe null/empty checks
```
@coalesce(activity('Call Web API').output.nextToken, '')

@if(
  empty(activity('Call Web API').output.pagination),
  false,
  activity('Call Web API').output.pagination.hasMore
)
```

---

## Debugging with Test Queries

### cURL for Testing
```bash
# Simple test
curl -H "Authorization: Bearer TOKEN" \
  "https://api.example.com/data?startDate=2026-05-01&endDate=2026-05-31"

# With verbose output
curl -v -H "Authorization: Bearer TOKEN" \
  "https://api.example.com/data?startDate=2026-05-01"

# Save response to file
curl -H "Authorization: Bearer TOKEN" \
  "https://api.example.com/data?startDate=2026-05-01" \
  > response.json
```

### PowerShell for Testing
```powershell
$headers = @{
  Authorization = "Bearer $token"
  "Content-Type" = "application/json"
}

$response = Invoke-WebRequest `
  -Uri "https://api.example.com/data?startDate=2026-05-01" `
  -Headers $headers

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Python for Testing
```python
import requests
import json

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://api.example.com/data?startDate=2026-05-01',
    headers=headers
)

data = response.json()
print(json.dumps(data, indent=2))
```

---

## Quick Reference: Choose Your Pattern

| Pattern | Use When | Example |
|---------|----------|---------|
| **Page Number** | Page param increments | GitHub, REST APIs |
| **Cursor/Token** | Opaque token in response | Stripe, Twitter, Facebook |
| **Offset/Limit** | Skip N records | AWS, Elasticsearch |
| **Next URL** | API provides full next URL | JSON:API, OData |
| **Time-based** | Timestamp indicates position | Event streams, logs |
| **No Pagination** | Single page only | Simple REST APIs |

---

For more details on customizing for your specific API, refer to **WebAPI-Pipeline-Guide.md**
