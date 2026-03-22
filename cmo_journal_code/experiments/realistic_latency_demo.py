"""Quick demo to exercise the RealisticLatencyModel and print results.

Run:
    python -m experiments.realistic_latency_demo
"""
from __future__ import annotations

from backend.engines.latency_graph import RealisticLatencyModel, demo_deployment


def main() -> None:
    model = RealisticLatencyModel()
    deployment = demo_deployment()
    result = model.compute_critical_path(deployment)

    print(f"Critical path latency: {result['total_latency']:.2f} ms")
    print("Critical path:", " → ".join(result['critical_path']))
    print("Breakdown:")
    for hop in result['path_breakdown']:
        print(f"  {hop['from']}({hop['from_region']}) -> {hop['to']}({hop['to_region']})"
              f" | svc={hop['service_latency']}ms, net={hop['network_latency']}ms, total={hop['total']}ms")


if __name__ == "__main__":
    main()
