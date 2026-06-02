# Fabric Pipeline: Web API Date Range Processor

## Overview

This pipeline demonstrates how to:
1. **Call a Web API** repeatedly with date range parameters
2. **Extract min/max dates** from responses to track processed data
3. **Handle pagination** using page tokens
4. **Loop until completion** when no more data is available
5. **Save responses** to a Lakehouse for persistence

## Architecture

```
Initialize Variables
    ↓
Set Date Variables (min, max, page token)
    ↓
Until Loop (continues while continueLoop = true)
    ├─ Call Web API with date range
    ├─ Parse Response
    ├─ Extract Min/Max dates from data
    ├─ Extract Next Page Token
    ├─ Save Response to Lakehouse
    └─ Check if more data exists
    ↓
Log Completion
```

## Pipeline Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `startDate` | String | Initial date to start fetching from (default: 30 days ago) |
| `minDate` | String | Minimum date found in current API response |
| `maxDate` | String | Maximum date found in current API response |
| `pageToken` | String | Token for pagination, fetched from API response |
| `continueLoop` | Boolean | Flag to control loop execution |
| `apiResponse` | Object | Parsed API response data |
| `apiToken` | String | Authentication token for API calls |

## Key Activities Explained

### 1. **Call Web API** (WebActivity)
```
URL: https://api.example.com/data?startDate={minDate}&endDate={maxDate}&pageToken={pageToken}
Method: GET
Headers: Authorization Bearer token
```

**Customization:**
- Replace `https://api.example.com/data` with your actual API endpoint
- Adjust query parameters to match your API's requirements
- Update authentication method (MSI, Basic, OAuth2, etc.)

### 2. **Check Response** (IfActivity)
Validates that the API returned data:
```
Expression: @not(empty(activity('Call Web API').output))
```

**If True:** Process the response and extract dates  
**If False:** Stop the loop (no more data)

### 3. **Extract Min/Max Dates** (SetVariable Activities)
```
MinDate: @min(activity('Call Web API').output.data[*].createdDate)
MaxDate: @max(activity('Call Web API').output.data[*].createdDate)
```

**Customization:**
- Replace `data[*].createdDate` with your JSON path to dates
- For nested properties: `data[*].metadata.timestamp`
- Handle multiple date fields as needed

### 4. **Extract Next Page Token** (SetVariable)
```
Expression: @activity('Call Web API').output.nextPageToken
```

**Customization:**
- Update to match your API's pagination field name
- Examples: `pagination.nextToken`, `links.next`, `hasMore`

### 5. **Save Response to Lakehouse** (CopyActivity)
Persists API response data to Lakehouse in Parquet format

**Customization:**
- Change format (Parquet, Delta, CSV, etc.)
- Update sink settings to target your Lakehouse
- Add transformations as needed

### 6. **Check for More Data** (IfActivity)
```
Expression: @empty(variables('pageToken'))
```

**Logic:**
- If page token is empty: Stop loop (no more pages)
- If page token exists: Continue loop (more data available)

## How to Customize for Your API

### Step 1: Understand Your API Response
```json
{
  "data": [
    {
      "id": "123",
      "createdDate": "2026-05-15T10:30:00Z",
      "value": 100
    }
  ],
  "nextPageToken": "eyJvZmZzZXQiOiAxMDB9",
  "hasMore": true
}
```

### Step 2: Update Date Extraction
If your API uses different field names:

**Original:**
```
@min(activity('Call Web API').output.data[*].createdDate)
```

**Custom (e.g., "timestamp"):**
```
@min(activity('Call Web API').output.data[*].timestamp)
```

**Custom (e.g., nested "metadata.date"):**
```
@min(activity('Call Web API').output.data[*].metadata.date)
```

### Step 3: Update Pagination Logic
If your API doesn't use tokens but has `limit/offset`:

Replace page token logic with offset tracking:

```
Set Offset Variable:
@add(variables('currentOffset'), length(activity('Call Web API').output.data))

Check for More Data:
@less(length(activity('Call Web API').output.data), variables('pageSize'))
```

### Step 4: Update API URL
```
Original:
https://api.example.com/data?startDate={minDate}&endDate={maxDate}&pageToken={pageToken}

Custom Example (Limit/Offset):
https://api.example.com/data?startDate={minDate}&endDate={maxDate}&limit=100&offset={offset}

Custom Example (ISO Dates):
https://api.example.com/records?from={minDate}&to={maxDate}&token={pageToken}
```

### Step 5: Handle Authentication
Update the authentication section in "Call Web API":

**Option A: MSI (Managed Identity)**
```json
"authentication": {
  "type": "MSI",
  "resource": "https://your-api.com"
}
```

**Option B: Basic Auth**
```json
"authentication": {
  "type": "Basic",
  "username": "@variables('apiUsername')",
  "password": "@variables('apiPassword')"
}
```

**Option C: API Key in Header**
```json
"headers": {
  "X-API-Key": "@variables('apiKey')",
  "Content-Type": "application/json"
}
```

## Implementation Steps in Fabric

1. **Create the Pipeline:**
   - In Fabric workspace, create new Pipeline
   - Switch to JSON editor
   - Paste the pipeline JSON
   - Save and rename appropriately

2. **Configure Parameters:**
   - Set `apiEndpoint` parameter (or hardcode URL)
   - Set `lakehouseTarget` parameter
   - Create Lakehouse table for storing API responses

3. **Add Linked Services:**
   - If using external API, create Web service connection
   - Configure authentication credentials

4. **Test with Sample API:**
   - Use public API (e.g., JSONPlaceholder, OpenWeather)
   - Verify date extraction logic
   - Confirm pagination works correctly

5. **Monitor Execution:**
   - Check pipeline runs for success/failures
   - Verify data is being saved to Lakehouse
   - Monitor date ranges to ensure no gaps

## Debugging Tips

### Issue: Loop never exits
- **Cause:** Page token not emptying or continueLoop not set to false
- **Fix:** Check API response field name for pagination token
- **Check:** Add logging activity to inspect token values

### Issue: Dates not being extracted
- **Cause:** JSON path incorrect or date field missing
- **Fix:** Inspect raw API response using Developer Tools
- **Check:** Verify field name matches exactly (case-sensitive)

### Issue: Data not saving to Lakehouse
- **Cause:** Incorrect sink configuration or permissions
- **Fix:** Verify Lakehouse connection and table structure
- **Check:** Ensure user has write permissions

## Example: Real Implementation with GitHub API

```
Endpoint: https://api.github.com/repos/microsoft/fabric/commits
Query Params: 
  - since={minDate} (RFC 3339 format)
  - until={maxDate}
  - page={pageNumber}
  - per_page=100

Date Field: commit.committer.date
Pagination: Link header or use page parameter directly
```

## Performance Optimization

1. **Batch Processing:**
   - Increase page size if API allows
   - Adjust date range window (hourly vs. daily)

2. **Parallel Streams:**
   - Split date range into multiple parallel pipeline runs
   - Each handles different time period

3. **Error Handling:**
   - Add retry logic with exponential backoff
   - Log failed requests for manual retry

4. **Caching:**
   - Store last processed date in metadata table
   - Resume from last known point on re-run

## Testing Checklist

- [ ] Web API successfully responds with test data
- [ ] Date extraction works for all records
- [ ] Page token correctly identifies pagination
- [ ] Loop terminates when no more data
- [ ] Responses saved correctly to Lakehouse
- [ ] Timestamps tracked for audit/replay
- [ ] Authentication tokens not exposed in logs
- [ ] Pipeline handles API errors gracefully

