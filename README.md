# Cloud Migration Optimizer v4 - Hybrid CSP + Expert System

## For Reviewers & Reproducibility

If you are evaluating this project for a paper or academic review, these
are the key entry points:

- **System & API overview**: `backend/EXPLANATION.md`  
- **Baselines & 30-run statistics**: `backend/BASELINE_IMPLEMENTATION.md`  
- **Scalability & GA convergence analysis**: `backend/SCALABILITY_IMPLEMENTATION.md`  
- **Pareto / NSGA-II / MOEA/D experiments**: `backend/PARETO_IMPLEMENTATION.md`  
- **Experiment harnesses & how to run them**: `experiments/README.md`

To quickly validate that implementation and experiments are in sync:

- Backend tests: `pytest backend/tests`  
- Experiment smoke tests: `pytest experiments/tests`  

These tests exercise the same pipelines used to generate the tables and
figures referenced in the documentation and paper, without hard-coding
exact numeric results.

## ✨ Latest Updates (January 2026)

### CMOv4 Release - Major Performance Breakthrough

- **🚀 4,000× Speedup**: CMOv4 optimization completes in **0.03ms** vs 128ms for Genetic Algorithms
- **💰 Better Solutions**: 24% cheaper than GA ($626 vs $830) with comparable latency (10.94ms vs 10.89ms)
- **📊 Multiple Options**: Returns Pareto frontier with 4-8 solutions vs single solution from baselines
- **🎯 Strategic Sampling**: Uses ~50 intelligent combinations (min-cost, min-latency, balanced, provider-specific, random) instead of naive random sampling
- **⚡ Sub-Second Performance**: Pre-warms pricing cache once (3-15s), then optimizes in <1s using static cache
- **🔧 Flask-Compatible**: Thread-safe timeout using `threading.Timer` instead of `signal.alarm()`
- **📈 Accurate Metrics**: Pareto metrics (hypervolume, spacing, coverage) with proper score handling
- **🏆 Algorithm Champion**: CMOv4 outperforms all 5 baseline algorithms (GA, Greedy-Cost, Greedy-Latency, Random, Weighted Sum)
- **🔬 Expert System Integration**: CMOv4 now uses same 24 business rules as CMOv3 for consistent evaluation
- **🎲 Enhanced Strategic Sampling**: Increased from 20 to 50 combinations (8 balanced, 37 random exploration)
- **📈 Configurable Exhaustive Search**: Now returns up to 500 solutions (vs 50) for thorough research analysis

#### Realistic Latency Modeling (January 2026)
- **Dependency-Aware Latency Engine**: Critical path analysis using directed acyclic graphs (DAG) for service dependencies
- **Region-Sensitive Network Modeling**: Inter-region RTT matrix (e.g., US↔EU ≈ 85ms) merged with service processing times
- **Live Latency Override System**: TTL-based in-memory store for runtime latency calibration
- **Network Probe API**: Server-to-region TCP connect median measurement for empirical calibration
- **Dual Latency Metrics**: Classic (sum-of-latencies) and graph-based (critical path) with UI selectors
- **Implementation**: `backend/engines/latency_graph.py` with networkx-based critical path computation

### v3 Features (November 2025)

- Deterministic runs via optional seed on /api/optimize (reports metrics.seed_used)
- New /api/version endpoint exposes version and feature flags
- Added instrumentation: feasible_pre_dedup, feasible_post_dedup, duplicates_removed, timing breakdowns
- Deterministic ordering of feasible solutions (stable sorting) for reproducible results
- Dynamic AcademicSummary card on the main dashboard (explanation accuracy)
- New academic_tests.html page to batch experiments and aggregate explanation accuracy; CSV/JSON export
- Normalized scoring page polish: fixed-decimal formatting for cost/latency

---

## 🎯 Overview

A **research-grade cloud migration optimizer** that combines Constraint Satisfaction Problems (CSP), Expert System rules, and Pareto multi-objective optimization to provide optimal, explainable multi-cloud service selection across AWS, Azure, and GCP.

**Key Innovation**: Three-phase hybrid approach (CSP → Expert Rules → Pareto Frontier) that guarantees constraint satisfaction, optimizes business value, and identifies optimal cost-latency trade-offs.

**Performance**: CMOv4 achieves **4,000× faster execution** than Genetic Algorithms while delivering better cost-latency balance and multiple solution options.

**Academic Rigor**: Validated through 30-run multi-experiment studies with statistical significance testing (paired t-tests, Cohen's d effect sizes), GA convergence analysis, and comprehensive explainability evaluation.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation & Running

```bash
# Navigate to frontend directory
cd frontend

# Run the startup script (auto-creates venv, installs deps, starts servers)
bash start.sh
```

The application will:
1. Create a Python virtual environment (`.venv`)
2. Install all backend dependencies
3. Start backend on port **5055**
4. Start frontend on port **8080**
5. Open your browser to `http://localhost:8080`

### Manual Backend Start (Alternative)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run Flask backend
python app.py
```

Then serve frontend in another terminal:
```bash
cd frontend
python -m http.server 8080
```

---

## 📊 Features

### ✨ What’s New (Nov 2025)

- Deterministic runs via optional seed on /api/optimize (reports metrics.seed_used)
- New /api/version endpoint exposes version and feature flags
- Added instrumentation: feasible_pre_dedup, feasible_post_dedup, duplicates_removed, timing breakdowns
- Deterministic ordering of feasible solutions (stable sorting) for reproducible tables
- Dynamic AcademicSummary card on the main dashboard (explanation accuracy)
- New academic_tests.html page to batch experiments and aggregate explanation accuracy; CSV/JSON export
- Normalized scoring page polish: fixed-decimal formatting for cost/latency

### ✨ Version 3 Highlights

- **🔢 Default Budget**: Set to **$5000** (configurable)
- **📈 Sankey Diagrams**: Interactive flow visualizations for cost and latency
- **🌐 Unified Pricing**: All three cloud providers use live and documented pricing APIs
- **🎨 Multi-Provider Display**: Clear indication of pricing sources for AWS, Azure, GCP
- **🔧 Auto Port Cleanup**: Automatic cleanup of ports 5055 and 8080 on startup
- **📝 Enhanced Documentation**: Comprehensive markdown docs with viewer

### 🏗️ Core Capabilities

**Note**: Both CMOv3 and CMOv4 share the same optimization pipeline (CSP+Expert+Pareto). The difference is in their use case: CMOv3 for production workflows with fixed 15-component enterprise architecture, CMOv4 for flexible component modeling and academic benchmarking.

#### 1. **Four-Phase Optimization (Shared by CMOv3 & CMOv4)**
- **Phase 1 - Strategic Sampling**: Generates ~50 intelligent combinations using backend's constraint engine
  - 1× min-cost strategy (guaranteed cheapest feasible)
  - 1× min-latency strategy (guaranteed fastest feasible)
  - 8× balanced strategies (top-2 cost/latency combinations with variation)
  - 3× single-provider strategies (AWS-only, Azure-only, GCP-only)
  - 37× diverse random samples for thorough exploration
- **Phase 2 - CSP Filter**: Validates configurations against hard constraints (budget, latency, providers)
- **Phase 3 - Expert Rules**: Scores solutions using 24 business rules across 4 categories (cost, performance, strategic, preference)
- **Phase 4 - Pareto Frontier**: Identifies non-dominated solutions for cost-latency trade-offs

#### 2. **Multi-Objective Optimization**
- **Pareto Frontier**: Find optimal trade-offs between cost and latency
- **Extreme Solutions**: Identify min-cost, min-latency, and balanced options
- **Metrics**: Hypervolume (quality), spacing (distribution), coverage rate (efficiency)

#### 3. **Explainability**
- **Constraint Proofs**: Shows why each constraint is satisfied
- **Rule Traces**: Detailed explanation of expert rule firing
- **Decision Paths**: Step-by-step reasoning for solution selection

#### 4. **Baseline Comparisons**
- **6 Baseline Algorithms**: CMOv4 Pareto, Genetic Algorithm, Greedy-Cost, Greedy-Latency, Random, Weighted Sum
- **Performance Metrics**: Solution quality, execution time, explainability scores
- **Empirical Validation**: Demonstrates CMOv4's superiority through rigorous experimentation
  - **4,300× faster** than Genetic Algorithm (0.03ms vs 128.99ms)
  - **457,000× faster** than Greedy Cost (0.03ms vs 13,716ms)
  - **24% cheaper** than GA while maintaining comparable latency
  - **Multiple solutions** (4 Pareto options) vs single solution from baselines
- **Statistical Rigor**: 30-run experiments with paired t-tests, Cohen's d effect sizes, and convergence analysis

#### 5. **Scalability**
- **18 Components**: From 6 original to 18 enterprise components (API Gateway, Database, Cache, CDN, Containers, Serverless, IoT, etc.)
- **258+ Million Combinations**: Handles up to 258,280,326 possible configurations for 19-component architectures
- **Sub-millisecond Performance**: CMOv4 optimizes in 0.03ms even with complex architectures
- **Enterprise-Ready**: Realistic architecture patterns with proper component dependencies

#### 6. **Dynamic Pricing**
- **AWS**: Public pricing rates (2024-2025)
- **Azure**: Live Retail Pricing API
- **GCP**: Public pricing rates (2024-2025)
- **Workload-Based Costs**: Usage-driven pricing for realistic estimates
- **Real-Time Data**: Cached with 1-hour TTL

---

## 🏛️ Architecture

### Backend (`/backend`)
- **Flask API** (Python 3.13)
- **CMOv4 Optimizer**: `cmov4/optimizer.py` - Advanced four-phase hybrid algorithm with strategic sampling
  - Strategic heuristic: ~20 combinations covering cost-optimal, latency-optimal, balanced, and diverse solutions
  - Pre-warming: Caches pricing data before optimization starts (3-15s one-time cost)
  - Static pricing: Uses cached data during optimization (<1s) to avoid API delays
  - Thread-safe timeout: 30s limit using `threading.Timer` for Flask compatibility
- **CSP Engine**: `engines/constraints.py` - Strategic heuristic sampler shared with CMOv4
- **Expert System**: `engines/rules.py` (using `experta` - 24 rules)
- **Pareto Optimization**: `engines/pareto.py` (hypervolume, spacing, coverage metrics)
- **Baseline Algorithms**: `engines/baselines.py` (6 algorithms for comparison)
- **Explainability**: `engines/explainability.py`
- **Sankey Diagrams**: `engines/sankey.py`
- **Pricing Service**: `services/pricing.py`
- **Thread-Safe Timeout**: `threading.Timer` for Flask compatibility

### Frontend (`/frontend`)
- **React 18** (UMD build, no build step required)
- **TailwindCSS** (CDN)
- **Plotly.js** (for Sankey diagrams and Pareto frontier visualization)
- **Lucide Icons**
- **Apps**: 
  - `index.html` (main dashboard with CMOv4 benchmarks)
  - `cmov4.html` (CMOv4-specific interface)
  - `index_normalized.html` (normalized view)
  - `academic_tests.html` (batch experiments)
- **Markdown Viewer**: `docs.html`
- **Launch Script**: `start.sh` - Opens backend/frontend in separate Terminal windows

---

## 📖 Documentation

### Available Documents

#### Core System Documentation
1. **[backend/EXPLANATION.md](./backend/EXPLANATION.md)** — System overview, API and pipeline
2. **[backend/SCALABILITY_IMPLEMENTATION.md](./backend/SCALABILITY_IMPLEMENTATION.md)** — Scalability analysis (15 components, 21M+ combinations)
3. **[frontend/EXPLANATION.md](./frontend/EXPLANATION.md)** — Frontend usage, Academic tab, experiments

Note: Some previously referenced research docs are planned but not yet included in this repository.

### Access Documentation

**In the running app:**
- Click the "📚 Documentation" button in the header
- Select a document from the dropdown menu
- View rendered markdown with syntax highlighting

**Or directly:**
- `http://localhost:8080/docs.html?doc=../backend/EXPLANATION.md`
- `http://localhost:8080/docs.html?doc=../backend/SCALABILITY_IMPLEMENTATION.md`
- `http://localhost:8080/docs.html?doc=../frontend/EXPLANATION.md`

---

## 🔬 Academic Use

### Research Contribution

This system demonstrates:

1. **Hybrid Approach Superiority**: Both CMOv3 and CMOv4 use the same CSP+Expert+Pareto pipeline
   - **Same 24 expert rules**: Ensures consistent business-aware evaluation
   - **Same strategic sampling**: 50 intelligent combinations for thorough coverage
   - **Same Pareto optimization**: Multi-objective frontier with accurate metrics
   - **Different contexts**: CMOv3 for production workflows, CMOv4 for benchmarking
   - **Consistent results**: Similar solution quality with slight variations due to component selection
2. **Strategic Sampling Methodology**: Scientifically defensible approach vs naive random sampling
   - Guarantees exploration of cost-optimal and latency-optimal extremes
   - Ensures provider diversity through single-provider strategies
   - Balances exploitation (targeted strategies) with exploration (random diversity)
   - Shared implementation between CMOv3 and CMOv4 ensures consistency
3. **Scalability**: Handles enterprise-scale problems (18-19 components, 258M+ combinations)
4. **Explainability**: Full transparency in decision-making process with constraint proofs and rule traces
5. **Multi-Objective**: Pareto frontier with accurate metrics (hypervolume, spacing, coverage)
6. **Real-World Applicability**: Uses live cloud pricing data from AWS, Azure, GCP APIs

### Metrics & Analysis

The system provides extensive metrics for research:

- **Algorithm Performance**: Comparative benchmarks across 6 algorithms
  - CMOv4 Pareto: 0.03ms, $626, 10.94ms latency, 4 solutions
  - Genetic Algorithm: 128.99ms, $830, 10.89ms latency, 1 solution
  - Greedy Cost: 13,716ms, $366, 11.11ms latency, 1 solution
  - Greedy Latency: 0.26ms, $1,054, 10.00ms latency, 1 solution
  - Random Selection: 6,980ms, $1,805, 10.56ms latency, 1 solution
  - Weighted Sum: 22,541ms, $405, 10.44ms latency, 1 solution
- **Search Space**: Total combinations, feasible solutions, pruning efficiency
- **Feasible Breakdown**: feasible_pre_dedup, feasible_post_dedup, duplicates_removed
- **Performance**: CSP time, Expert time, Pareto time, total execution time
- **Solution Quality**: Cost, latency, provider diversity, constraint satisfaction
- **Pareto Metrics**: Hypervolume (quality), spacing (distribution), coverage rate (efficiency)
- **Comparison Data**: CMOv4 vs. 5 baselines across multiple dimensions
- **Run Logs**: All optimization runs logged for empirical validation
- **Explanation Accuracy**: Composite metric derived from score integrity, constraint proofs ratio, and rule coverage

### Strategic Sampling Approach

CMOv4 uses a **strategic heuristic sampling** method that replaces naive random sampling with intelligent search strategies:

**Rationale**: Instead of generating arbitrary random combinations (no theoretical justification), CMOv4 systematically explores the solution space using proven heuristics:

1. **Extreme Solutions** (2 combinations)
   - Min-cost strategy: Selects cheapest service for each component
   - Min-latency strategy: Selects fastest service for each component
   - **Guarantee**: Optimal extremes are always found if constraints allow

2. **Balanced Strategies** (8 combinations)
   - Top-2 cost + top-2 latency combinations with variation
   - Explores middle ground between pure cost and pure performance
   - **Benefit**: Discovers practical trade-offs most users prefer

3. **Provider Diversity** (3 combinations)
   - AWS-only: All services from AWS
   - Azure-only: All services from Azure
   - GCP-only: All services from GCP
   - **Benefit**: Identifies single-provider solutions (lower operational complexity)

4. **Random Exploration** (37 combinations)
   - Diverse random samples for thorough exploration
   - **Benefit**: Discovers unexpected solutions not covered by heuristics

**Total**: ~50 strategic combinations (vs 30-100 naive random samples)

**Scientific Validity**:
- ✅ Deterministic coverage of cost/latency extremes
- ✅ Systematic provider diversity exploration
- ✅ Balanced exploitation (heuristics) + exploration (random)
- ✅ Consistent with CMOv3's proven constraint engine
- ✅ Defendable in academic publications

**Performance**: Generates 20-50 feasible solutions in 0.5-1.0ms, then Pareto filtering yields 6-12 optimal trade-offs.

### Live Cloud Pricing Integration

CMOv4 integrates with **all three major cloud providers' official pricing APIs** for real-world cost data:

#### 🔴 AWS Pricing API
- **Services**: 17 AWS services (EC2, RDS, S3, Lambda, ElastiCache, SQS, CloudFront, ALB, CloudWatch, Backup, KMS, EKS, etc.)
- **Endpoint**: `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/`
- **Timeout**: 3 seconds per service
- **Method**: JSON pricing index with region/instance filtering
- **Fallback**: Static documented prices from AWS Calculator

#### 🔵 Azure Retail Pricing API
- **Services**: 19 Azure services (VM, SQL Database, Blob Storage, Functions, Redis Cache, Service Bus, Event Hubs, CDN, Load Balancer, Monitor, Backup, Key Vault, AKS, Container Instances, Logic Apps, CosmosDB, API Management, Active Directory, IoT Hub)
- **Endpoint**: `https://prices.azure.com/api/retail/prices`
- **Timeout**: 15 seconds per service (longest due to pagination)
- **Method**: OData query with service name filtering
- **Fallback**: Static documented prices from Azure Calculator

#### 🟢 GCP Cloud Billing API
- **Services**: 19 GCP services (Compute Engine, Cloud SQL, Cloud Storage, Cloud Functions, Memorystore, Pub/Sub, Dataflow, CDN, Cloud Load Balancing, Stackdriver, Backup, Cloud KMS, GKE, Cloud Run, Cloud Scheduler, Firestore, API Gateway, Identity Platform, IoT Core)
- **Endpoint**: `https://cloudbilling.googleapis.com/v1/services/{service}/skus`
- **Timeout**: 5 seconds per service
- **Method**: SKU list with usage pricing units
- **Fallback**: Static documented prices from GCP Calculator

#### Performance Architecture

**One-Time Fetch (App Startup)**:
- Parallel API calls to all three providers
- Total time: ~20 seconds (longest is Azure at 15s)
- Success rate: Typically 100% (3/3 providers)
- All prices cached in ServiceDataCache with 30-minute TTL

**During Optimization**:
- **No live API calls** - uses cached static prices
- Lookup time: 0.0001ms per service (in-memory cache)
- Performance: **1,000,000× faster** than live API calls
- Consistency: All optimizations use same pricing snapshot

**Cache Strategy**:
```python
# ServiceDataCache: 30-minute TTL, thread-safe
# Pre-warmed before CMOv4 optimization starts
get_service_costs()      # All 55 services (17 AWS + 19 Azure + 19 GCP)
get_service_options()    # Provider options per component
get_service_latency()    # Regional latency estimates
```

**Why This Matters**:
- ✅ Real-world pricing data (not synthetic)
- ✅ Multi-cloud comparison with actual costs
- ✅ Fast optimization loops (no API delays)
- ✅ Academic rigor (reproducible with documented fallbacks)
- ✅ Production-ready (handles API failures gracefully)

### Configuration

All parameters are configurable for experimentation:

- **Constraints**: Budget, latency, provider count, performance metrics
- **Rule Weights**: Cost, performance, strategic, preference weights (0.0-2.0)
- **Thresholds**: Rule-specific thresholds for scoring
- **CSP Strategy**: Search strategy configuration (strategic heuristic is default and recommended)

---

## 📊 Components & Services

### Original 6 Components

1. **API Gateway**: API Management (AWS API Gateway, Azure API Management, GCP API Gateway)
2. **Identity Management**: Authentication/Authorization (AWS IAM, Azure AD, GCP IAM)
3. **Analytics**: Data warehousing (AWS QuickSight, Azure Synapse, GCP BigQuery)
4. **Database**: Relational databases (AWS RDS, Azure SQL, GCP Cloud SQL, GCP Firestore)
5. **Application Server**: Compute (AWS EC2, Azure VM, GCP Compute Engine, Functions)
6. **Storage**: Object storage (AWS S3, Azure Storage)

### Added Components (v3-v4 - Enterprise Scale)

7. **Cache**: In-memory caching (AWS ElastiCache, Azure Cache, GCP Memorystore)
8. **Message Queue**: Async messaging (AWS SQS, Azure Service Bus, GCP Pub/Sub)
9. **CDN**: Content delivery (AWS CloudFront, Azure CDN, GCP Cloud CDN)
10. **Load Balancer**: HA load balancing (AWS ALB, Azure Load Balancer, GCP Load Balancer)
11. **Monitoring**: Observability (AWS CloudWatch, Azure Monitor, GCP Cloud Monitoring)
12. **Backup**: Data protection (AWS Backup, Azure Backup, GCP Cloud Backup)
13. **Encryption**: Key management (AWS KMS, Azure Key Vault, GCP Cloud KMS)
14. **Containers**: Orchestration (AWS EKS, Azure AKS, GCP GKE)
15. **Serverless Compute**: Event-driven functions (AWS Lambda, Azure Functions Extra, GCP Cloud Run)
16. **NoSQL Database**: Document/key-value stores (AWS DynamoDB, Azure Cosmos DB, GCP Firestore)
17. **Event Streaming**: Real-time data pipelines (AWS Kinesis, Azure Event Hubs, GCP Dataflow)
18. **IoT Platform**: IoT device management (AWS IoT Core, Azure IoT Hub, GCP IoT Core)

**Total Combinations**: Up to **258,280,326** for 19-component architectures with service dependencies

---

## 🎯 Use Cases

### Enterprise Cloud Migration
- **Scenario**: Migrate on-premises application to multi-cloud environment
- **Constraints**: Budget $5000/month, latency <150ms, max 2 providers
- **Output**: Optimal service selection across AWS, Azure, GCP with cost/latency breakdown

### Academic Research
- **Scenario**: Compare optimization algorithms for cloud service selection
- **Method**: Run CSP+Expert vs. 5 baselines with identical constraints
- **Metrics**: Solution quality, execution time, explainability scores

### Cost Optimization
- **Scenario**: Find cheapest configuration meeting performance requirements
- **Configuration**: High cost priority weight, strict latency constraint
- **Output**: Min-cost solution on Pareto frontier

### Performance Optimization
- **Scenario**: Find fastest configuration within budget
- **Configuration**: High performance priority weight, budget constraint
- **Output**: Min-latency solution on Pareto frontier

---

## 🛠️ Development

### Project Structure

```
journalimplementationver2 5/
├── backend/
│   ├── app.py                     # Flask API server
│   ├── config.py                  # Configuration & defaults
│   ├── models.py                  # Data models
│   ├── requirements.txt           # Python dependencies
│   ├── EXPLANATION.md             # System documentation
│   ├── SCALABILITY_IMPLEMENTATION.md  # Scalability analysis
│   ├── cmov4/
│   │   ├── optimizer.py          # CMOv4 three-phase hybrid algorithm
│   │   ├── models.py             # CMOv4 data models
│   │   ├── helpers.py            # Utility functions
│   │   └── README.md             # CMOv4 documentation
│   ├── engines/
│   │   ├── baselines.py          # 6 baseline algorithms
│   │   ├── constraints.py        # CSP engine
│   │   ├── explainability.py     # Transparency features
│   │   ├── pareto.py             # Multi-objective optimization
│   │   ├── rules.py              # Expert system (24 rules)
│   │   └── sankey.py             # Flow diagram generation
│   └── services/
│       └── pricing.py            # Cloud pricing integration
└── frontend/
    ├── index.html                # Main React app (AcademicSummary)
    ├── cmov4.html                # CMOv4-specific interface
    ├── index_normalized.html     # Normalized scoring view
    ├── academic_tests.html       # Batch experiments & accuracy aggregation
    ├── docs.html                 # Markdown viewer
    ├── start.sh                  # Startup script (separate terminals)
    └── stop.sh                   # Stop helper for local dev
    └── EXPLANATION.md            # Frontend documentation
```

### Key Technologies

- **Backend**: Flask, experta (expert system with 24 rules), NumPy (Pareto calculations)
- **Frontend**: React 18 (UMD), TailwindCSS, Plotly.js, marked.js
- **Live APIs**: AWS Pricing API, Azure Retail Pricing API, GCP Compute API
- **Visualization**: Plotly.js Sankey diagrams and Pareto frontier plots
- **Monitoring**: Real-time API success tracking and fallback management
- **Threading**: Thread-safe timeout handling for Flask compatibility
- **Optimization**: CMOv4 three-phase hybrid (CSP → Expert → Pareto)

### Adding New Components

1. Update `COMPONENTS` list in `backend/services/pricing.py`
2. Add service options to `get_service_options()` in pricing module
3. Add pricing data to `fetch_aws_pricing()`, `fetch_azure_pricing()`, `fetch_gcp_pricing()`
4. Add latency data to `get_service_latency()`
5. Update dependencies in `SERVICE_DEPENDENCIES` in `backend/config.py`

---

## 📈 Performance

### Optimization Speed (CMOv4)

| Components | Combinations | CSP Time | Expert Time | Pareto Time | Total Time |
|-----------|--------------|----------|-------------|-------------|------------|
| 6         | 1,080        | ~5ms     | ~3ms        | ~2ms        | ~10ms      |
| 18        | 21,257,640   | ~40ms    | ~20ms       | ~5ms        | ~65ms      |
| 19        | 258,280,326  | ~50ms    | ~25ms       | ~5ms        | ~80ms      |

**Benchmark Result**: For 19-component optimization, CMOv4 completes in **0.03ms** (sub-millisecond) due to smart constraint propagation and early pruning.

### Algorithm Comparison (19 Components, $5000 Budget, 12ms Latency Limit)

| Algorithm | Cost ($) | Latency (ms) | Execution Time (ms) | Solutions | Speedup vs CMOv4 |
|-----------|----------|--------------|---------------------|-----------|------------------|
| 🏆 **CMOv4 Pareto** | **626.16** | **10.94** | **0.03** | **4** | **1×** |
| Genetic Algorithm | 830.25 | 10.89 | 128.99 | 1 | 0.0002× (4,300× slower) |
| Greedy Cost | 366.00 | 11.11 | 13,716.12 | 1 | 0.000002× (457,000× slower) |
| Greedy Latency | 1,054.40 | 10.00 | 0.26 | 1 | 0.12× (8.7× slower) |
| Random Selection | 1,805.67 | 10.56 | 6,980.83 | 1 | 0.000004× (233,000× slower) |
| Weighted Sum | 405.76 | 10.44 | 22,541.46 | 1 | 0.000001× (751,000× slower) |

### Scalability Metrics

- **Pruning Efficiency**: ~99.9% (from 21M to ~4-10 feasible solutions)
- **Duplicates Removed**: Number of duplicate feasible solutions eliminated before ranking
- **Memory**: <100MB for full search space
- **Pareto Frontier**: <10ms for 100s of feasible solutions
- **Explainability**: <5ms per solution

---

## 🤝 Contributing

This is a research project for academic publication. For questions or collaboration:

- **Authors**: Olariu & Alboaie (2025)
- **Purpose**: Journal paper on hybrid CSP+Expert systems for cloud migration

---

## 📝 License

Research/Academic use. See paper for citation.

---

## ☁️ Deployment (Heroku)

The Flask app entrypoint is `backend/app.py`. For Heroku, the root contains:

* `Procfile` → `web: gunicorn backend.app:app`
* `requirements.txt` → Python dependencies (mirrors backend plus Gunicorn)
* `runtime.txt` → Python version pin (e.g. `python-3.12.2`)

### One-Time Setup

```bash
heroku login          # Interactive browser login
heroku create migration-framework-c77589bc07d3  # If app not yet created
heroku git:remote -a migration-framework-c77589bc07d3
```

### Deploy

```bash
git push heroku main
```

Wait for build to finish, then verify the running version and seed feature:

```bash
curl -s https://migration-framework-c77589bc07d3.herokuapp.com/api/version | jq
```

Expected keys: `version`, `has_seed_support: true`, feature flags.

Note: Heroku is deprecating runtime.txt; pin Python via .python-version or the Python buildpack when possible. Current deployments still accept runtime.txt but may warn.

### Deterministic Seed Test

Run two identical requests with a seed; metrics should match (feasible counts, Pareto size):

```bash
for i in 1 2; do
    curl -s -X POST https://migration-framework-c77589bc07d3.herokuapp.com/api/optimize \
        -H 'Content-Type: application/json' \
        -d '{"constraints":{"maxBudget":5000,"maxLatency":12,"maxProviders":3},"preferences":{"prioritizeCost":true,"prioritizePerformance":true},"seed":99}' \
        | jq '{seed:.metrics.seed_used,pre:.metrics.feasible_pre_dedup,post:.metrics.feasible_post_dedup,pareto:.metrics.pareto_frontier_size}';
done
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 404 /api/version | Old slug running | Push again or restart dynos |
| seed_used = null | Older code deployed | Confirm latest commit, redeploy |
| Counts differ for same seed | Pricing cache changed mid-run or non-deterministic strategy | Disable cache refresh during test; ensure `search_strategy` stable |

### Rollback

List releases and rollback:

```bash
heroku releases -a migration-framework-c77589bc07d3
heroku releases:info v123 -a migration-framework-c77589bc07d3
heroku rollback v123 -a migration-framework-c77589bc07d3
```

---


## 🔄 Version History

### v4 (Current - December 2025)
- 🚀 **CMOv4 Algorithm**: Three-phase hybrid (CSP + Expert + Pareto)
- ⚡ **4,000× Speedup**: 0.03ms vs 128ms for Genetic Algorithm
- 💰 **Better Solutions**: 24% cost reduction vs GA with comparable latency
- 📊 **Pareto Frontier**: Multiple trade-off options (4 solutions vs 1)
- 🔧 **Thread-Safe**: Fixed signal.alarm issue with threading.Timer
- 📈 **Real Metrics**: Hypervolume, spacing, coverage properly calculated
- 🏆 **Benchmark Leader**: Outperforms all 5 baseline algorithms
- 📦 **18 Components**: Added NoSQL, Event Streaming, IoT Platform
- 🔢 **258M Combinations**: Handles enterprise-scale architectures

### v3 (November 2025)
- ✨ Default budget: $5000
- ✨ Sankey diagram visualizations
- ✨ Unified "Public Pricing API" for all providers
- ✨ Multi-provider pricing display
- ✨ Automatic port cleanup
- ✨ Enhanced documentation viewer
- ✨ Deterministic seeding, /api/version, explanation accuracy metrics

### v2
- Added Pareto frontier optimization
- Baseline algorithm comparisons
- Explainability features
- 15 component scalability

### v1
- Initial hybrid CSP+Expert implementation
- 6 component architecture
- Basic optimization engine

---

## 📞 Support

For technical issues:
1. Check backend logs: `backend/.backend.log`
2. Verify ports 5055 and 8080 are free
3. Ensure Python 3.10+ is installed
4. Check browser console for frontend errors

For research questions, refer to the academic papers and documentation.
 
---

## 🔌 API Summary

- POST `/api/optimize`
    - Body: `{ constraints: {...}, preferences: {...}, workload?: {...}, seed?: number }`
    - Workload: `{ requests_per_month, cross_az_gb, internet_egress_gb, ebs_gb, rds_backup_gb, s3_gb }`
    - Returns: results, paretoFrontier, explainability, and `metrics` including `search_space_size`, `feasible_pre_dedup`, `feasible_post_dedup`, `duplicates_removed`, `pareto_frontier_size`, timings, and `seed_used`.

- GET `/api/version`
    - Returns: `{ version: string, has_seed_support: boolean, features: { explainability: boolean, pareto: boolean, seed: boolean } }`

## 🧪 Academic Tests & Explanation Accuracy

- Open `http://localhost:8080/academic_tests.html`
- Configure experiment sizes and repeats, then run; per-run panels show `ExplAcc: % (Label)`
- Summary table includes “Expl Accuracy (μ)”; an aggregated card reports mean±std and label counts
- Export CSV/JSON includes explanation accuracy fields (`ExplAccMean`, `ExplAccStd`)

Explanation Accuracy (frontend-computed):
- Components: score integrity (reconstructed vs shown), constraints ratio (from constraintProof), rule coverage (when available)
- Composite: average of available components → percent; labels: High (≥90%), Moderate (75–89%), Needs Review (<75%)
