# Fabric Web API Date Range Pipeline - Complete Solution

## 📋 Overview

This solution provides a **production-ready Fabric pipeline** that:
- Calls a web API with date range parameters
- Extracts min/max dates from responses  
- Handles pagination (tokens, cursors, offsets)
- Loops until all data is received
- Saves responses to Lakehouse

Perfect for syncing data from SaaS APIs, REST endpoints, or any paginated data source into Microsoft Fabric.

---

## 📦 What's Included

### Core Files

| File | Purpose | For Whom |
|------|---------|----------|
| **WebAPI-DateRange-Pipeline.json** | Complete, runnable pipeline definition | Fabric developers, DevOps engineers |
| **QUICKSTART.md** | Get up and running in 5 minutes | Quick start users |
| **WebAPI-Pipeline-Guide.md** | Comprehensive reference documentation | Detailed implementation guidance |
| **EXAMPLES.md** | Real-world API configurations | API-specific customization |

### Tools & Scripts

| File | Purpose | For Whom |
|------|---------|----------|
| **test_web_api.py** | Validate API response structure before deploying | Data engineers, Python users |
| **Deploy-WebAPI-Pipeline.ps1** | Automated deployment to Fabric | PowerShell users, automation specialists |
| **INDEX.md** | This file - navigation guide | Everyone starting out |

---

## 🚀 Quick Navigation

### "I want to get started immediately"
→ Read [QUICKSTART.md](QUICKSTART.md) (5 min)

### "I need detailed step-by-step instructions"
→ Read [WebAPI-Pipeline-Guide.md](WebAPI-Pipeline-Guide.md) (15 min)

### "I need to integrate with a specific API"
→ Search [EXAMPLES.md](EXAMPLES.md) for your API type

### "I want to test my API first"
→ Run `python test_web_api.py` in the terminal

### "I want to automate deployment"
→ Use `Deploy-WebAPI-Pipeline.ps1` with your workspace

---

## 🎯 Use Cases

### ✅ This Solution Works Best For:
- **SaaS Data Sync:** Salesforce, HubSpot, Stripe, etc.
- **REST APIs:** Any paginated REST endpoint
- **Time-Series Data:** Event logs, metrics, transactions
- **Incremental Loads:** Process data by date ranges
- **Scheduled Updates:** Daily/hourly data refreshes

### ⚠️ When to Consider Alternatives:
- **Real-time streaming** → Use Fabric Streaming Endpoints
- **Batch file imports** → Use Fabric Data Factory Copy activity
- **Direct database connections** → Use Warehouse shortcuts

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FABRIC PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Start] → [Init Variables] → [Set Date Range]             │
│                                     ↓                       │
│          ┌──────────────────[LOOP UNTIL]────────────────┐   │
│          │                                              │   │
│          ├→ [Call Web API] ─→ [Parse Response]        │   │
│          │                        ↓                    │   │
│          ├→ [Extract Min Date]    │                    │   │
│          │                        ↓                    │   │
│          ├→ [Extract Max Date]    │                    │   │
│          │                        ↓                    │   │
│          ├→ [Extract Page Token]  │                    │   │
│          │                        ↓                    │   │
│          ├→ [Save to Lakehouse]   │                    │   │
│          │                        ↓                    │   │
│          └→ [Check: More Data?]──┘                    │   │
│                    ↓                                   │   │
│              [Continue/Stop]                          │   │
│                                                        │   │
└────────────────────────────────────────────────────────────┘
                          ↓
                  [Log Completion]
```

---

## 🔧 Implementation Path

### Phase 1: Preparation (15 min)
```
1. Review QUICKSTART.md
2. Test your API: python test_web_api.py
3. Verify API response structure
4. Identify date fields and pagination method
```

### Phase 2: Configuration (30 min)
```
1. Create pipeline in Fabric
2. Paste WebAPI-DateRange-Pipeline.json
3. Update API endpoint URL
4. Map date extraction fields
5. Configure pagination logic
6. Set up Lakehouse sink
```

### Phase 3: Testing (15 min)
```
1. Run pipeline with 1 day of data
2. Verify records saved to Lakehouse
3. Check min/max dates extracted correctly
4. Inspect for any errors in Activity log
```

### Phase 4: Production (ongoing)
```
1. Extend date range gradually
2. Schedule for automated runs
3. Monitor for failures
4. Optimize date window size
```

---

## 📖 Key Concepts

### Date Range Processing
Pipeline processes data in time windows:
```
Iteration 1: Jan 1-7  → Extract dates → Save 500 records → Get next page token
Iteration 2: Jan 1-7  → Extract dates → Save 300 records → Get next page token  
Iteration 3: Jan 1-7  → Extract dates → No more pages    → Move to next date range
...
Pipeline stops when no more data for entire date range
```

### Min/Max Date Extraction
Tracks processed data to avoid gaps:
```json
Response 1: Records dated Jan 1-5   → minDate=Jan 1, maxDate=Jan 5
Response 2: Records dated Jan 4-7   → minDate=Jan 4, maxDate=Jan 7
Response 3: Records dated Jan 6-10  → minDate=Jan 6, maxDate=Jan 10
```

### Pagination Handling
Continues fetching until API signals "no more data":
```
API returns: { data: [...], nextPageToken: "abc123" } → Continue
API returns: { data: [...], nextPageToken: "" }       → Continue with next date
API returns: { data: [] }                             → No more records in date range
```

---

## 🛠️ Customization Checklist

### For Your API, You'll Need to Update:

- [ ] **API Endpoint URL** in Web Activity
- [ ] **Date Field Name** in Extract Min/Max Date activities
  - If not `createdDate`, use your field name
- [ ] **Pagination Field** in Extract Next Page Token activity
  - If not `nextPageToken`, use your API's pagination field
- [ ] **Authentication** method and credentials
  - API key, OAuth, MSI, or Basic auth
- [ ] **Lakehouse Configuration** for data sink
  - Target table name and schema
- [ ] **Headers** if API requires special headers
  - Accept type, User-Agent, custom headers

See [WebAPI-Pipeline-Guide.md](WebAPI-Pipeline-Guide.md) for details on each.

---

## 🔍 File Dependencies

```
QUICKSTART.md
    ├─→ WebAPI-DateRange-Pipeline.json (copy and use)
    ├─→ WebAPI-Pipeline-Guide.md (refer for details)
    └─→ test_web_api.py (validate your API)

EXAMPLES.md
    ├─→ Real configurations for GitHub, Stripe, Graph, AWS, etc.
    └─→ Debugging patterns

Deploy-WebAPI-Pipeline.ps1
    └─→ Automates creating pipeline from JSON

WebAPI-Pipeline-Guide.md
    ├─→ Deep dive on each activity
    ├─→ Expression language reference
    ├─→ Common error solutions
    └─→ Performance optimization tips
```

---

## ⚡ Performance Tips

### Optimization for Large Datasets

| Setting | Default | Optimize For |
|---------|---------|--------------|
| Date Window | 7 days | Increase to 30 days if stable |
| Page Size | 100 | Use max your API allows |
| Retry Count | 2 | Increase for unstable APIs |
| Timeout | 7 hours | Adjust based on data volume |
| Parallel Runs | Single | Run multiple for different date ranges |

### Example: Processing 1 Year of Data
```
Option 1 (Sequential):  
- 52 iterations × 5 min each = 260 minutes total

Option 2 (Parallel):
- 4 pipelines × 13 weeks each = 65 minutes total
- Split date range: Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec
```

---

## 📝 Common Questions

### Q: How do I handle APIs with different pagination methods?
**A:** See [EXAMPLES.md](EXAMPLES.md) - covers page numbers, cursors, tokens, offsets, and more.

### Q: What if my API doesn't support date filtering?
**A:** Modify to use limit/offset pagination instead. See EXAMPLES.md for offset pattern.

### Q: Can I process multiple date ranges in parallel?
**A:** Yes! Create multiple pipeline instances or use parent pipeline to spawn child pipelines.

### Q: How do I authenticate with the API?
**A:** Use Web Activity authentication options (MSI, Basic, API key in headers). See WebAPI-Pipeline-Guide.md.

### Q: What format should dates be in?
**A:** Use ISO 8601 format: `2026-05-01T00:00:00Z`. Adjust in URL formatting if needed.

### Q: How do I save responses in different formats?
**A:** Modify Copy Activity sink - supports Parquet, Delta, CSV, JSON. Default is Parquet.

---

## 🐛 Troubleshooting Quick Reference

| Problem | Most Likely Cause | Solution |
|---------|------------------|----------|
| Pipeline runs but no data | API returns empty | Check date range, verify endpoint |
| Loop never stops | Wrong stop condition | Update "Check for More Data" expression |
| Dates not extracting | Wrong field name | Inspect API response, update path |
| Auth fails | Bad credentials | Verify key/token in variables |
| Data not saving | Lakehouse issue | Check table exists, verify schema |

See [WebAPI-Pipeline-Guide.md](WebAPI-Pipeline-Guide.md) **Debugging Tips** section for detailed solutions.

---

## 📚 Learning Resources

### In This Package
- **Technical Deep Dive:** [WebAPI-Pipeline-Guide.md](WebAPI-Pipeline-Guide.md)
- **API Examples:** [EXAMPLES.md](EXAMPLES.md)
- **Quick Setup:** [QUICKSTART.md](QUICKSTART.md)
- **Testing Tool:** `test_web_api.py`

### External Resources
- Microsoft Fabric Documentation: https://learn.microsoft.com/fabric
- Pipeline Activities Reference: https://learn.microsoft.com/en-us/fabric/data-factory/pipeline-activities
- Azure Data Factory Expression Language: https://learn.microsoft.com/en-us/azure/data-factory/control-flow-expression-language-functions

---

## 🎓 Training Videos (Suggested Topics)

1. Creating Your First Fabric Pipeline (5 min)
2. Understanding Variables and Expressions (10 min)
3. REST API Integration Patterns (15 min)
4. Date Range Processing Strategies (10 min)
5. Debugging Failed Pipeline Runs (8 min)

---

## 📋 Deployment Checklist

Before going to production:

- [ ] Tested with your actual API endpoint
- [ ] Verified date extraction works correctly
- [ ] Confirmed pagination handles full data set
- [ ] Data persists correctly to Lakehouse
- [ ] Error handling verified (retry, timeouts)
- [ ] Authentication credentials secured in Key Vault
- [ ] Monitoring and alerts configured
- [ ] Disaster recovery plan documented
- [ ] Documented for team handoff

---

## 🤝 Contributing & Feedback

Found an issue or improvement? Consider:
1. Testing with the provided `test_web_api.py`
2. Checking [EXAMPLES.md](EXAMPLES.md) for similar patterns
3. Reviewing [WebAPI-Pipeline-Guide.md](WebAPI-Pipeline-Guide.md) troubleshooting section

---

## 📄 File Manifest

```
c:\code\fabriciq\
├── INDEX.md                           ← You are here
├── QUICKSTART.md                      ← Start here (5 min)
├── WebAPI-Pipeline-Guide.md           ← Full reference (15 min)
├── EXAMPLES.md                        ← Real API configs
├── WebAPI-DateRange-Pipeline.json     ← The actual pipeline
├── test_web_api.py                    ← API validation tool
└── Deploy-WebAPI-Pipeline.ps1         ← Deployment automation
```

---

## 🏁 Getting Started Now

### Absolute Quickest Start:
```
1. Open QUICKSTART.md
2. Run: python test_web_api.py --help
3. Create new pipeline in Fabric UI
4. Paste WebAPI-DateRange-Pipeline.json
5. Update API endpoint
6. Run
```

### Recommended Full Setup:
```
1. Read QUICKSTART.md (5 min)
2. Review WebAPI-Pipeline-Guide.md (15 min)
3. Find your API in EXAMPLES.md (5 min)
4. Test: python test_web_api.py (5 min)
5. Create pipeline in Fabric (10 min)
6. Configure for your API (10 min)
7. Test run (5 min)
Total: ~55 minutes
```

---

**Ready to build?** Start with [QUICKSTART.md](QUICKSTART.md)

**Questions?** Check [WebAPI-Pipeline-Guide.md](WebAPI-Pipeline-Guide.md) or [EXAMPLES.md](EXAMPLES.md)

**Integrating specific API?** Search [EXAMPLES.md](EXAMPLES.md) for your API type
