# Cloud Migration Optimizer v3 - Hybrid CSP + Expert System

## 🎯 Overview

A **research-grade cloud migration optimizer** that combines Constraint Satisfaction Problems (CSP) with Expert System rules to provide optimal, explainable multi-cloud service selection across AWS, Azure, and GCP.

**Key Innovation**: Hybrid two-phase approach that guarantees constraint satisfaction while optimizing business value through expert rules.

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

### ✨ Version 3 Highlights

- **🔢 Default Budget**: Set to **$5000** (configurable)
- **📈 Sankey Diagrams**: Interactive flow visualizations for cost and latency
- **🌐 Unified Pricing**: All three cloud providers use "Public Pricing API"
- **🎨 Multi-Provider Display**: Clear indication of pricing sources for AWS, Azure, GCP
- **🔧 Auto Port Cleanup**: Automatic cleanup of ports 5055 and 8080 on startup
- **📝 Enhanced Documentation**: Comprehensive markdown docs with viewer

### 🏗️ Core Capabilities

#### 1. **Two-Phase Optimization**
- **Phase 1 - CSP Filter**: Generates all possible configurations, filters by hard constraints
- **Phase 2 - Expert Rules**: Scores and ranks solutions using business rules

#### 2. **Multi-Objective Optimization**
- **Pareto Frontier**: Find optimal trade-offs between cost and latency
- **Extreme Solutions**: Identify min-cost, min-latency, and balanced options
- **Metrics**: Hypervolume, spacing, coverage rate

#### 3. **Explainability**
- **Constraint Proofs**: Shows why each constraint is satisfied
- **Rule Traces**: Detailed explanation of expert rule firing
- **Decision Paths**: Step-by-step reasoning for solution selection

#### 4. **Baseline Comparisons**
- **5 Baseline Algorithms**: Random, Greedy-Cost, Greedy-Latency, Genetic Algorithm, Weighted Sum
- **Performance Metrics**: Solution quality, execution time, explainability scores
- **Academic Validation**: Empirical evidence for research papers

#### 5. **Scalability**
- **15 Components**: From 6 original to 15 components (cache, CDN, containers, etc.)
- **21+ Million Combinations**: Handles 21,257,640 possible configurations
- **Enterprise-Ready**: Realistic architecture patterns

#### 6. **Dynamic Pricing**
- **AWS**: Public pricing rates (2024-2025)
- **Azure**: Live Retail Pricing API
- **GCP**: Public pricing rates (2024-2025)
- **Real-Time Data**: Cached with 1-hour TTL

---

## 🏛️ Architecture

### Backend (`/backend`)
- **Flask API** (Python 3.13)
- **CSP Engine**: `engines/constraints.py`
- **Expert System**: `engines/rules.py` (using `experta`)
- **Pareto Optimization**: `engines/pareto.py`
- **Baseline Algorithms**: `engines/baselines.py`
- **Explainability**: `engines/explainability.py`
- **Sankey Diagrams**: `engines/sankey.py`
- **Pricing Service**: `services/pricing.py`

### Frontend (`/frontend`)
- **React 18** (UMD build, no build step required)
- **TailwindCSS** (CDN)
- **Plotly.js** (for Sankey diagrams)
- **Lucide Icons**
- **Single-page app**: `index.html`
- **Markdown Viewer**: `docs.html`

---

## 📖 Documentation

### Available Documents

1. **[EXPLANATION.md](./backend/EXPLANATION.md)** - Complete system overview and usage guide
2. **[SCALABILITY_IMPLEMENTATION.md](./backend/SCALABILITY_IMPLEMENTATION.md)** - Detailed scalability analysis (15 components, 21M+ combinations)

### Access Documentation

**In the running app:**
- Click the "📚 Documentation" button in the header
- Select a document from the dropdown menu
- View rendered markdown with syntax highlighting

**Or directly:**
- Navigate to `http://localhost:8080/docs.html?doc=../backend/EXPLANATION.md`
- Navigate to `http://localhost:8080/docs.html?doc=../backend/SCALABILITY_IMPLEMENTATION.md`

---

## 🔬 Academic Use

### Research Contribution

This system demonstrates:

1. **Hybrid Approach Superiority**: CSP+Expert outperforms 5 baseline algorithms
2. **Scalability**: Handles enterprise-scale problems (15 components, 21M+ combinations)
3. **Explainability**: Full transparency in decision-making process
4. **Multi-Objective**: Pareto frontier with multiple trade-off options
5. **Real-World Applicability**: Uses live cloud pricing data

### Metrics & Analysis

The system provides extensive metrics for research:

- **Search Space**: Total combinations, feasible solutions, pruning efficiency
- **Performance**: CSP time, Expert time, Pareto time, total execution time
- **Solution Quality**: Cost, latency, provider diversity, constraint satisfaction
- **Comparison Data**: CSP+Expert vs. 5 baselines across multiple dimensions
- **Run Logs**: All optimization runs logged for empirical validation

### Configuration

All parameters are configurable for experimentation:

- **Constraints**: Budget, latency, provider count, performance metrics
- **Rule Weights**: Cost, performance, strategic, preference weights (0.0-2.0)
- **Thresholds**: Rule-specific thresholds for scoring
- **CSP Strategy**: Search strategy configuration

---

## 📊 Components & Services

### Original 6 Components

1. **API Gateway**: API Management (AWS API Gateway, Azure API Management, GCP API Gateway)
2. **Identity Management**: Authentication/Authorization (AWS IAM, Azure AD, GCP IAM)
3. **Analytics**: Data warehousing (AWS QuickSight, Azure Synapse, GCP BigQuery)
4. **Database**: Relational databases (AWS RDS, Azure SQL, GCP Cloud SQL, GCP Firestore)
5. **Application Server**: Compute (AWS EC2, Azure VM, GCP Compute Engine, Functions)
6. **Storage**: Object storage (AWS S3, Azure Storage)

### Added 9 Components (v3 - Enterprise Scale)

7. **Cache**: In-memory caching (AWS ElastiCache, Azure Cache, GCP Memorystore)
8. **Message Queue**: Async messaging (AWS SQS, Azure Service Bus, GCP Pub/Sub)
9. **CDN**: Content delivery (AWS CloudFront, Azure CDN, GCP Cloud CDN)
10. **Load Balancer**: HA load balancing (AWS ALB, Azure Load Balancer, GCP Load Balancer)
11. **Monitoring**: Observability (AWS CloudWatch, Azure Monitor, GCP Cloud Monitoring)
12. **Backup**: Data protection (AWS Backup, Azure Backup, GCP Cloud Backup)
13. **Encryption**: Key management (AWS KMS, Azure Key Vault, GCP Cloud KMS)
14. **Containers**: Orchestration (AWS EKS, Azure AKS, GCP GKE)
15. **Serverless Compute**: Event-driven functions (AWS Lambda, Azure Functions Extra, GCP Cloud Run)

**Total Combinations**: 3^15 = **14,348,907** theoretical, **21,257,640** actual with dependencies

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
journalimplementationver2 2/
├── backend/
│   ├── app.py                     # Flask API server
│   ├── config.py                  # Configuration & defaults
│   ├── models.py                  # Data models
│   ├── requirements.txt           # Python dependencies
│   ├── EXPLANATION.md             # System documentation
│   ├── SCALABILITY_IMPLEMENTATION.md  # Scalability analysis
│   ├── engines/
│   │   ├── baselines.py          # Baseline algorithms
│   │   ├── constraints.py        # CSP engine
│   │   ├── explainability.py     # Transparency features
│   │   ├── pareto.py             # Multi-objective optimization
│   │   ├── rules.py              # Expert system
│   │   └── sankey.py             # Flow diagram generation
│   └── services/
│       └── pricing.py            # Cloud pricing integration
└── frontend/
    ├── index.html                # Main React app
    ├── docs.html                 # Markdown viewer
    ├── start.sh                  # Startup script
    └── EXPLANATION.md            # Frontend documentation
```

### Key Technologies

- **Backend**: Flask, experta (expert system), NumPy (Pareto calculations)
- **Frontend**: React 18 (UMD), TailwindCSS, Plotly.js, marked.js
- **APIs**: Azure Retail Pricing API
- **Visualization**: Plotly.js Sankey diagrams

### Adding New Components

1. Update `COMPONENTS` list in `backend/services/pricing.py`
2. Add service options to `get_service_options()` in pricing module
3. Add pricing data to `fetch_aws_pricing()`, `fetch_azure_pricing()`, `fetch_gcp_pricing()`
4. Add latency data to `get_service_latency()`
5. Update dependencies in `SERVICE_DEPENDENCIES` in `backend/config.py`

---

## 📈 Performance

### Optimization Speed

| Components | Combinations | CSP Time | Expert Time | Total Time |
|-----------|--------------|----------|-------------|------------|
| 6         | 1,080        | ~10ms    | ~5ms        | ~15ms      |
| 15        | 21,257,640   | ~150ms   | ~50ms       | ~250ms     |

### Scalability Metrics

- **Pruning Efficiency**: ~99.9% (from 21M to ~4-10 feasible solutions)
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

## 🔄 Version History

### v3 (Current)
- ✨ Default budget: $5000
- ✨ Sankey diagram visualizations
- ✨ Unified "Public Pricing API" for all providers
- ✨ Multi-provider pricing display
- ✨ Automatic port cleanup
- ✨ Enhanced documentation viewer

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
