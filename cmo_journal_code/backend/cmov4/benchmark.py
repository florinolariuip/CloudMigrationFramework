SCENARIOS = [
    # 5 components
    {
        'architecture': {
            'components': [
                {'name': 'Frontend', 'type': 'web', 'instance_count': 2, 'tech_stack': {'framework': 'React'}, 'dependencies': ['AppServer']},
                {'name': 'AppServer', 'type': 'compute', 'instance_count': 2, 'tech_stack': {'language': 'Python'}, 'dependencies': ['Database']},
                {'name': 'Database', 'type': 'database', 'instance_count': 1, 'tech_stack': {'engine': 'Postgres'}, 'dependencies': []},
                {'name': 'Cache', 'type': 'cache', 'instance_count': 1, 'tech_stack': {'engine': 'Redis'}, 'dependencies': ['Database']},
                {'name': 'Monitor', 'type': 'monitoring', 'instance_count': 1, 'tech_stack': {'tool': 'Prometheus'}, 'dependencies': []}
            ],
            'relationships': [
                {'from': 'Frontend', 'to': 'AppServer', 'type': 'depends_on'},
                {'from': 'AppServer', 'to': 'Database', 'type': 'depends_on'},
                {'from': 'Cache', 'to': 'Database', 'type': 'depends_on'}
            ],
            'multi_tenancy': False,
            'architecture_pattern': 'monolith'
        },
        'constraints': {
            'maxBudget': 10000,
            'maxLatency': 150,
            'requiredProviders': ['AWS', 'Azure', 'GCP'],
            'securityLevel': 'medium'
        },
        'pricing': {
            'AWS': {'web': {'React': 0.08}, 'compute': {'Python': 0.10}, 'database': {'Postgres': 0.25}, 'cache': {'Redis': 0.05}, 'monitoring': {'Prometheus': 0.03}},
            'Azure': {'web': {'React': 0.07}, 'compute': {'Python': 0.09}, 'database': {'Postgres': 0.22}, 'cache': {'Redis': 0.04}, 'monitoring': {'Prometheus': 0.02}}
        }
    },
    # 10 components
    {
        'architecture': {
            'components': [
                {'name': 'Frontend', 'type': 'web', 'instance_count': 3, 'tech_stack': {'framework': 'Angular'}, 'dependencies': ['AppServer']},
                {'name': 'AppServer', 'type': 'compute', 'instance_count': 3, 'tech_stack': {'language': 'Java'}, 'dependencies': ['Database']},
                {'name': 'Database', 'type': 'database', 'instance_count': 2, 'tech_stack': {'engine': 'MySQL'}, 'dependencies': []},
                {'name': 'Cache', 'type': 'cache', 'instance_count': 2, 'tech_stack': {'engine': 'Memcached'}, 'dependencies': ['Database']},
                {'name': 'Monitor', 'type': 'monitoring', 'instance_count': 1, 'tech_stack': {'tool': 'Grafana'}, 'dependencies': []},
                {'name': 'Queue', 'type': 'message_queue', 'instance_count': 1, 'tech_stack': {'engine': 'RabbitMQ'}, 'dependencies': ['AppServer']},
                {'name': 'Storage', 'type': 'storage', 'instance_count': 1, 'tech_stack': {'engine': 'S3'}, 'dependencies': []},
                {'name': 'LB', 'type': 'load_balancer', 'instance_count': 1, 'tech_stack': {'engine': 'Nginx'}, 'dependencies': ['Frontend']},
                {'name': 'Backup', 'type': 'backup', 'instance_count': 1, 'tech_stack': {'tool': 'Velero'}, 'dependencies': ['Storage']},
                {'name': 'Security', 'type': 'security', 'instance_count': 1, 'tech_stack': {'tool': 'Vault'}, 'dependencies': []}
            ],
            'relationships': [],
            'multi_tenancy': True,
            'architecture_pattern': 'microservices'
        },
        'constraints': {
            'maxBudget': 15000,
            'maxLatency': 200,
            'requiredProviders': ['AWS', 'Azure', 'GCP'],
            'securityLevel': 'high'
        },
        'pricing': {
            'AWS': {'web': {'Angular': 0.09}, 'compute': {'Java': 0.12}, 'database': {'MySQL': 0.28}, 'cache': {'Memcached': 0.06}, 'monitoring': {'Grafana': 0.04}, 'message_queue': {'RabbitMQ': 0.07}, 'storage': {'S3': 0.03}, 'load_balancer': {'Nginx': 0.05}, 'backup': {'Velero': 0.04}, 'security': {'Vault': 0.06}},
            'Azure': {'web': {'Angular': 0.08}, 'compute': {'Java': 0.11}, 'database': {'MySQL': 0.25}, 'cache': {'Memcached': 0.05}, 'monitoring': {'Grafana': 0.03}, 'message_queue': {'RabbitMQ': 0.06}, 'storage': {'S3': 0.02}, 'load_balancer': {'Nginx': 0.04}, 'backup': {'Velero': 0.03}, 'security': {'Vault': 0.05}},
            'GCP': {'web': {'Angular': 0.10}, 'compute': {'Java': 0.13}, 'database': {'MySQL': 0.30}, 'cache': {'Memcached': 0.07}, 'monitoring': {'Grafana': 0.05}, 'message_queue': {'RabbitMQ': 0.08}, 'storage': {'S3': 0.04}, 'load_balancer': {'Nginx': 0.06}, 'backup': {'Velero': 0.05}, 'security': {'Vault': 0.07}}
        }
    },
    # 18 components (enterprise scale)
    {
        'architecture': {
            'components': [
                {'name': 'Frontend', 'type': 'web', 'instance_count': 5, 'tech_stack': {'framework': 'Vue'}, 'dependencies': ['AppServer']},
                {'name': 'AppServer', 'type': 'compute', 'instance_count': 5, 'tech_stack': {'language': 'Go'}, 'dependencies': ['Database']},
                {'name': 'Database', 'type': 'database', 'instance_count': 3, 'tech_stack': {'engine': 'SQL Server'}, 'dependencies': []},
                {'name': 'NoSQL', 'type': 'nosql', 'instance_count': 2, 'tech_stack': {'engine': 'MongoDB'}, 'dependencies': []},
                {'name': 'Cache', 'type': 'cache', 'instance_count': 3, 'tech_stack': {'engine': 'Redis'}, 'dependencies': ['Database']},
                {'name': 'Monitor', 'type': 'monitoring', 'instance_count': 2, 'tech_stack': {'tool': 'Datadog'}, 'dependencies': []},
                {'name': 'Queue', 'type': 'message_queue', 'instance_count': 2, 'tech_stack': {'engine': 'Kafka'}, 'dependencies': ['AppServer']},
                {'name': 'EventStream', 'type': 'event_streaming', 'instance_count': 1, 'tech_stack': {'engine': 'Kinesis'}, 'dependencies': ['Queue']},
                {'name': 'Storage', 'type': 'storage', 'instance_count': 2, 'tech_stack': {'engine': 'Blob'}, 'dependencies': []},
                {'name': 'LB', 'type': 'load_balancer', 'instance_count': 2, 'tech_stack': {'engine': 'HAProxy'}, 'dependencies': ['Frontend']},
                {'name': 'Backup', 'type': 'backup', 'instance_count': 2, 'tech_stack': {'tool': 'Restic'}, 'dependencies': ['Storage']},
                {'name': 'Security', 'type': 'security', 'instance_count': 2, 'tech_stack': {'tool': 'Keycloak'}, 'dependencies': []},
                {'name': 'CDN', 'type': 'cdn', 'instance_count': 1, 'tech_stack': {'engine': 'Cloudflare'}, 'dependencies': ['Frontend']},
                {'name': 'Analytics', 'type': 'analytics', 'instance_count': 1, 'tech_stack': {'tool': 'Mixpanel'}, 'dependencies': []},
                {'name': 'Encryption', 'type': 'encryption', 'instance_count': 1, 'tech_stack': {'tool': 'AWS KMS'}, 'dependencies': []},
                {'name': 'Containers', 'type': 'containers', 'instance_count': 1, 'tech_stack': {'engine': 'Docker'}, 'dependencies': ['AppServer']},
                {'name': 'Serverless', 'type': 'serverless_compute', 'instance_count': 1, 'tech_stack': {'engine': 'AWS Lambda'}, 'dependencies': []},
                {'name': 'Identity', 'type': 'identity', 'instance_count': 1, 'tech_stack': {'tool': 'Auth0'}, 'dependencies': []},
                {'name': 'IoT', 'type': 'iot', 'instance_count': 1, 'tech_stack': {'platform': 'AWS IoT'}, 'dependencies': []}
            ],
            'relationships': [],
            'multi_tenancy': True,
            'architecture_pattern': 'event-driven'
        },
        'constraints': {
            'maxBudget': 25000,
            'maxLatency': 300,
            'requiredProviders': ['AWS', 'Azure', 'GCP'],
            'securityLevel': 'high'
        },
        'pricing': {
            'AWS': {'web': {'Vue': 0.12}, 'compute': {'Go': 0.15}, 'database': {'SQL Server': 0.35}, 'nosql': {'MongoDB': 0.28}, 'cache': {'Redis': 0.09}, 'monitoring': {'Datadog': 0.08}, 'message_queue': {'Kafka': 0.10}, 'event_streaming': {'Kinesis': 0.12}, 'storage': {'Blob': 0.06}, 'load_balancer': {'HAProxy': 0.08}, 'backup': {'Restic': 0.07}, 'security': {'Keycloak': 0.09}, 'cdn': {'Cloudflare': 0.11}, 'analytics': {'Mixpanel': 0.10}, 'encryption': {'AWS KMS': 0.09}, 'containers': {'Docker': 0.13}, 'serverless_compute': {'AWS Lambda': 0.14}, 'identity': {'Auth0': 0.06}, 'iot': {'AWS IoT': 0.08}},
            'Azure': {'web': {'Vue': 0.11}, 'compute': {'Go': 0.14}, 'database': {'SQL Server': 0.33}, 'nosql': {'MongoDB': 0.26}, 'cache': {'Redis': 0.08}, 'monitoring': {'Datadog': 0.07}, 'message_queue': {'Kafka': 0.09}, 'event_streaming': {'Kinesis': 0.11}, 'storage': {'Blob': 0.05}, 'load_balancer': {'HAProxy': 0.07}, 'backup': {'Restic': 0.06}, 'security': {'Keycloak': 0.08}, 'cdn': {'Cloudflare': 0.10}, 'analytics': {'Mixpanel': 0.09}, 'encryption': {'AWS KMS': 0.08}, 'containers': {'Docker': 0.12}, 'serverless_compute': {'AWS Lambda': 0.13}, 'identity': {'Auth0': 0.05}, 'iot': {'AWS IoT': 0.07}},
            'GCP': {'web': {'Vue': 0.13}, 'compute': {'Go': 0.16}, 'database': {'SQL Server': 0.36}, 'nosql': {'MongoDB': 0.30}, 'cache': {'Redis': 0.10}, 'monitoring': {'Datadog': 0.09}, 'message_queue': {'Kafka': 0.11}, 'event_streaming': {'Kinesis': 0.13}, 'storage': {'Blob': 0.07}, 'load_balancer': {'HAProxy': 0.09}, 'backup': {'Restic': 0.08}, 'security': {'Keycloak': 0.10}, 'cdn': {'Cloudflare': 0.12}, 'analytics': {'Mixpanel': 0.11}, 'encryption': {'AWS KMS': 0.10}, 'containers': {'Docker': 0.14}, 'serverless_compute': {'AWS Lambda': 0.15}, 'identity': {'Auth0': 0.07}, 'iot': {'AWS IoT': 0.09}}
        }
    }
]
"""
CMOv4 Benchmarking
- Compare CMOv3/baselines and CMOv4 on identical scenarios

Pricing fix:
  The static SCENARIOS above contain per-unit "pricing" dicts that were
  originally used for development placeholders.  All baseline and CMOv4
  runs now use the live pricing service (backend.services.pricing) so that
  CMO and every baseline algorithm operate on identical cost/latency data.
  The static pricing dicts are ignored at runtime.
"""
from ..engines.baselines import run_all_baselines
from .optimizer import optimize_architecture
from .models import Architecture


def run_benchmark(scenarios: list = SCENARIOS):
    """
    Run benchmarks for a list of scenarios (default: static SCENARIOS).
    """
    results = []
    for scenario in scenarios:
        results.append(run_single_benchmark(scenario))
    return results


def run_single_benchmark(scenario: dict, fast_baselines: bool = False):
    """
    Run benchmark for a single scenario dict.

    All algorithms (CMOv4, GA, greedy, random, weighted-sum) use the same
    live pricing data fetched from backend.services.pricing at runtime.
    The 'pricing' key in the scenario dict is intentionally ignored to
    ensure a fair, apples-to-apples comparison.

    Args:
        scenario:        Scenario dict (architecture + constraints).
        fast_baselines:  Pass True only for quick smoke tests.  Publication
                         runs must use fast_baselines=False (default) so that
                         GA runs with pop=50 × gen=100 as stated in the paper.
    """
    arch         = scenario['architecture']
    constraints  = scenario['constraints']
    # NOTE: scenario.get('pricing') is deliberately NOT forwarded to any
    # algorithm.  All cost/latency data comes from the live pricing service.
    config        = scenario.get('config', None)
    usage_profile = scenario.get('usage_profile', None)
    preferences   = scenario.get('preferences', None)

    if usage_profile:
        constraints['usage_profile'] = usage_profile
    if preferences:
        constraints['preferences'] = preferences

    # Apply smart selection rules if present
    from .models import Architecture, Component
    components   = [Component(**c) for c in arch.get('components', [])]
    architecture = Architecture(
        components=components,
        relationships=arch.get('relationships', []),
        multi_tenancy=arch.get('multi_tenancy', False),
        architecture_pattern=arch.get('architecture_pattern'),
        pricing=None,
        selection_rules=arch.get('selection_rules', [])
    )
    if hasattr(architecture, 'apply_selection_rules'):
        architecture.apply_selection_rules({'constraints': constraints, 'pricing': {}})

    # Build CMOv3-compatible Constraints for the baselines
    from backend.models import Constraints
    from .optimizer import map_cmov4_to_cmov3_components

    selected_components = map_cmov4_to_cmov3_components(arch.get('components', []))
    cmov3_constraints = Constraints(
        maxBudget=constraints.get('maxBudget', 10000),
        maxLatency=constraints.get('maxLatency', 150),
        maxProviders=len(constraints.get('requiredProviders', ['AWS', 'Azure', 'GCP'])),
        selected_components=selected_components
    )

    # Run baselines (live pricing, consistent GA parameters)
    try:
        print(f"Running baselines (fast={fast_baselines})...")
        v3_results = run_all_baselines(cmov3_constraints, fast=fast_baselines)
        print("Baselines completed.")
    except Exception as e:
        print(f"Baselines failed: {e}")
        v3_results = {"error": str(e)}

    # Run CMOv4 optimizer (also uses live pricing internally)
    try:
        print("Running CMOv4 optimizer...")
        v4_results = optimize_architecture(arch, constraints, config)
        print("CMOv4 optimizer completed.")
    except Exception as e:
        print(f"CMOv4 optimizer failed: {e}")
        v4_results = {"error": str(e)}

    return {
        'scenario':    scenario,
        'v3_baselines': v3_results,
        'v4':           v4_results,
    }
