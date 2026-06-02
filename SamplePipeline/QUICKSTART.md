# Quick Start: Web API Date Range Pipeline for Fabric

## What You Get

A complete Fabric pipeline solution that:
- ✅ Calls a web API repeatedly with date range parameters  
- ✅ Automatically extracts min/max dates from each response
- ✅ Handles pagination using page tokens
- ✅ Stops automatically when no more data is available
- ✅ Saves all responses to a Lakehouse
- ✅ Tracks progress with variables and logging

## Files Included

| File | Purpose |
|------|---------|
| `WebAPI-DateRange-Pipeline.json` | Complete pipeline definition (JSON) |
| `WebAPI-Pipeline-Guide.md` | Detailed documentation & customization guide |
| `Deploy-WebAPI-Pipeline.ps1` | PowerShell script to deploy to Fabric |
| `test_web_api.py` | Python tool to test your API before deploying |
| `QUICKSTART.md` | This file |

## 5-Minute Setup

### Step 1: Test Your API
```bash
python test_web_api.py
```

This validates that your API returns data in a format the pipeline can process.

### Step 2: Create the Pipeline in Fabric

**Option A: Using PowerShell**
```powershell
.\Deploy-WebAPI-Pipeline.ps1 `
  -WorkspaceName "YourWorkspace" `
  -PipelineName "MyAPISync" `
  -ApiEndpoint "https://api.example.com/data"
```

**Option B: Manual in Fabric UI**
1. In your Fabric workspace, create a new **Pipeline**
2. Switch to **Editor** view
3. Open **{}** (JSON editor)
4. Copy-paste contents of `WebAPI-DateRange-Pipeline.json`
5. Update the API endpoint URL in the Web Activity
6. Save and publish

### Step 3: Configure the Pipeline

In Fabric pipeline editor, customize:

**URL for Web API call:**
```
https://your-api.com/data?startDate={minDate}&endDate={maxDate}&pageToken={pageToken}
```

**Date extraction (if not using 'createdDate'):**
In "Extract Min Date" activity, change:
```
@min(activity('Call Web API').output.data[*].createdDate)
```
To your actual date field:
```
@min(activity('Call Web API').output.data[*].YOUR_DATE_FIELD)
```

**Pagination check (if not using 'nextPageToken'):**
In "Extract Next Page Token" activity, change:
```
@activity('Call Web API').output.nextPageToken
```
To your API's pagination field.

### Step 4: Run the Pipeline

1. Click **Run** in Fabric
2. Monitor execution in the **Activity** pane
3. Check **Lakehouse** for saved data

## Common API Patterns

### Pattern 1: Page Token Pagination
```json
{
  "data": [...],
  "nextPageToken": "abc123"  // Empty when done
}
```
✅ **Works as-is** - Pipeline automatically detects

### Pattern 2: Offset/Limit Pagination
```json
{
  "data": [...],
  "offset": 100,
  "limit": 100
}
```
🔧 **Needs customization:**
- Replace page token logic with offset tracking
- Set `continueLoop = false` when `length(data) < limit`

### Pattern 3: Link Header Pagination
```
Link: <https://api.example.com/data?page=2>; rel="next"
```
🔧 **Needs customization:**
- Extract from Response Headers instead of JSON body
- Parse Link header for next URL

### Pattern 4: Has More Flag
```json
{
  "data": [...],
  "hasMore": false
}
```
🔧 **Needs customization:**
- Set `continueLoop = hasMore` instead of checking token

## Date Field Mapping

### If your API uses...

**Nested dates:**
```
data[0].metadata.timestamp
```
Change to:
```
@min(activity('Call Web API').output.data[*].metadata.timestamp)
```

**Different field names:**
```
data[0].processedAt
data[0].updated_date
data[0].ingestionDate
```
Just update the field name in the expression.

**Multiple date fields:**
```
@min(
  union(
    activity('Call Web API').output.data[*].createdDate,
    activity('Call Web API').output.data[*].updatedDate
  )
)
```

## Authentication

### API Key in Headers
```json
"headers": {
  "X-API-Key": "@variables('apiKey')",
  "Authorization": "Bearer @{variables('apiToken')}"
}
```

### Basic Auth
```json
"authentication": {
  "type": "Basic",
  "username": "user@example.com",
  "password": "@variables('apiPassword')"
}
```

### OAuth/MSI
```json
"authentication": {
  "type": "MSI",
  "resource": "https://your-api.com"
}
```

## Troubleshooting

### Pipeline runs but stops immediately
**Cause:** Empty API response on first call  
**Fix:** 
- Check API endpoint URL
- Verify date range parameters
- Test endpoint with Postman/curl

### Dates not extracting
**Cause:** Wrong field name or nested structure  
**Fix:**
- Look at raw API response in Activity output
- Update date extraction expression
- Use the Python test script to inspect response

### Loop keeps running (doesn't stop)
**Cause:** Page token not clearing or wrong pagination field  
**Fix:**
- Check what API returns for "end of data"
- Update "Check for More Data" expression
- Add logging to see token values

### Data not saving to Lakehouse
**Cause:** Wrong sink configuration or permissions  
**Fix:**
- Create Lakehouse table first
- Verify schema matches API response
- Check user has write permissions

## Performance Tips

1. **Adjust date window:** Change `adddays(utcnow(), -30)` to different range
2. **Parallel processing:** Run multiple pipelines with different date ranges
3. **Batch size:** Ask API if you can increase records per page
4. **Retry logic:** Set retry count for network resilience
5. **Scheduling:** Use scheduled runs instead of manual testing

## Monitoring

Check pipeline execution:
- **Runs pane** → See all executions and status
- **Duration** → Monitor how long API calls take
- **Failed runs** → Debug errors in activity outputs
- **Data volume** → Track records processed per run

## Example: Real API

### GitHub Commits API
```
URL: https://api.github.com/repos/{owner}/{repo}/commits
Date Field: commit.committer.date
Page Token: page parameter
Auth: Optional token in headers
```

Configure as:
```
URL: https://api.github.com/repos/microsoft/fabric/commits
  ?since={minDate}&until={maxDate}&page={pageNumber}&per_page=100
```

### JSONPlaceholder (Free Test API)
```
URL: https://jsonplaceholder.typicode.com/posts
```

## Next Steps

1. **Customize for your API** (see WebAPI-Pipeline-Guide.md)
2. **Test with test_web_api.py** before running pipeline
3. **Start with small date range** for testing
4. **Monitor first few runs** to ensure data is correct
5. **Schedule for production** once validated

## Support

For more details, see:
- `WebAPI-Pipeline-Guide.md` - Complete documentation
- `test_web_api.py` - Python validation tool
- `Deploy-WebAPI-Pipeline.ps1` - PowerShell deployment

## Video: Typical Configuration Flow

```
1. Copy pipeline JSON to Fabric
2. Set API endpoint URL
3. Map date fields to your API
4. Update pagination logic
5. Configure Lakehouse sink
6. Run test execution
7. Monitor and debug
8. Schedule for automation
```

---

**Ready to go?** Start with Step 1 above or refer to WebAPI-Pipeline-Guide.md for detailed customization.
