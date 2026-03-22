# Experiment Results

## NSGA2

| algorithm   |   cost |   latency |   hypervolume |
|:------------|-------:|----------:|--------------:|
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |
| NSGA-II     | 676.37 |         9 |           nan |

## MOEAD

| algorithm   |   cost |   latency |   hypervolume |
|:------------|-------:|----------:|--------------:|
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |
| MOEA/D      | 676.37 |         9 |           nan |

## BASELINES

| algorithm         |    cost |   latency |   hypervolume | success   |   iterations | reason                                            |
|:------------------|--------:|----------:|--------------:|:----------|-------------:|:--------------------------------------------------|
| Random Selection  | 2097.99 |   9.53333 |           nan | True      |            1 | Found valid solution after 1 random attempts      |
| Greedy-Cost       |  577.73 |   9.4     |           nan | True      |            1 | Greedy cost minimization successful               |
| Greedy-Latency    |  676.37 |   9       |           nan | True      |            1 | Greedy latency minimization successful            |
| Genetic Algorithm |  638.41 |   9.13333 |           nan | True      |         1500 | GA converged after 50 generations                 |
| Weighted Sum      |  624.1  |   9       |           nan | True      |            1 | Weighted sum (cost=0.50, latency=0.50) successful |

