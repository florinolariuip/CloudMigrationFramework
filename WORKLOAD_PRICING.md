# Workload-Based Pricing Implementation

**Added:** December 2025  
**Status:** Production Ready

## Overview

The system now supports workload-based pricing calculations instead of static monthly service costs. This provides realistic cost estimates based on actual usage patterns.

## Implementation

### Backend Changes

1. **New Function**: `calculate_workload_cost()` in `backend/services/pricing.py`
   - Calculates costs based on actual usage metrics
   - Replaces static monthly costs with usage-driven calculations

2. **Updated Constraints Engine**: `backend/engines/constraints.py`
   - Modified `calculate_total_cost()` to accept workload profiles
   - Passes workload data to cost calculation functions

3. **API Integration**: `backend/app.py`
   - Added workload parameter parsing in `/api/optimize` endpoint
   - Validates and passes workload data to constraints engine

### Workload Parameters

| Parameter | Description | Unit | Example |
|-----------|-------------|------|---------|
| `requests_per_month` | API Gateway requests | requests | 10,000,000 |
| `cross_az_gb` | Cross-AZ data transfer | GB | 500 |
| `internet_egress_gb` | Internet egress traffic | GB | 1,000 |
| `ebs_gb` | EBS storage volume | GB | 100 |
| `rds_backup_gb` | RDS backup storage | GB | 150 |
| `s3_gb` | S3 object storage | GB | 500 |

### Pricing Calculations

```python
# API Gateway: $3.50 per 1M requests
api_cost = (requests_per_month / 1_000_000) * 3.50

# Data transfer: $0.02/GB cross-AZ, $0.09/GB internet
transfer_cost = (cross_az_gb * 0.02) + (internet_egress_gb * 0.09)

# Storage: EBS $0.08/GB, RDS backup $0.095/GB, S3 $0.023/GB
storage_cost = (ebs_gb * 0.08) + (rds_backup_gb * 0.095) + (s3_gb * 0.023)

total_workload_cost = base_cost + api_cost + transfer_cost + storage_cost
```

## Usage

### API Request Format

```json
{
  "constraints": {
    "maxBudget": 5000,
    "maxLatency": 150,
    "maxProviders": 3
  },
  "preferences": {
    "prioritizeCost": true
  },
  "workload": {
    "requests_per_month": 10000000,
    "cross_az_gb": 500,
    "internet_egress_gb": 1000,
    "ebs_gb": 100,
    "rds_backup_gb": 150,
    "s3_gb": 500
  }
}
```

### Cost Impact Example

For the example workload profile:
- API costs: $35 (10M requests × $3.50/M)
- Transfer costs: $100 (500GB × $0.02 + 1TB × $0.09)
- Storage costs: $37.25 (100GB × $0.08 + 150GB × $0.095 + 500GB × $0.023)
- **Total workload overhead**: ~$172/month

## Benefits

1. **Realistic Estimates**: Costs reflect actual usage patterns instead of flat monthly fees
2. **Better Service Selection**: High-volume workloads favor different services (dedicated vs serverless)
3. **Accurate Multi-Cloud Analysis**: Data transfer costs become significant factors
4. **Enterprise Relevance**: Matches real cloud billing patterns

## Backward Compatibility

- If no workload profile is provided, the system defaults to base service costs (0 usage)
- Existing API calls continue to work without modification
- Static pricing remains available as fallback

## Future Enhancements

- Frontend workload input form
- Workload profile templates for common scenarios
- Time-based usage patterns (peak/off-peak)
- Reserved instance pricing integration