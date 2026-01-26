# Workload-Based Pricing Implementation

**Added:** December 2025  
**Last Updated:** January 2026  
**Status:** Production Ready (CMOv3 & CMOv4)

## Overview

The optimizer supports **workload-based pricing** in addition to regional base
service prices. Instead of assuming a flat monthly cost per SKU, the backend
combines:

1. **Base service prices** from `ServiceDataCache` (per VM / DB / storage SKU)  
2. **Usage-driven adjustments** based on a `UsageProfile` (requests, data
   transfer, storage volumes)

This yields more realistic monthly cost estimates, especially for
high-traffic, data-intensive workloads.

For a detailed discussion of data sources and caching, see
`backend/PRICING_METHODOLOGY.md`. This document focuses specifically on how the
**workload** dimension is modeled and integrated.

---

## Backend Implementation

### 1. UsageProfile dataclass

**File:** `backend/models.py` (or equivalent models module)

```python
@dataclass
class UsageProfile:
    requests_per_month: int = 10_000_000
    cross_az_gb: int = 500
    internet_egress_gb: int = 1000
    ebs_gb: int = 100
    rds_backup_gb: int = 150
    s3_gb: int = 500
```

- Acts as the **canonical representation** of workload for pricing.  
- All workload-aware pricing functions accept a `UsageProfile` instance
  instead of ad-hoc dicts.

### 2. ServiceDataCache and workload-aware cost helpers

**File:** `backend/services/pricing.py`

- `ServiceDataCache` loads regional prices and exposes structured data:
  - `costs` – base monthly cost per service/SKU
  - `latency` – estimated latency per service (used by CSP/latency engine)
  - `options` – valid services per component type
- Workload-aware helpers use both **base prices** and `UsageProfile` to
  compute effective monthly cost, for example:

```python
def calculate_workload_cost(usage: UsageProfile, base_cost: float) -> float:
    """Illustrative example; exact coefficients live in services/pricing.py.

    Combines base SKU cost with request, transfer, and storage charges.
    """

    api_cost = (usage.requests_per_month / 1_000_000) * api_price_per_million
    transfer_cost = (
        usage.cross_az_gb * cross_az_price_per_gb
        + usage.internet_egress_gb * internet_egress_price_per_gb
    )
    storage_cost = (
        usage.ebs_gb * ebs_price_per_gb
        + usage.rds_backup_gb * rds_backup_price_per_gb
        + usage.s3_gb * s3_price_per_gb
    )

    return base_cost + api_cost + transfer_cost + storage_cost
```

> **Note:** The actual unit prices (`api_price_per_million`,
> `*_price_per_gb`) are derived from cached cloud pricing data and may change
> when live APIs or static tables are updated. This document uses generic
> placeholders rather than hard-coded numbers to avoid future drift.

### 3. Constraints / Optimizer Integration

**Files:**
- `backend/engines/constraints.py` – cost aggregation for candidate solutions  
- `backend/cmov4/optimizer.py` – orchestrates benchmark runs for CMOv4

The CSP/optimizer layer:

1. Receives a `UsageProfile` (or a dict convertible to it).  
2. For each candidate architecture, computes **per-service base cost** using
   `ServiceDataCache` (e.g., VM, DB, storage SKUs).  
3. Applies `calculate_workload_cost(...)` (or equivalent helpers) to adjust
   cost based on workload.  
4. Uses this workload-adjusted monthly cost when enforcing budget
   constraints and evaluating solutions.

---

## Workload Parameters

The workload model covers six key dimensions:

| Parameter              | Description                    | Unit   | Typical Example |
|------------------------|--------------------------------|--------|-----------------|
| `requests_per_month`   | API / HTTP requests           | count  | 10,000,000      |
| `cross_az_gb`          | Cross-AZ data transfer        | GB     | 500             |
| `internet_egress_gb`   | Internet egress traffic       | GB     | 1,000           |
| `ebs_gb`               | Block storage volume          | GB     | 100             |
| `rds_backup_gb`        | Database backup storage       | GB     | 150             |
| `s3_gb`                | Object storage                | GB     | 500             |

These parameters are:

- Exposed in the CMOv4 **benchmark UI** as part of the workload configuration.  
- Serialized as `usage_profile` in API payloads (see `FE_BE_SYNC.md`).  
- Mapped into a `UsageProfile` dataclass instance in the backend.

---

## API Integration

Workload-based pricing is primarily exercised via the **benchmark APIs** used
by CMOv4.

### 1. Preset Scenarios – `/api/benchmark` (GET)

See `FE_BE_SYNC.md` for full details. In summary:

- Frontend sends workload parameters as query string fields:  
  `requests_per_month`, `cross_az_gb`, `internet_egress_gb`, `ebs_gb`,
  `rds_backup_gb`, `s3_gb`.
- Backend (`app.py` → benchmark helper) builds a `UsageProfile` from the
  query and attaches it to the selected scenario.
- Optimizer uses this `UsageProfile` when computing CMOv3/CMOv4 costs.

### 2. Custom Scenarios – `/api/benchmark/dynamic` (POST)

The CMOv4 UI sends a full scenario, including workload:

```json
{
  "scenario": {
    "architecture": { "architecture_pattern": "microservices", "components": [/* ... */] },
    "constraints": {
      "maxBudget": 5000,
      "maxLatency": 150,
      "requiredProviders": ["AWS", "Azure", "GCP"]
    },
    "pricing": {},
    "usage_profile": {
      "requests_per_month": 10000000,
      "cross_az_gb": 500,
      "internet_egress_gb": 1000,
      "ebs_gb": 100,
      "rds_backup_gb": 150,
      "s3_gb": 500
    }
  }
}
```

Backend flow (simplified):

1. `app.py` extracts `scenario` and its `usage_profile`.  
2. `benchmark` helper converts `usage_profile` → `UsageProfile`.  
3. CMOv3/CMOv4 optimizers call pricing helpers with both base prices and this
   `UsageProfile` for cost computation.

> **Note:** Older `/api/optimize` payloads without a `usage_profile` field
> continue to work; the backend falls back to the default `UsageProfile`
> values shown above.

---

## Example Cost Impact (Illustrative)

For a representative workload profile:

- `requests_per_month` = 10M  
- `cross_az_gb` = 500  
- `internet_egress_gb` = 1000  
- `ebs_gb` = 100  
- `rds_backup_gb` = 150  
- `s3_gb` = 500  

the workload component of the monthly cost may contribute on the order of a
few hundred USD/month on top of base service prices. Exact values depend on
the region and live/static prices captured by `ServiceDataCache`.

The key qualitative effects are:

- **High request volumes** increase API Gateway / front-door costs.  
- **Cross-AZ and internet egress** make network-intensive architectures more
  expensive, especially in multi-region setups.  
- **Storage-heavy workloads** (large EBS/RDS/S3 footprints) significantly
  affect total monthly cost.

---

## Benefits

1. **Realistic Estimates** – Costs reflect actual usage instead of flat
   monthly list prices.  
2. **Better Service Selection** – High-volume workloads may favor
   dedicated/VM-based services over purely serverless options, or vice versa.  
3. **Accurate Multi-Cloud Analysis** – Data transfer and storage patterns
   become first-class drivers of provider choice.  
4. **Enterprise Relevance** – Mirrors real cloud billing patterns used in
   FinOps and TCO analyses.

---

## Backward Compatibility

- If **no** `usage_profile` is provided, the backend uses the default
  `UsageProfile` values (effectively a baseline workload) together with base
  service prices.  
- Existing API calls that predate workload support continue to work without
  modification.  
- Static/regional pricing remains available as a fallback when live cloud
  pricing APIs are unavailable.

---

## Related Documentation

- `backend/PRICING_METHODOLOGY.md` – Data sources (AWS/GCP static tables,
  Azure Retail API), caching, and pricing limitations.  
- `FE_BE_SYNC.md` – How workload parameters flow between CMOv4 frontend and
  backend (preset and dynamic benchmark endpoints).  
- `backend/tests/test_pricing_validation.py` – Sanity checks for realistic
  price ranges and API response structures.  
- `backend/tests/test_cache_update.py` – Cache TTL, fallback, and
  partial-success behavior for pricing data.
