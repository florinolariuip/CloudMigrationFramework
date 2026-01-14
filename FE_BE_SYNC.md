# Frontend-Backend Synchronization Summary

## Date: January 2026

This document describes the synchronization between the frontend (cmov4.html) and backend (Flask API) for the Cloud Migration Optimizer v4, documenting API contracts and data flow for reproducibility.

---

## API Endpoints

### 1. `/api/benchmark` (GET) - Preset Scenarios
**Frontend Request:**
```javascript
GET /api/benchmark?scenario=0&requests_per_month=1000000&cross_az_gb=100&internet_egress_gb=500&ebs_gb=1000&rds_backup_gb=200&s3_gb=5000
```

**Backend Processing:**
- Accepts `scenario` index (0, 1, or 2)
- Extracts usage_profile parameters from query string:
  - `requests_per_month` (int)
  - `cross_az_gb` (float)
  - `internet_egress_gb` (float)
  - `ebs_gb` (float)
  - `rds_backup_gb` (float)
  - `s3_gb` (float)
- Adds usage_profile to the scenario dict
- Runs benchmark and returns v3 and v4 results

**Backend Response:**
```json
{
  "v3": { /* CMOv3 baseline results */ },
  "v4": { /* CMOv4 optimized results */ },
  "scenario": { /* Original scenario data */ }
}
```

---

### 2. `/api/benchmark/dynamic` (POST) - Custom Scenarios
**Frontend Request:**
```javascript
POST /api/benchmark/dynamic
Content-Type: application/json

{
  "scenario": {
    "architecture": {
      "architecture_pattern": "microservices",
      "components": [
        {
          "name": "Component1",
          "type": "web",
          "instance_count": 1,
          "tech_stack": { "framework": "React" },
          "dependencies": []
        }
        // ... more components
      ],
      "relationships": [],
      "multi_tenancy": false
    },
    "constraints": {
      "maxBudget": 10000,
      "maxLatency": 150,
      "requiredProviders": ["AWS", "Azure", "GCP"],
      "securityLevel": "medium"
    },
    "pricing": {},
    "usage_profile": {
      "requests_per_month": 1000000,
      "cross_az_gb": 100,
      "internet_egress_gb": 500,
      "ebs_gb": 1000,
      "rds_backup_gb": 200,
      "s3_gb": 5000
    }
  }
}
```

**Backend Processing:**
- Extracts scenario from POST body
- Validates scenario structure
- Extracts usage_profile from scenario
- Adds usage_profile to constraints dict
- Runs single benchmark and returns v3 and v4 results

**Backend Response:**
```json
{
  "v3": { /* CMOv3 baseline results */ },
  "v4": { /* CMOv4 optimized results */ },
  "scenario": { /* Original scenario data */ }
}
```

---

## Data Flow

### Preset Scenarios Flow:
1. **Frontend** → User selects scenario and adjusts workload parameters
2. **Frontend** → Sends GET request with query parameters
3. **Backend** (`app.py`) → Extracts parameters and builds usage_profile dict
4. **Backend** (`benchmark.py`) → Adds usage_profile to scenario
5. **Backend** (`optimizer.py`) → Converts usage_profile dict to UsageProfile object
6. **Backend** (`pricing.py`) → Uses UsageProfile for cost calculations
7. **Backend** → Returns results to frontend
8. **Frontend** → Displays results

### Custom Scenarios Flow:
1. **Frontend** → User builds custom scenario (pattern, components, providers, workload)
2. **Frontend** → Constructs full scenario object with proper component structure
3. **Frontend** → Sends POST request with JSON body
4. **Backend** (`app.py`) → Extracts scenario from request
5. **Backend** (`benchmark.py`) → Passes usage_profile to optimizer
6. **Backend** (`optimizer.py`) → Converts usage_profile dict to UsageProfile object
7. **Backend** (`pricing.py`) → Uses UsageProfile for cost calculations
8. **Backend** → Returns results to frontend
9. **Frontend** → Displays results

---

## Component Structure Mapping

### Frontend Component Types (15 total):
1. `web` → Web Frontend
2. `compute` → Application Server
3. `database` → Database
4. `cache` → Cache
5. `monitoring` → Monitoring
6. `message_queue` → Message Queue
7. `storage` → Object Storage
8. `load_balancer` → Load Balancer
9. `backup` → Backup
10. `security` → Security / Secrets
11. `cdn` → CDN
12. `analytics` → Analytics
13. `encryption` → Encryption / KMS
14. `container` → Container Runtime
15. `serverless` → Serverless / Lambda

### Backend Component Requirements:
Each component must have:
- `name` (string): Unique component name
- `type` (string): Component type from list above
- `instance_count` (int): Number of instances
- `tech_stack` (dict): Technology details (varies by type)
- `dependencies` (list): List of component dependencies

---

## Usage Profile Integration

### Frontend State:
```javascript
const [requestsPerMonth, setRequestsPerMonth] = useState('1000000');
const [crossAzGb, setCrossAzGb] = useState('100');
const [internetEgressGb, setInternetEgressGb] = useState('500');
const [ebsGb, setEbsGb] = useState('1000');
const [rdsBackupGb, setRdsBackupGb] = useState('200');
const [s3Gb, setS3Gb] = useState('5000');
```

### Backend Model:
```python
@dataclass
class UsageProfile:
    requests_per_month: int = 10000000
    cross_az_gb: int = 500
    internet_egress_gb: int = 1000
    ebs_gb: int = 100
    rds_backup_gb: int = 150
    s3_gb: int = 500
```

### Conversion Points:
1. **Frontend → API**: Converts strings to numbers in JavaScript
2. **Backend → Model**: Converts dict to UsageProfile dataclass using `**dict` unpacking
3. **Cost Calculation**: UsageProfile object passed to `calculate_total_cost()`

---

## Key Synchronization Points ✅

1. ✅ **Field Names**: All usage_profile fields use snake_case consistently
2. ✅ **Component Structure**: Frontend builds complete component objects with all required fields
3. ✅ **Architecture Pattern**: Uses `architecture_pattern` key (not `pattern`)
4. ✅ **Provider Format**: Both use arrays of provider names (AWS, Azure, GCP)
5. ✅ **Data Types**: Frontend converts strings to numbers before sending
6. ✅ **Error Handling**: Both frontend and backend handle missing/invalid data gracefully

---

## Testing Checklist

- [x] Preset scenario with default workload parameters
- [x] Preset scenario with custom workload parameters
- [x] Custom scenario with all 15 component types
- [x] Custom scenario with workload parameters
- [x] Backend properly converts usage_profile dict to UsageProfile object
- [x] Cost calculations use workload parameters correctly

---

## Notes

- The backend now properly extracts usage_profile from both GET query parameters (preset) and POST JSON body (custom)
- The optimizer converts the usage_profile dict to a UsageProfile dataclass object for type safety
- All cost calculations use the UsageProfile object for dynamic pricing
- Frontend builds complete component objects with proper tech_stack mappings
