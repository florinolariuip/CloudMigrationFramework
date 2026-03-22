# How to See the Benchmark Comparison

## Quick Start (3 Steps)

### 1. Start the Servers
```bash
cd "/Users/florinolariu/Downloads/journalimplementationver2 3"
bash frontend/start.sh
```

This will:
- ✅ Start backend on http://localhost:5055
- ✅ Start frontend on http://localhost:8080
- ✅ Open browser automatically

### 2. Navigate to CMOv4
Click on: **"CMOv4 Benchmarking"** button
Or go directly to: http://localhost:8080/cmov4.html

### 3. Run a Benchmark

#### Option A: Preset Scenario (Recommended for first time)
1. **Select a scenario** from the list:
   - 📦 **5 Components** (monolith) - Quick test
   - 📦 **10 Components** (microservices) - Medium complexity
   - 📦 **15 Components** (event-driven) - Full test

2. **Configure search method:**
   ```
   ⚙️ CSP Search Configuration
   Search Strategy: [Exhaustive Search ▼]  (or heuristic/random)
   Sample Size: 1000  (for random sampling)
   ```

3. **Click "Run Benchmark"**

4. **See Results!** 👇

## What You'll See

### Part 1: Benchmark Header
```
┌─────────────────────────────────────────────────────────┐
│ 📊 CMOv4 vs CMOv3 Benchmark Results                    │
│ Comparing CMOv4 dynamic optimization with               │
│ CMOv3 baseline algorithms                               │
└─────────────────────────────────────────────────────────┘
```

### Part 2: Found Solutions Summary
```
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ ✓ Feasible       │ │ ⭐ Pareto        │ │ 📈 Coverage      │
│   Solutions      │ │   Optimal        │ │   Rate           │
│                  │ │                  │ │                  │
│     19           │ │     2            │ │    10.5%         │
│                  │ │                  │ │                  │
│ Meeting          │ │ Non-dominated    │ │ Of feasible      │
│ constraints      │ │ solutions        │ │ space explored   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### Part 3: Optimization Process (Blue Box 📊)
```
┌─────────────────────────────────────────────────────────┐
│ 📊 Optimization Process                                 │
├─────────────────────────────────────────────────────────┤
│ Generated 180 total combinations                        │
│ Found 19 feasible solutions meeting constraints         │
│ Evaluated 19 solutions using expert rules              │
│ Identified 2 Pareto-optimal solutions                  │
│                                                         │
│ Best solution: $194.65/month, 7.2ms latency           │
│ Expert score: 127/150                                  │
│                                                         │
│ CMOv3 thresholds applied:                              │
│ - Cost high threshold: $2800                           │
│ - Cost low threshold: $2000                            │
│ - Latency excellent threshold: 10ms                    │
│ - Latency poor threshold: 11.5ms                       │
│ - Single provider bonus: +10 points                    │
└─────────────────────────────────────────────────────────┘
```

### Part 4: Expert System Thresholds (Green Box ⚙️)
```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Expert System Thresholds (from CMOv3)               │
├─────────────────────────────────────────────────────────┤
│ Cost High:     $2,800    Cost Low:        $2,000       │
│ Latency        10ms      Latency Poor:    11.5ms       │
│ Excellent:                                              │
│ Single Provider Bonus:   +10 points                     │
└─────────────────────────────────────────────────────────┘
```

### Part 5: Recommended Solution (Yellow Box 🏆)
```
┌─────────────────────────────────────────────────────────┐
│ 🏆 Recommended Solution                                 │
├─────────────────────────────────────────────────────────┤
│ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐│
│ │ Monthly Cost   │ │ Avg Latency    │ │ Expert Score ││
│ │                │ │                │ │              ││
│ │  $194.65       │ │   7.2ms        │ │  127/150     ││
│ └────────────────┘ └────────────────┘ └──────────────┘│
│                                                         │
│ Configuration Details:                                  │
│ ┌───────────────────────────────────────────────────┐  │
│ │ api_gateway:          AWS API Gateway             │  │
│ │ application_server:   AWS EC2                     │  │
│ │ database:             AWS RDS                     │  │
│ │ cache:                GCP Memorystore             │  │
│ │ monitoring:           AWS CloudWatch              │  │
│ │ ...                   ...                         │  │
│ └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Part 6: Pareto Frontier (Purple Box 📈)
```
┌─────────────────────────────────────────────────────────┐
│ 📈 Pareto Frontier - Alternative Trade-offs             │
├─────────────────────────────────────────────────────────┤
│ 2 non-dominated solutions offering different           │
│ cost/latency trade-offs                                 │
│                                                         │
│ ┌──────┬──────────┬──────────┬───────────┬──────────┐ │
│ │ Rank │   Cost   │ Latency  │ Providers │  Score   │ │
│ ├──────┼──────────┼──────────┼───────────┼──────────┤ │
│ │  1   │ $194.65  │  7.2ms   │     2     │   127    │ │
│ │  2   │ $203.45  │  6.8ms   │     2     │   118    │ │
│ └──────┴──────────┴──────────┴───────────┴──────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Part 7: CMOv3 Baseline Algorithms (Gray Box 🔬)
**THIS IS WHERE YOU SEE THE COMPARISON!**

```
┌─────────────────────────────────────────────────────────┐
│ 🔬 CMOv3 Baseline Algorithm Results                     │
├─────────────────────────────────────────────────────────┤
│ {                                                       │
│   "Greedy-Cost": {                                      │
│     "algorithm": "Greedy-Cost",                         │
│     "solution": {                                       │
│       "cost": 577.73,              ← MORE EXPENSIVE     │
│       "latency": 9.4,              ← SLOWER             │
│       "providers": 2,                                   │
│       "configuration": {...}                            │
│     },                                                  │
│     "execution_time_ms": 1740.87                        │
│   },                                                    │
│   "Greedy-Latency": {                                   │
│     "cost": 676.37,                ← EVEN MORE $$$      │
│     "latency": 9.0,                ← STILL SLOWER       │
│     ...                                                 │
│   },                                                    │
│   "Genetic-Algorithm": {                                │
│     "cost": 582.73,                                     │
│     "latency": 9.33,                                    │
│     ...                                                 │
│   },                                                    │
│   "Random": {                                           │
│     "cost": 1429.47,               ← WORST!             │
│     "latency": 9.67,                                    │
│     ...                                                 │
│   },                                                    │
│   "Weighted-Sum": {                                     │
│     "cost": 624.10,                                     │
│     "latency": 9.0,                                     │
│     ...                                                 │
│   }                                                     │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

## The Comparison Insight! 💡

### CMOv4 (Your Hybrid System)
```
✅ Best Solution: $194.65, 7.2ms, Score: 127
✅ Uses CSP + Expert System intelligently
✅ Finds Pareto-optimal solutions
✅ Explainable with thresholds shown
```

### CMOv3 Baselines (Reference)
```
❌ Greedy-Cost:      $577.73  (3x more expensive!)
❌ Greedy-Latency:   $676.37  (3.5x more expensive!)
❌ Genetic Algorithm: $582.73  (3x more expensive!)
❌ Random:           $1,429.47 (7x more expensive!)
❌ Weighted-Sum:     $624.10  (3.2x more expensive!)
```

**Winner: CMOv4 by a huge margin!** 🎉

The hybrid CSP + Expert System approach:
- Finds solutions **3-7x cheaper** than baseline algorithms
- Achieves **better latency** (7.2ms vs 9ms+)
- Provides **explainable results** with expert scores
- Shows **alternative trade-offs** via Pareto frontier

## Custom Scenario Testing

Want to test your own architecture?

1. **Switch to "Custom Mode"**
2. **Select components you need:**
   ```
   ☑️ Web (API Gateway)
   ☑️ Compute (App Server)
   ☑️ Database
   ☑️ Cache
   ☑️ Monitoring
   ☑️ Message Queue
   ... (15 types available)
   ```

3. **Choose architecture pattern:**
   ```
   ⚪ Monolith
   ⦿ Microservices  ← (selected)
   ⚪ Event-Driven
   ```

4. **Select providers:**
   ```
   ☑️ AWS
   ☑️ Azure
   ☑️ GCP
   ```

5. **Set constraints:**
   ```
   Max Budget: $10,000
   Max Latency: 150ms
   ```

6. **Configure CSP search:**
   ```
   Strategy: Exhaustive
   Sample Size: 1000
   ```

7. **Run and compare!**

## Understanding the Results

### Feasible Solutions
**All** combinations that meet your hard constraints:
- Cost ≤ maxBudget
- Latency ≤ maxLatency
- Uses only requiredProviders

### Pareto Optimal
**Non-dominated** solutions where:
- No other solution is both cheaper AND faster
- Represents the best cost/latency trade-offs
- These are your "shortlist" options

### Expert Score (out of 150 points)
Combines multiple factors:
- **Cost score** (based on thresholds from CMOv3)
- **Latency score** (based on thresholds from CMOv3)
- **Multi-cloud bonus** (using multiple providers = +10)
- **Security score** (encryption, monitoring)
- **Reliability score** (redundancy, backup)

### CMOv3 Thresholds Applied
Shows exactly which rules from CMOv3 were used:
- `cost_high_threshold: $2,800` - expensive solutions penalized
- `cost_low_threshold: $2,000` - cheap solutions rewarded
- `latency_excellent_threshold: 10ms` - fast solutions rewarded
- `latency_poor_threshold: 11.5ms` - slow solutions penalized
- `single_provider_bonus: +10` - multi-cloud encouraged

## Troubleshooting

### "No feasible solutions found"
- **Relax constraints**: Increase budget or latency limits
- **Change search strategy**: Try "random_sample" with larger sample size
- **Select fewer components**: Fewer components = more likely to find solutions

### "Only 1 Pareto optimal solution"
- **This is normal** for very constrained problems
- The single solution dominates all others
- Try different constraint values to see more alternatives

### "CMOv3 baselines show error"
- Check backend logs: `ps aux | grep python`
- Restart backend: `cd backend && python3 -m backend.app`
- Verify CMOv3 services data loaded

### Backend not responding
```bash
# Check if backend is running
lsof -i:5055

# Restart backend
cd backend
python3 -m backend.app &

# Test endpoint
curl http://localhost:5055/api/benchmark?scenario=0
```

## API Testing (Advanced)

Test the API directly to see raw JSON:

```bash
# Preset scenario
curl -s http://localhost:5055/api/benchmark?scenario=0 | python3 -m json.tool

# Custom scenario
curl -X POST http://localhost:5055/api/benchmark/dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": {
      "architecture": {
        "components": [
          {"name": "Web", "type": "web"},
          {"name": "App", "type": "compute"},
          {"name": "DB", "type": "database"}
        ],
        "architecture_pattern": "microservices"
      },
      "constraints": {
        "maxBudget": 5000,
        "maxLatency": 100,
        "requiredProviders": ["AWS", "Azure"]
      },
      "config": {
        "search_strategy": "exhaustive",
        "sample_size": 1000
      }
    }
  }' | python3 -m json.tool
```

## Next Steps

1. **Run multiple scenarios** - compare 5, 10, 15 components
2. **Try different search strategies** - see performance impact
3. **Test custom architectures** - model your real migrations
4. **Analyze Pareto frontiers** - understand trade-offs
5. **Compare with baselines** - validate CMOv4's superiority
6. **Export results** - save for journal paper data

## Questions?

- **What are components?** → Building blocks of your architecture (web, compute, DB)
- **What is architecture?** → Overall design pattern (monolith vs microservices)
- **Why map to CMOv3?** → Reuse proven CSP + Expert System optimization
- **What's a Pareto frontier?** → Set of best trade-off solutions (no solution dominates another)
- **Why is CMOv4 better?** → Combines intelligent search (CSP) with business rules (Expert System)
- **How do I compare?** → Look at "CMOv3 Baseline Algorithm Results" section!

See `ARCHITECTURE_LOGIC.md` for detailed technical explanation.
