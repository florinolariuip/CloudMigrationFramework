# Optimization Preferences in CMOv4

## Overview

Preferences let you bias the optimization engine toward solutions that better match your business priorities, **without changing the underlying Pareto frontier**. They are implemented in the expert system: during scoring, solutions that satisfy selected preferences receive configurable **bonus points**.

Preferences in CMOv4 are:

- **Soft**: they shift scores and rankings, but do not filter out solutions.
- **Server-side configured**: thresholds and bonuses live in `backend/config.py`.
- **Explained**: applied bonuses are surfaced in the explanation output.

## Available Preferences

### 1. Preferred Cloud Provider

- **Options**: No Preference, AWS, Azure, GCP
- **Effect**: Solutions whose main provider matches your choice receive a **provider bonus**.
- **Typical use cases**:
  - Existing contracts or credits with a provider
  - Team expertise on a specific platform
  - Compliance or data residency constraints

**Example:**

- Preference: `preferredProvider = "AWS"`
- Solution using mostly AWS services → gets the provider bonus
- Solution using only Azure/GCP → no provider bonus

### 2. Prioritize Cost Efficiency

- **Idea**: Favor solutions whose **monthly cost** stays below a configured cost threshold.
- **Effect**: If `prioritizeCost = true` and the total cost is below the configured threshold, the solution receives a **cost bonus**.
- **Typical use cases**:
  - Tight or fixed budgets
  - Cost-sensitive internal tools or POCs
  - Early-stage startups

**Example scoring sketch:**

- Solution A: cost below the configured “cost priority” threshold → gets the cost bonus
- Solution B: cost above that threshold → no cost bonus

### 3. Prioritize Performance

- **Idea**: Favor solutions with **low end-to-end latency** under a performance threshold.
- **Effect**: If `prioritizePerformance = true` and the predicted latency is below the configured threshold, the solution receives a **performance bonus**.
- **Typical use cases**:
  - Real-time or interactive workloads
  - User-facing APIs with strict SLAs
  - Trading / analytics pipelines where latency matters

**Example scoring sketch:**

- Solution A: latency below the performance threshold → gets the performance bonus
- Solution B: latency above that threshold → no performance bonus

> Threshold values and bonus magnitudes are **configurable**, not hard-coded into the preference model. See `EXPERT_RULES_CONFIG` below.

## How Preferences Flow Through the System

### Data Flow

```text
Frontend (user selects preferences)
        ↓
API payload (preferences included in request)
        ↓
Backend benchmark flow (extract preferences)
        ↓
Optimizer (builds Preferences object)
        ↓
Expert System (rules.py applies bonuses)
        ↓
Ranked solutions (sorted by final score)
```

Concretely:

- The frontend sends a `preferences` object as part of the benchmark request payload.
- The backend parses that into a `Preferences` / `UserPreferences` structure.
- The expert system (`backend/engines/rules.py`) reads both:
  - Objective metrics (cost, latency, provider),
  - User preferences,
  - And configuration from `EXPERT_RULES_CONFIG`,
  and then adds bonus points to the base score when conditions are met.

### Scoring Illustration

**Without preferences (baseline):**

```text
Solution A: cost = low, latency = medium, provider = AWS
Base expert score: 75
Final score: 75  (no bonuses applied)
```

**With Cost Priority + AWS Preference:**

```text
Solution A: cost < cost_threshold, latency = medium, provider = AWS
Base expert score: 75
+ cost priority bonus
+ preferred provider bonus
Final score: 75 + cost_bonus + provider_bonus
```

**With Performance Priority Only:**

```text
Solution B: cost = higher, latency < perf_threshold, provider = Azure
Base expert score: 70
+ performance priority bonus
Final score: 70 + performance_bonus
```

The **relative ordering** of solutions changes because some get additional points.

## Combining Preferences

All three preferences can be enabled at once:

- `preferredProvider = "Azure"`
- `prioritizeCost = true`
- `prioritizePerformance = true`

A solution that:

- Uses Azure as main provider,
- Has cost below the cost threshold,
- Has latency below the performance threshold,

will receive **all three bonuses**, creating a strong bias toward that type of solution. Other solutions are still present on the Pareto front but may rank lower in the list.

## Real-World Scenarios

### Scenario 1: Startup with Provider Credits

```text
Preferred Provider: AWS
Prioritize Cost:    true
Prioritize Perf:    false
```

- Effect: AWS-based solutions that are relatively cheap rise to the top,
  even if they are not the absolute fastest.

### Scenario 2: Latency-Critical Platform

```text
Preferred Provider: No Preference
Prioritize Cost:    false
Prioritize Perf:    true
```

- Effect: The optimizer favors the fastest solutions across all providers;
  cost matters less in the ranking.

### Scenario 3: Enterprise with Existing Azure Contract

```text
Preferred Provider: Azure
Prioritize Cost:    true
Prioritize Perf:    true
```

- Effect: Azure solutions that are both cost-effective and low-latency
  receive the largest scoring advantage.

## Configuration and Code References

### Expert Rules Configuration (`backend/config.py`)

The thresholds and bonus amounts are defined in `EXPERT_RULES_CONFIG`:

```python
EXPERT_RULES_CONFIG = {
    "preferred_provider_bonus": ...,
    "cost_priority_threshold": ...,
    "cost_priority_bonus": ...,
    "performance_priority_threshold": ...,
    "performance_priority_bonus": ...,
}
```

- **Threshold keys** control when a bonus is applied (e.g., max cost, max latency).
- **Bonus keys** control how many points are added to the expert score.

Exact values may change over time; they’re kept in config to make tuning easier without touching the rules engine code.

### Rules Engine (`backend/engines/rules.py`)

The expert system implements checks similar to:

```python
# Preferred provider
if self.preferences.preferredProvider and main_provider == self.preferences.preferredProvider:
    self.final_score += self.rules_config["preferred_provider_bonus"]

# Cost priority
if self.preferences.prioritizeCost and cost < self.rules_config["cost_priority_threshold"]:
    self.final_score += self.rules_config["cost_priority_bonus"]

# Performance priority
if self.preferences.prioritizePerformance and latency < self.rules_config["performance_priority_threshold"]:
    self.final_score += self.rules_config["performance_priority_bonus"]
```

(The actual line numbers can change; follow the rule names rather than specific line references.)

## Frontend Integration (CMOv4)

### UI Controls

In the CMOv4 frontend (e.g. `cmov4.html`):

- **Dropdown**: Preferred cloud provider (No Preference / AWS / Azure / GCP).
- **Checkboxes / toggles**:
  - “Prioritize lower cost”
  - “Prioritize lower latency”
- Changes affect the **next** benchmark or optimization run.

### API Payload Shape

Preferences are sent in a `preferences` field:

```json
{
  "preferences": {
    "preferredProvider": "AWS",
    "prioritizeCost": true,
    "prioritizePerformance": false
  }
}
```

The backend treats this block as optional; if omitted, default behavior is “no special preference” (pure expert rules based on objectives only).

## Relationship to the Pareto Frontier

Preferences **do not modify**:

- How the Pareto frontier is computed,
- The set of feasible solutions.

The frontier is still constructed purely from objective trade-offs (cost, latency, and other objectives).

Preferences **do modify**:

1. **Ranking**: which solution appears as the “top suggestion”.
2. **Alternative suggestions**: which non-top solutions are highlighted.
3. **Explainability output**: the explanation explicitly lists which bonuses were applied and why (e.g., “AWS preferred provider bonus applied”, “cost below threshold bonus applied”).

This separation is important for the paper and for reviewers: **objective evaluation vs. subjective ranking** are kept distinct.

## Limitations

- Preferences are **soft**: they bias scores but never make a solution infeasible.
- Thresholds and bonuses are **global** in CMOv4; users do not (yet) tune numeric values from the UI.
- Only a single preferred provider can be selected at a time.

## Possible Future Extensions

1. **UI-tunable thresholds**  
   Expose cost and latency thresholds in the frontend so users can interactively steer how strict the preferences are.

2. **Configurable weights per user**  
   Allow users or scenarios to override bonus magnitudes on a per-run basis.

3. **Multi-provider preferences**  
   Support sets like “prefer AWS or Azure” with per-provider weights.

4. **Custom business rules**  
   Let advanced users define organization-specific rules that plug into the same expert system (e.g., “no data outside EU”, “prefer managed services over IaaS”).
