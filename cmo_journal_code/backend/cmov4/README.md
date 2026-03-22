# Cloud Migration Optimizer v4 (CMOv4)

This module extends the capabilities of CMOv3 by supporting:
- Richer component modeling (instance counts, logical relationships, dependencies)
- Technology stack awareness (languages, frameworks, DB engines)
- Real-world architecture patterns (multi-tenancy, ports/adapters, microservices)
- Improved heuristic and exhaustive search
- Direct comparison with CMOv3 for benchmarking

## Structure
- `models.py`: Data models for components, relationships, tech stack
- `optimizer.py`: CSP, rule engine, Pareto logic adapted for richer models
- `search.py`: Heuristic and exhaustive search algorithms
- `validation.py`: Input validation and smart selection rules
- `benchmark.py`: Scripts for comparing CMOv3 and CMOv4

## Getting Started
- See `models.py` for input schema
- Use `optimizer.py` to run optimization
- Use `benchmark.py` to compare results with CMOv3

---
This module is under active development. Contributions and feedback are welcome.