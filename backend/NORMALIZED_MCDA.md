# Normalized Multi-Criteria Decision Analysis (MCDA) Interface

## Overview

The **Normalized MCDA Interface** (`index_normalized.html`) is an advanced, research-oriented UI built on top of the same CSP + Expert + Pareto optimization pipeline used by CMOv3/CMOv4. It exposes **6-metric normalization** with **configurable weights** and **real-time validation** for scenarios where a single aggregated score is useful in addition to the Pareto frontier.

This implementation follows established MCDA research methodologies and provides transparency in multi-objective decision making. It complements (rather than replaces) the main `index.html` and `cmov4.html` flows by re-scoring feasible solutions returned by the backend using a normalized weighted-sum model.

---

## 🎯 Key Features

### 1. **6-Metric Multi-Criteria Decision Analysis**

The interface evaluates cloud solutions across **6 normalized criteria** based on established research in cloud service selection:

| Metric | Direction | Weight (Default) | Description |
|--------|-----------|------------------|-------------|
| **Cost** | Lower is better | 30% | Total monthly cost (normalized, inverted) |
| **Latency** | Lower is better | 20% | Average response time (normalized, inverted) |
| **Reliability** | Higher is better | 20% | Uptime based on provider SLAs |
| **Security** | Higher is better | 15% | Encryption, compliance, IAM features |
| **Vendor Risk** | Lower is better | 10% | Lock-in risk (1/n providers, inverted) |
| **Scalability** | Higher is better | 5% | Serverless, containers, auto-scaling |

### 2. **Min-Max Normalization**

All metrics are normalized to `[0, 1]` range using:

```
normalized_value = (value - min) / (max - min)
```

**Edge Case Handling:**
- If `max == min` (no variation): normalized value = `0.5` (middle value)
- Values clamped to `[0, 1]` to prevent overflow
- NaN/Infinity prevented with `safeNormalize()` function

### 3. **Weighted Sum Model (WSM)**

Final score calculated as:

```
score = cost_weight × (1 - norm_cost) 
      + latency_weight × (1 - norm_latency)
      + reliability_weight × norm_reliability
      + security_weight × norm_security
      + vendor_risk_weight × (1 - norm_vendor_risk)
      + scalability_weight × norm_scalability
```

**Note:** Cost, latency, and vendor risk are inverted (lower is better)

### 4. **Configurable Weights**

Users can adjust weights with **real-time validation**:
- Sliders: 0% to 100% for each metric
- Total must sum to **100%** (±1% tolerance)
- Visual warning if total ≠ 100%
- Changes immediately recalculate scores

---

## 🏗️ Architecture

### Data Flow

```
User Input (Constraints + Weights)
    ↓
Backend API (/api/experiment)
    ↓
CSP Engine (Generate feasible solutions)
    ↓
Normalization (Min-max scaling)
    ↓
Weighted Sum Model (Calculate scores)
    ↓
Ranking (Sort by score)
    ↓
Frontend Display
    ↓
Pareto Frontier + Sankey + Explanation Card
```

### API Usage

In the current implementation, normalized MCDA runs on top of the standard optimization APIs (for example, `/api/optimize` or `/api/benchmark`), which first generate a set of feasible solutions via CSP + Expert + Pareto. Those solutions are then passed through the normalized MCDA scoring function (`evaluate_solutions_normalized`) in `backend/engines/rules.py`.

An earlier experimental setup used a dedicated endpoint such as `/api/experiment`. The effective payload shape is still the same when invoking MCDA scoring explicitly:

**Example request body:**
```json
{
   "constraints": {
      "maxBudget": 5000,
      "maxLatency": 150,
      "maxProviders": 3
   },
  "weights": {
    "cost": 0.30,
    "latency": 0.20,
    "reliability": 0.20,
    "security": 0.15,
    "vendor_risk": 0.10,
    "scalability": 0.05
  }
}
```

**Response:**
```json
{
  "solutions": [
    {
      "configuration": {...},
      "cost": 2340,
      "latency": 8.5,
      "reliability": 0.9995,
      "security_score": 0.92,
      "vendor_lockin_risk": 0.33,
      "scalability_score": 0.85,
      "score": 0.8234,
      "providers": 3
    }
  ],
  "normalization": {
    "cost_min": 2100,
    "cost_max": 4800,
    "latency_min": 6.2,
    "latency_max": 15.8,
    "reliability_min": 0.95,
    "reliability_max": 0.9999,
    "security_min": 0.85,
    "security_max": 0.95,
    "vendor_risk_min": 0.33,
    "vendor_risk_max": 1.0,
    "scalability_min": 0.70,
    "scalability_max": 0.90,
    "weights": {...}
  }
}
```

---

## 📊 User Interface Components

### 1. **Constraints Panel**
- Max Budget: Default $5,000
- Max Latency: Default 150ms (tight experimental scenarios may still use values like 12ms)
- Max Providers: Default 3 (1, 2, or 3)

### 2. **Weights Configuration**
- 6 sliders with percentage display
- Real-time total calculation
- Visual validation (red if ≠100%)

### 3. **Results Table**
Displays top 20 solutions with:
- Rank (⭐ for Pareto optimal)
- Cost, Latency, Reliability %
- Security %, Vendor Risk %, Scalability %
- Final Score (weighted)
- Actions: View details, Explain score

### 4. **Top Solution Explanation Card** ✨ NEW

**Automatic analysis of #1 ranked solution:**

#### Section 1: Why This Solution?
- Final score achieved
- Provider distribution (AWS, Azure, GCP)
- Architecture pattern (Serverless/Container/VM-based)

#### Section 2: Architecture Pattern
- Auto-detects: Serverless, Containers, Managed Services
- Tags: Lambda, Functions, Kubernetes, RDS, etc.
- Benefits explanation

#### Section 3: Top Strengths
- Top 3 performing metrics
- Visual progress bars
- Raw metric values

#### Section 4: Trade-offs & Considerations
- 2 weakest metrics
- Vendor lock-in risk assessment
- Multi-cloud strategy advice

#### Section 5: Intelligent Recommendations
Context-aware suggestions based on actual values:

**Cost Optimization:**
- High cost (>70%): "Consider reserved instances or savings plans"
- Medium cost: "Good balance, review spending monthly"
- Low cost (<30%): "Excellent efficiency, monitor for unused resources"

**Performance:**
- High latency (>70%): "Consider edge computing or CDN"
- Medium latency: "Acceptable, monitor user experience"
- Low latency (<30%): "Outstanding, maintain caching strategies"

**Reliability:**
- High score (>70%): "Ensure proper monitoring and alerting"
- Lower score: "Implement circuit breakers and retry mechanisms"

**Security:**
- High score (>70%): "Strong posture, maintain regular audits"
- Lower score: "Enhance with encryption and IAM policies"

### 5. **Normalization Details Panel**
- Min-max ranges for all 6 metrics
- Active weights display
- Scoring formula explanation
- Academic foundation notes

### 6. **Pareto Frontier Visualization**
- Interactive scatter plot (Cost vs Latency)
- Pareto-optimal solutions highlighted
- Hover for details
- Metrics: Hypervolume, Spacing, Coverage

### 7. **Dual Sankey Diagrams**

**Cost Flow:**
```
Providers (AWS/Azure/GCP) → Component Categories → Total Cost
```

**Latency Flow:**
```
Providers (AWS/Azure/GCP) → Individual Components → Total Latency
```

---

## 🔬 Academic Foundation

### Mathematical Model

**Normalization Function:**
```python
def safeNormalize(value, min, max):
    range = max - min
    if range == 0 or isNaN(range):
        return 0.5  # No variation
    normalized = (value - min) / range
    return clamp(normalized, 0, 1)
```

**Scoring Function:**
```python
score = Σ(weight_i × transformed_metric_i)

where:
  transformed_metric_i = {
    metric_i           if higher is better
    1 - metric_i       if lower is better
  }
```

### Advantages Over Traditional Approaches

| Aspect | Traditional | Our Approach |
|--------|-------------|--------------|
| Normalization | Often skipped | Min-max with edge cases |
| Weights | Fixed | User-configurable |
| Transparency | Black box | Full breakdown |
| Metrics | 2-3 criteria | 6 comprehensive criteria |
| Validation | Manual | Real-time |
| Explainability | None | Automatic insights |

### Comparison with Related Work

- **AHP (Analytic Hierarchy Process)**: Requires pairwise comparisons (n²), our approach is simpler
- **TOPSIS**: Similar normalization, but we add explainability
- **PROMETHEE**: More complex preference functions, our WSM is interpretable
- **ELECTRE**: Outranking relations, our scoring is more intuitive

---

## 🎓 Usage Scenarios

### Scenario 1: Cost-Conscious Organization
**Configuration:**
- Cost weight: 50%
- Latency weight: 10%
- Other weights: 10% each

**Expected Result:** Low-cost solution, potentially higher latency

### Scenario 2: Performance-Critical Application
**Configuration:**
- Latency weight: 40%
- Cost weight: 20%
- Reliability weight: 20%
- Other weights: 6.67% each

**Expected Result:** Ultra-low latency, higher cost acceptable

### Scenario 3: Balanced Enterprise
**Configuration:**
- Default weights (30/20/20/15/10/5)

**Expected Result:** Well-balanced solution optimizing all criteria

### Scenario 4: Security-First Organization
**Configuration:**
- Security weight: 35%
- Reliability weight: 25%
- Vendor risk weight: 15%
- Other weights: 8.33% each

**Expected Result:** Maximum security and reliability, cost secondary

---

## 🔧 Implementation Details

### Frontend (index_normalized.html)

**Key Functions:**

1. **`safeNormalize(value, min, max)`**
   - Global helper function
   - Handles division by zero
   - Clamps to [0, 1]

2. **`updateWeight(metric, value)`**
   - Updates weight sliders
   - Real-time validation
   - Visual feedback

3. **`runAnalysis()`**
   - Collects constraints and weights
   - Calls `/api/experiment`
   - Renders results

4. **`renderResults(results, normalization)`**
   - Displays solutions table
   - Generates explanation card
   - Updates visualizations

5. **`generateTopSolutionExplanation(topSol, norm)`**
   - Analyzes #1 solution
   - Detects architecture patterns
   - Generates recommendations

6. **`explainScore(idx)`**
   - Modal with detailed breakdown
   - Metric contributions
   - Visual progress bars

### Backend (backend/engines/rules.py)

**Key Functions:**

1. **`evaluate_solutions_normalized(solutions, weights)`**
   - Min-max normalization
   - Weighted sum calculation
   - Returns sorted solutions + normalization data

2. **`calculate_reliability(solution)`**
   - Based on provider SLAs
   - AWS/GCP: 99.99%
   - Azure: 99.95%

3. **`calculate_security_score(solution)`**
   - Detects encryption services
   - Identity management (IAM, AD)
   - Compliance features

4. **`calculate_vendor_lockin_risk(solution)`**
   - Formula: 1 / number_of_providers
   - 1 provider = 100% risk
   - 3 providers = 33% risk

5. **`calculate_scalability_score(solution)`**
   - Detects serverless (Lambda, Functions)
   - Detects containers (Kubernetes, ECS)
   - Detects auto-scaling services

---

## 📈 Metrics Calculation Details

### 1. Cost
**Source:** Live pricing data from AWS, Azure, GCP APIs  
**Normalization:** Min-max across all feasible solutions  
**Transformation:** Inverted (1 - normalized) because lower is better

### 2. Latency
**Source:** Benchmarked latency data for each service  
**Calculation:** Weighted average based on component types  
**Normalization:** Min-max  
**Transformation:** Inverted (1 - normalized)

### 3. Reliability
**Source:** Provider SLA data  
**Calculation:** Product of component reliabilities  
**Formula:** `∏(SLA_i)` for all components  
**Normalization:** Min-max  
**Transformation:** Direct (higher is better)

### 4. Security
**Source:** Service feature detection  
**Components:**
- Encryption at rest: +20%
- Encryption in transit: +20%
- Identity management: +30%
- Compliance certifications: +30%
**Normalization:** Min-max  
**Transformation:** Direct (higher is better)

### 5. Vendor Lock-in Risk
**Source:** Configuration analysis  
**Formula:** `1 / unique_providers`  
**Examples:**
- 1 provider: 100% risk
- 2 providers: 50% risk
- 3 providers: 33% risk
**Normalization:** Min-max  
**Transformation:** Inverted (1 - normalized)

### 6. Scalability
**Source:** Architecture pattern detection  
**Components:**
- Serverless: +40%
- Containers: +30%
- Managed databases: +20%
- Load balancers: +10%
**Normalization:** Min-max  
**Transformation:** Direct (higher is better)

---

## 🐛 Edge Cases Handled

### 1. Zero Range (All Solutions Identical)
**Problem:** Division by zero in normalization  
**Solution:** Return 0.5 (middle value) for that metric

### 2. NaN/Infinity Values
**Problem:** Invalid calculations propagate  
**Solution:** `safeNormalize()` checks and clamps

### 3. Weights Don't Sum to 100%
**Problem:** Invalid weight configuration  
**Solution:** Visual warning, but still processes (normalized internally)

### 4. No Feasible Solutions
**Problem:** Constraints too tight  
**Solution:** Display "No results found" message

### 5. Duplicate Solutions
**Problem:** Same configuration appears multiple times  
**Solution:** Deduplication at API level before processing

---

## 🔍 Debugging & Troubleshooting

### Common Issues

**Issue 1: "safeNormalize is not defined"**
- **Cause:** Function scope issue
- **Fix:** Function moved to global scope (v41)

**Issue 2: NaN in score explanations**
- **Cause:** Division by zero in normalization
- **Fix:** safeNormalize with edge case handling (v40)

**Issue 3: Weights don't sum to 100%**
- **Cause:** Rounding errors or user input
- **Fix:** Visual warning, backend normalizes weights

**Issue 4: Explanation card not showing**
- **Cause:** No solutions returned
- **Fix:** Check constraints, ensure feasible solutions exist

### Browser Console Commands

```javascript
// Check current weights
console.log(weights);

// Check all results
console.log(allResults);

// Check normalization data
console.log(currentNormalization);

// Test safeNormalize
console.log(safeNormalize(50, 0, 100)); // Should be 0.5
console.log(safeNormalize(50, 50, 50)); // Should be 0.5 (edge case)
```

---

## 📚 References

### Academic Papers

1. **Hwang, C.L., & Yoon, K. (1981).** Multiple Attribute Decision Making: Methods and Applications. Springer.
2. **Saaty, T.L. (1980).** The Analytic Hierarchy Process. McGraw-Hill.
3. **Brans, J.P., & Vincke, P. (1985).** PROMETHEE: A new family of outranking methods. IFORS.
4. **Deb, K., et al. (2002).** A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE TEC.

### Implementation References

- **Min-Max Normalization:** Standard feature scaling technique
- **Weighted Sum Model:** Classic MCDA aggregation method
- **Pareto Optimality:** Multi-objective optimization fundamental
- **SLA Data:** AWS, Azure, GCP official documentation

---

## 🚀 Future Enhancements

### Planned Features

1. **Dynamic Weight Learning**
   - Learn user preferences over time
   - Suggest optimal weight configurations
   
2. **Sensitivity Analysis**
   - Show how weight changes affect solutions
   - Tornado diagrams for robustness

3. **Historical Comparison**
   - Compare current vs previous optimizations
   - Trend analysis

4. **Export Capabilities**
   - PDF reports
   - CSV data export
   - Presentation slides

5. **Advanced Metrics**
   - Carbon footprint
   - Data residency compliance
   - Disaster recovery readiness

---

## 📞 Support & Contribution

For issues or questions about the Normalized MCDA interface:
- Check browser console for errors
- Verify API endpoint is reachable
- Ensure weights sum to 100%
- Review normalization details panel

**Version:** v42 (November 2025)  
**Status:** Production-ready  
**License:** Research/Academic use
