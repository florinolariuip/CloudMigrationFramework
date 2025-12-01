# CMOv4 Architecture Logic

## Component → Architecture → Optimization Flow

### 1. **Components** (Building Blocks)
Components are the individual services/resources in your cloud architecture:

```python
Component {
    name: "Frontend",           # Human-readable name
    type: "web",                 # Component type (web, compute, database, etc.)
    instance_count: 2,           # How many instances
    tech_stack: {                # Technology preferences
        framework: "React"
    },
    dependencies: ["AppServer"]  # What this depends on
}
```

**Component Types Available:**
- `web` → API Gateway
- `compute` → Application Server  
- `database` → Database
- `cache` → Cache (Redis/Memcached)
- `monitoring` → Monitoring (CloudWatch/Prometheus)
- `message_queue` → Message Queue (SQS/Pub/Sub)
- `storage` → Object Storage (S3/Blob)
- `load_balancer` → Load Balancer
- `backup` → Backup Service
- `security` → Encryption/Security
- `cdn` → Content Delivery Network
- `analytics` → Analytics Service
- `encryption` → Key Management
- `containers` → Container Orchestration (EKS/AKS/GKE)
- `serverless_compute` → Serverless Functions (Lambda/Functions)
- `identity` → Identity Management (IAM)

### 2. **Architecture** (Overall Design)
Architecture is the collection of components with their relationships:

```python
Architecture {
    components: [Component1, Component2, ...],
    relationships: [                    # How components connect
        {from: "Frontend", to: "AppServer", type: "depends_on"}
    ],
    multi_tenancy: False,               # Single vs multi-tenant
    architecture_pattern: "monolith"    # Pattern type
}
```

**Architecture Patterns:**
- **Monolith**: Single deployment unit, simpler, lower latency
- **Microservices**: Distributed services, scalable, higher latency
- **Event-Driven**: Async messaging, loosely coupled, complex

### 3. **Component → CMOv3 Mapping**
CMOv4 component types are mapped to CMOv3 service names for optimization:

```python
COMPONENT_TYPE_MAPPING = {
    'web': 'api_gateway',
    'compute': 'application_server',
    'database': 'database',
    'cache': 'cache',
    ...
}
```

This allows CMOv4 to use CMOv3's proven CSP + Expert System optimization!

### 4. **Optimization Flow**

```
┌─────────────────┐
│ User Selects    │
│ Components      │ → "web", "compute", "database", "cache"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Map to CMOv3    │
│ Services        │ → ["api_gateway", "application_server", 
└────────┬────────┘    "database", "cache"]
         │
         ▼
┌─────────────────┐
│ Generate        │
│ Feasible        │ → CSP generates all valid combinations
│ Solutions       │   (AWS RDS + AWS EC2 + ..., etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apply Expert    │
│ Rules           │ → Score each solution using CMOv3 rules
└────────┬────────┘   (cost thresholds, latency, multi-cloud)
         │
         ▼
┌─────────────────┐
│ Compute Pareto  │
│ Frontier        │ → Find non-dominated solutions
└────────┬────────┘   (best cost/latency trade-offs)
         │
         ▼
┌─────────────────┐
│ Return Results  │ → solutions, metrics, explanations,
└─────────────────┘   thresholds_used, pareto_frontier
```

## How Components Affect Optimization

### Example: 5-Component Scenario

**User selects:**
```javascript
components: [
  {type: "web"},      // Frontend
  {type: "compute"},  // App Server
  {type: "database"}, // Database
  {type: "cache"},    // Cache
  {type: "monitoring"} // Monitoring
]
```

**Mapped to CMOv3:**
```python
selected_components = [
    "api_gateway",
    "application_server", 
    "database",
    "cache",
    "monitoring"
]
```

**CSP generates combinations like:**
```
Solution 1: AWS API Gateway + AWS EC2 + AWS RDS + AWS ElastiCache + AWS CloudWatch
Solution 2: GCP API Gateway + AWS EC2 + AWS RDS + GCP Memorystore + AWS CloudWatch
Solution 3: AWS API Gateway + GCP Functions + AWS RDS + AWS ElastiCache + GCP Monitoring
... (thousands more)
```

**Expert System scores each:**
```
Solution 1: Cost=$194, Latency=7.2ms, Score=127/150 ⭐ BEST
Solution 2: Cost=$203, Latency=8.1ms, Score=118/150
Solution 3: Cost=$215, Latency=6.9ms, Score=115/150
```

## Architecture Pattern Effects

### Monolith
- Fewer components, tighter coupling
- Lower latency (everything co-located)
- Simpler deployment
- Single failure domain

### Microservices  
- More components, loose coupling
- Higher latency (network hops)
- Independent scaling
- Fault isolation

### Event-Driven
- Async communication
- Queue-based messaging
- Eventual consistency
- Complex troubleshooting

The pattern influences:
1. **Component selection** (microservices need load balancers, message queues)
2. **Latency calculations** (more network hops = higher latency)
3. **Cost optimization** (more components = higher cost)

## Constraints Impact

```python
constraints: {
    maxBudget: 5000,      # Filter out expensive solutions
    maxLatency: 100,      # Filter out slow solutions
    requiredProviders: ["AWS", "Azure"],  # Only use these providers
    securityLevel: "high" # Apply security rules
}
```

**CSP applies these as HARD constraints:**
- If cost > $5000 → **REJECT** solution
- If latency > 100ms → **REJECT** solution
- If uses GCP → **REJECT** solution (not in requiredProviders)

## Example Benchmark Comparison

When you run a benchmark, you get:

### CMOv4 Results (Your New System)
```
✓ 19 Feasible Solutions found
⭐ 2 Pareto Optimal solutions
📈 10.5% Coverage Rate

🏆 Best Solution:
   Cost: $194.65/month
   Latency: 7.2ms
   Score: 127/150
   Providers: AWS (60%) + GCP (40%)

📊 Used CMOv3 Thresholds:
   Cost High: $2,800
   Cost Low: $2,000
   Latency Excellent: 10ms
   Single Provider Bonus: +10 points
```

### CMOv3 Baselines (Reference Algorithms)
```
🔬 Baseline Algorithms:
   - Greedy-Cost: $577.73, 9.4ms (cheapest-first approach)
   - Greedy-Latency: $676.37, 9.0ms (fastest-first approach)
   - Genetic Algorithm: $582.73, 9.3ms (evolutionary search)
   - Random Selection: $1,429.47, 9.7ms (random picks)
   - Weighted Sum: $624.10, 9.0ms (balanced approach)
```

**Key Insight:** CMOv4's hybrid CSP + Expert System finds better solutions ($194 vs $577+) because it intelligently combines constraint satisfaction with business rules!

## How to See the Comparison

### Option 1: Open cmov4.html
1. Start servers: `bash frontend/start.sh`
2. Navigate to http://localhost:8080/cmov4.html
3. Select a preset scenario (5, 10, or 15 components)
4. Configure search method (exhaustive, heuristic, random)
5. Click "Run Benchmark"
6. See results showing:
   - **Found Solutions** stats
   - **CMOv4 Optimization** with explanations
   - **CMOv3 Thresholds** used
   - **Best Solution** details
   - **Pareto Frontier** alternatives
   - **CMOv3 Baselines** for comparison

### Option 2: API Call
```bash
curl http://localhost:5055/api/benchmark?scenario=0 | python3 -m json.tool
```

Returns:
```json
{
  "v4": {
    "solutions": [...],
    "pareto_frontier": [...],
    "metrics": {
      "feasible_count": 19,
      "pareto_count": 2,
      "coverage_rate": 0.105
    },
    "explanations": [...],
    "thresholds_used": {...}
  },
  "v3": {
    "Greedy-Cost": {...},
    "Greedy-Latency": {...},
    "Genetic-Algorithm": {...}
  }
}
```

### Option 3: Custom Scenario Builder
1. Switch to "Custom Mode" in cmov4.html
2. Select components (web, compute, database, etc.)
3. Choose architecture pattern (microservices, monolith, event-driven)
4. Select cloud providers
5. Set constraints (budget, latency)
6. Configure CSP search method
7. Run and compare results!

## Key Differences: CMOv3 vs CMOv4

| Feature | CMOv3 | CMOv4 |
|---------|-------|-------|
| **Component Model** | Fixed 15 services | Dynamic component selection |
| **Architecture** | Implicit | Explicit patterns (monolith/microservices/event-driven) |
| **Dependencies** | Not modeled | Explicit relationships |
| **Tech Stack** | Generic | Technology-specific (React/Vue, Python/Go, etc.) |
| **Selection** | All-or-nothing | Smart component selection rules |
| **Optimization** | CSP + Expert System | Same engine, better input modeling |
| **Use Case** | Academic research | Real-world migration planning |

## Benefits of the Component → Architecture Model

1. **Flexibility**: Pick only what you need (5, 10, 15+ components)
2. **Realism**: Model actual dependencies and tech stacks
3. **Scalability**: Add new component types easily
4. **Patterns**: Optimize for specific architecture styles
5. **Comparison**: Benchmark against CMOv3 baselines
6. **Explainability**: See which thresholds/rules were applied
7. **Trade-offs**: Visualize Pareto frontier for alternatives
