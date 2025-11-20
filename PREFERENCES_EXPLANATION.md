# Optimization Preferences in CMOv4

## Overview
Preferences allow you to guide the optimization engine to favor solutions that align with your business priorities. They work by **adding bonus points** to solutions that meet certain criteria during the expert system scoring phase.

## Available Preferences

### 1. **Preferred Cloud Provider**
- **Options**: No Preference, AWS, Azure, GCP
- **Impact**: +8 bonus points if the solution's main provider matches your preference
- **Use Case**: 
  - Existing cloud contracts or credits
  - Team expertise with specific provider
  - Compliance requirements for specific regions

**Example**: If you select "AWS" as preferred provider:
- Solution using mostly AWS services: Gets +8 bonus points
- Solution using Azure/GCP: No bonus

### 2. **Prioritize Cost Efficiency** ✓
- **Threshold**: Solutions below $2,600/month
- **Impact**: +5 bonus points for cost-efficient solutions
- **Use Case**:
  - Tight budget constraints
  - Cost-sensitive projects
  - Startups or proof-of-concepts

**Example Scoring**:
- Solution A: $2,400/month → Gets +5 bonus points ✓
- Solution B: $2,800/month → No bonus (above threshold)

### 3. **Prioritize Performance** ⚡
- **Threshold**: Solutions below 10.5ms latency
- **Impact**: +5 bonus points for high-performance solutions
- **Use Case**:
  - Real-time applications
  - Low-latency requirements
  - Customer experience focus

**Example Scoring**:
- Solution A: 9.8ms latency → Gets +5 bonus points ✓
- Solution B: 12ms latency → No bonus (above threshold)

## How Preferences Influence Optimization

### Data Flow
```
Frontend Selection
       ↓
API Request (preferences in payload)
       ↓
Backend benchmark.py (extracts preferences)
       ↓
optimizer.py (creates Preferences object)
       ↓
Expert System rules.py (applies bonus rules)
       ↓
Ranked Solutions (sorted by score)
```

### Scoring Impact

**Without Preferences** (Default):
```
Solution A: Cost=$2,400, Latency=10ms, Provider=AWS
Base Score: 75 points
Final Score: 75 points
```

**With Cost Priority + AWS Preference**:
```
Solution A: Cost=$2,400, Latency=10ms, Provider=AWS
Base Score: 75 points
+ Cost Priority Bonus: +5 points (below $2,600)
+ Preferred Provider Bonus: +8 points (AWS)
Final Score: 88 points ⬆️
```

**With Performance Priority**:
```
Solution B: Cost=$2,800, Latency=9ms, Provider=Azure
Base Score: 70 points
+ Performance Priority Bonus: +5 points (below 10.5ms)
Final Score: 75 points ⬆️
```

## Combining Preferences

You can enable multiple preferences simultaneously:

**Cost + Performance + AWS**:
```
Solution C: Cost=$2,500, Latency=10ms, Provider=AWS
Base Score: 80 points
+ Cost Priority: +5
+ Performance Priority: +5
+ Preferred Provider: +8
Final Score: 98 points ⬆️⬆️⬆️
```

This creates a **strong bias** toward solutions that meet all three criteria.

## Real-World Scenarios

### Scenario 1: Startup on AWS Credits
```
✓ Preferred Provider: AWS
✓ Prioritize Cost Efficiency
✗ Prioritize Performance

Result: Optimizer favors cheap AWS solutions, even if latency is higher
```

### Scenario 2: High-Performance Trading Platform
```
✗ Preferred Provider: No Preference
✗ Prioritize Cost Efficiency
✓ Prioritize Performance

Result: Optimizer favors fastest solutions across all providers
```

### Scenario 3: Balanced Enterprise Migration
```
✓ Preferred Provider: Azure (existing contract)
✓ Prioritize Cost Efficiency
✓ Prioritize Performance

Result: Optimizer seeks Azure solutions that are both fast AND cheap
```

## Code References

### Backend Configuration (`backend/config.py`)
```python
EXPERT_RULES_CONFIG = {
    "preferred_provider_bonus": 8,      # Bonus for using preferred cloud
    "cost_priority_threshold": 2600,    # Threshold for cost bonus
    "cost_priority_bonus": 5,           # Bonus amount for cost
    "performance_priority_threshold": 10.5,  # Threshold for perf bonus
    "performance_priority_bonus": 5,    # Bonus amount for performance
}
```

### Rules Engine (`backend/engines/rules.py`)

**Preferred Provider Rule** (Line 98):
```python
if self.preferences.preferredProvider and main_provider == self.preferences.preferredProvider:
    self.final_score += self.rules_config["preferred_provider_bonus"]
```

**Cost Priority Rule** (Line 109):
```python
if self.preferences.prioritizeCost and cost < self.rules_config["cost_priority_threshold"]:
    self.final_score += self.rules_config["cost_priority_bonus"]
```

**Performance Priority Rule** (Line 120):
```python
if self.preferences.prioritizePerformance and latency < self.rules_config["performance_priority_threshold"]:
    self.final_score += self.rules_config["performance_priority_bonus"]
```

## Frontend Integration (CMOv4)

### UI Controls
- **Dropdown**: Select preferred cloud provider
- **Checkboxes**: Toggle cost and performance priorities
- **Live**: Changes apply immediately to next benchmark run

### API Payload
```json
{
  "preferences": {
    "preferredProvider": "AWS",
    "prioritizeCost": true,
    "prioritizePerformance": false
  }
}
```

## Tuning Guide

### When to Use Cost Priority
- Budget < $3,000/month
- Proof-of-concept projects
- Non-critical workloads
- Development/staging environments

### When to Use Performance Priority
- Latency SLA < 15ms
- Real-time applications
- Customer-facing services
- High-throughput requirements

### When to Set Preferred Provider
- Existing cloud contracts
- Regional compliance needs
- Team has provider-specific expertise
- Using provider-specific credits

## Impact on Pareto Frontier

Preferences **do not change** the Pareto frontier (it's still based on objective cost/latency trade-offs), but they **do influence**:

1. **Top Solution Ranking**: Solutions matching preferences rank higher
2. **Alternative Recommendations**: Preferred alternatives bubble up
3. **Explainability**: Rules show which bonuses were applied

## Limitations

- Preferences are **soft constraints** (they influence scoring but don't filter solutions)
- Thresholds are **fixed** in CMOv4 (no UI tuning yet, unlike CMOv3)
- Bonus values are **configured server-side** (backend/config.py)

## Future Enhancements

1. **Dynamic Thresholds**: Allow users to adjust cost/latency thresholds in UI
2. **Weight Tuning**: Customize bonus point values per preference
3. **Multi-Provider Preference**: Prefer 2 out of 3 providers
4. **Custom Rules**: Define business-specific preference rules
