"""
Realistic latency modeling using a directed dependency graph.

Nodes = microservices; edges = API calls with weights that include
service processing time and inter-region network latency.

This replaces naive sum-of-latencies with critical path analysis.
"""
from __future__ import annotations

from typing import Dict, List, Any

import networkx as nx


class RealisticLatencyModel:
    """Geography-aware latency model with service dependencies.

    - Edge weight = service processing latency + inter-region network latency
    - Total latency = longest path (critical path) in the dependency DAG
    """

    def __init__(self, network_latency: Dict[tuple, float] | None = None,
                 service_dependencies: Dict[str, List[str]] | None = None) -> None:
        # Default inter-region network latencies (ms) — Dec 2025 realistic ranges
        self.network_latency: Dict[tuple, float] = network_latency or {
            # Intra-region
            ('us-east-1', 'us-east-1'): 1,
            ('us-west-2', 'us-west-2'): 1,
            ('eu-west-1', 'eu-west-1'): 1,
            ('eu-central-1', 'eu-central-1'): 1,
            ('ap-south-1', 'ap-south-1'): 1,
            ('ap-northeast-1', 'ap-northeast-1'): 1,

            # Cross-US
            ('us-east-1', 'us-west-2'): 65,
            ('us-west-2', 'us-east-1'): 65,

            # Within Europe
            ('eu-west-1', 'eu-central-1'): 20,
            ('eu-central-1', 'eu-west-1'): 20,

            # Cross-Atlantic
            ('us-east-1', 'eu-west-1'): 85,
            ('eu-west-1', 'us-east-1'): 85,
            ('us-east-1', 'eu-central-1'): 95,
            ('eu-central-1', 'us-east-1'): 95,
            ('us-west-2', 'eu-west-1'): 140,
            ('eu-west-1', 'us-west-2'): 140,

            # US ↔ Asia
            ('us-east-1', 'ap-south-1'): 200,
            ('ap-south-1', 'us-east-1'): 200,
            ('us-east-1', 'ap-northeast-1'): 180,
            ('ap-northeast-1', 'us-east-1'): 180,
            ('us-west-2', 'ap-south-1'): 180,
            ('ap-south-1', 'us-west-2'): 180,
            ('us-west-2', 'ap-northeast-1'): 120,
            ('ap-northeast-1', 'us-west-2'): 120,

            # Europe ↔ Asia
            ('eu-west-1', 'ap-south-1'): 120,
            ('ap-south-1', 'eu-west-1'): 120,
            ('eu-west-1', 'ap-northeast-1'): 230,
            ('ap-northeast-1', 'eu-west-1'): 230,
            ('eu-central-1', 'ap-south-1'): 110,
            ('ap-south-1', 'eu-central-1'): 110,

            # Within Asia
            ('ap-south-1', 'ap-northeast-1'): 90,
            ('ap-northeast-1', 'ap-south-1'): 90,
        }

    # Typical microservice dependencies (can be overridden)
        self.service_dependencies: Dict[str, List[str]] = service_dependencies or {
            # Entry
            'api-gateway': [],

            # User flows
            'user-service': ['api-gateway', 'auth-service'],
            'product-service': ['api-gateway', 'cache-service'],
            'order-service': ['api-gateway', 'user-service', 'inventory-service'],
            'payment-service': ['order-service', 'fraud-detection'],

            # Backend
            'inventory-service': ['product-service', 'database'],
            'notification-service': ['order-service', 'message-queue'],
            'analytics-service': ['message-queue', 'data-warehouse'],
            'search-service': ['product-service', 'elasticsearch'],

            # Infra
            'auth-service': ['cache-service', 'database'],
            'fraud-detection': ['database', 'ml-model'],
            'recommendation-engine': ['product-service', 'ml-model'],
            'cache-service': [],
            'database': [],
            'message-queue': [],
            'elasticsearch': [],
            'data-warehouse': [],
            'ml-model': [],
        }

        # Merge in live override matrix if available
        try:
            from backend.services.network_latency_store import get_override
            override = get_override()
            if override:
                # override keys are tuples (region_from, region_to)
                for (a, b), val in override.items():
                    self.network_latency[(a, b)] = float(val)
        except Exception:
            # If override store not available or fails, ignore silently
            pass

    def get_network_latency(self, from_region: str, to_region: str) -> float:
        key = (from_region, to_region)
        if key in self.network_latency:
            return self.network_latency[key]

        # Heuristics if missing
        if from_region == to_region:
            return 1
        if ('us' in from_region) and ('us' in to_region):
            return 65
        if ('eu' in from_region) and ('eu' in to_region):
            return 20
        if ('ap' in from_region) and ('ap' in to_region):
            return 90
        return 150  # cross-continent default

    def compute_critical_path(self, deployment: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compute critical path latency for a given deployment.

        deployment: service -> {region: str, latency: float, provider?: str}
        returns: {total_latency, critical_path, path_breakdown, num_hops}
        """
        G = nx.DiGraph()

        # Add nodes first
        for service_id, cfg in deployment.items():
            G.add_node(service_id,
                       service_latency=float(cfg.get('latency', 0.0)),
                       region=str(cfg.get('region', 'unknown')),
                       provider=str(cfg.get('provider', 'unknown')))

        # Add edges from dependencies
        for svc, deps in self.service_dependencies.items():
            if svc not in deployment:
                continue
            svc_region = deployment[svc]['region']
            svc_latency = float(deployment[svc].get('latency', 0.0))
            for dep in deps:
                if dep not in deployment:
                    continue
                dep_region = deployment[dep]['region']
                net = self.get_network_latency(dep_region, svc_region)
                total_edge = svc_latency + net
                G.add_edge(dep, svc,
                           network_latency=net,
                           service_latency=svc_latency,
                           total_latency=total_edge)

        # Identify entries/exits
        entry_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
        exit_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]

        # If graph is empty or has no edges, fallback
        if G.number_of_edges() == 0:
            total = sum(cfg.get('latency', 0.0) for cfg in deployment.values())
            return {
                'total_latency': total,
                'critical_path': list(deployment.keys()),
                'path_breakdown': [],
                'num_hops': 0,
                'entry_services': entry_nodes,
                'exit_services': exit_nodes,
            }

        # Compute longest path over subgraphs reachable from each entry
        best_latency = -1.0
        best_path: List[str] = []
        for entry in entry_nodes:
            reachable = nx.descendants(G, entry) | {entry}
            sub = G.subgraph(reachable).copy()
            # Ensure DAG longest path; if cycles exist, approximate by ignoring cycles
            try:
                path = nx.dag_longest_path(sub, weight='total_latency')
            except nx.NetworkXUnfeasible:
                # If cycles, break them by treating as DAG (remove back edges)
                path = list(nx.topological_sort(sub))
            path_latency = self._path_latency(sub, path)
            if path_latency > best_latency:
                best_latency = path_latency
                best_path = path

        breakdown = []
        for i in range(len(best_path) - 1):
            u, v = best_path[i], best_path[i + 1]
            data = G.get_edge_data(u, v)
            breakdown.append({
                'from': u,
                'to': v,
                'from_region': G.nodes[u]['region'],
                'to_region': G.nodes[v]['region'],
                'service_latency': float(data['service_latency']),
                'network_latency': float(data['network_latency']),
                'total': float(data['total_latency']),
            })

        return {
            'total_latency': float(best_latency if best_latency >= 0 else 0.0),
            'critical_path': best_path,
            'path_breakdown': breakdown,
            'num_hops': max(0, len(best_path) - 1),
            'entry_services': entry_nodes,
            'exit_services': exit_nodes,
        }

    @staticmethod
    def _path_latency(G: nx.DiGraph, path: List[str]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            data = G.get_edge_data(path[i], path[i + 1])
            total += float(data['total_latency'])
        return total


def demo_deployment() -> Dict[str, Dict[str, Any]]:
    """Small demo deployment showing cross-Atlantic hops."""
    return {
        'api-gateway': {'region': 'us-east-1', 'latency': 3.0},
        'auth-service': {'region': 'us-east-1', 'latency': 4.0},
        'user-service': {'region': 'eu-west-1', 'latency': 6.0},
        'product-service': {'region': 'eu-west-1', 'latency': 5.0},
        'order-service': {'region': 'us-east-1', 'latency': 7.0},
        'payment-service': {'region': 'us-east-1', 'latency': 9.0},
        'inventory-service': {'region': 'eu-west-1', 'latency': 5.0},
        'cache-service': {'region': 'us-east-1', 'latency': 1.0},
        'database': {'region': 'us-east-1', 'latency': 8.0},
        'message-queue': {'region': 'us-east-1', 'latency': 2.0},
        'fraud-detection': {'region': 'us-east-1', 'latency': 10.0},
        'ml-model': {'region': 'us-east-1', 'latency': 12.0},
        'elasticsearch': {'region': 'eu-west-1', 'latency': 4.0},
        'data-warehouse': {'region': 'eu-west-1', 'latency': 11.0},
    }


if __name__ == "__main__":
    model = RealisticLatencyModel()
    result = model.compute_critical_path(demo_deployment())
    print(f"Critical path latency: {result['total_latency']:.2f} ms")
    print("Path:", " → ".join(result['critical_path']))
    for hop in result['path_breakdown']:
        print(f"{hop['from']}({hop['from_region']}) -> {hop['to']}({hop['to_region']})"
              f" | svc={hop['service_latency']}ms, net={hop['network_latency']}ms, total={hop['total']}ms")
