# NEWS.md

## January 2026

### Realistic Latency Modeling
- **Dependency-Aware Latency Engine**: Implemented critical path analysis using directed acyclic graphs (DAG) for service dependencies
- **Region-Sensitive Network Modeling**: Inter-region RTT matrix merged with service processing times
- **Live Latency Override System**: TTL-based in-memory store for runtime latency calibration
- **Network Probe API**: Server-to-region TCP connect median measurement endpoint
- **Dual Latency Metrics**: Classic (sum-of-latencies) and graph-based (critical path) with UI selectors
- **UI Integration**: Both CMOv3 and CMOv4 display network latency status cards on load

### Experimental Rigor
- **30-Run Multi-Experiments**: Statistical validation with mean ± std dev across all algorithms
- **GA Convergence Analysis**: Empirical justification of baseline parameters
- **Statistical Significance Testing**: Paired t-tests and Cohen's d effect sizes
- **Reproducibility**: Fixed seeds and documented experimental harness

## November 2025

- Automated experiment pipeline now runs all baselines and NSGA-II with comprehensive metrics.
- Results, figures, and tables are dynamically updated to reflect current implementation.
- Explanations now include direct links to cloud provider pricing APIs for full transparency.
- Frontend clearly communicates optimization results with detailed explanations.
- NSGA-II results are integrated into comparative analysis.
- All code and data dependencies are documented for reproducibility.

---

For more details, see the documentation in the experiments/ directory and backend/ documentation files.
