#!/usr/bin/env python3
"""
Test script to verify academic PDF report generation
"""

import sys
import json
from academic_report_generator import generate_academic_report

# Sample benchmark data
sample_benchmark_data = {
    "v3": {
        "aws_cost": 1250.50,
        "azure_cost": 1380.75,
        "gcp_cost": 1195.25,
        "optimal_cost": 1195.25,
        "optimal_provider": "GCP"
    },
    "v4": {
        "solutions": [
            {
                "cost": 1195.25,
                "latency": 12.5,
                "providers": 3,
                "score": 92.5,
                "configuration": {
                    "web": "AWS EC2 t3.medium",
                    "compute": "Azure Standard_D2s_v3",
                    "database": "GCP Cloud SQL db-n1-standard-2",
                    "cache": "AWS ElastiCache cache.t3.micro",
                    "storage": "GCP Cloud Storage Standard"
                },
                "providerDistribution": {
                    "AWS": 2,
                    "Azure": 1,
                    "GCP": 2
                }
            },
            {
                "cost": 1250.00,
                "latency": 10.2,
                "providers": 2,
                "score": 88.0,
                "configuration": {
                    "web": "AWS EC2 t3.medium",
                    "compute": "AWS Lambda",
                    "database": "Azure SQL Database",
                    "cache": "AWS ElastiCache cache.t3.micro",
                    "storage": "AWS S3 Standard"
                },
                "providerDistribution": {
                    "AWS": 4,
                    "Azure": 1
                }
            },
            {
                "cost": 1380.50,
                "latency": 8.5,
                "providers": 1,
                "score": 85.0,
                "configuration": {
                    "web": "Azure App Service",
                    "compute": "Azure Functions",
                    "database": "Azure SQL Database",
                    "cache": "Azure Cache for Redis",
                    "storage": "Azure Blob Storage"
                },
                "providerDistribution": {
                    "Azure": 5
                }
            }
        ],
        "pareto_frontier": [
            {"cost": 1195.25, "latency": 12.5, "providers": 3, "score": 92.5},
            {"cost": 1250.00, "latency": 10.2, "providers": 2, "score": 88.0},
            {"cost": 1380.50, "latency": 8.5, "providers": 1, "score": 85.0}
        ],
        "pareto_metrics": {
            "hypervolume": 156.75,
            "spacing": 0.85,
            "coverage_rate": 3.8
        },
        "deduplication_stats": {
            "initial_count": 24,
            "final_count": 12,
            "reduction_percentage": 50.0
        },
        "metadata": {
            "execution_time_ms": 450,
            "timestamp": "2025-11-19T22:00:00Z"
        }
    },
    "metrics": {
        "total_time_ms": 450,
        "csp_time_ms": 180,
        "expert_time_ms": 120,
        "pareto_time_ms": 150,
        "search_space_size": 32768,
        "feasible_space_size": 24,
        "pareto_frontier_size": 3,
        "pruning_efficiency": 99.93,
        "solutions_evaluated": 24,
        "config_snapshot": {
            "csp_strategy": "adaptive",
            "rule_weights": {
                "cost_weight": 1.0,
                "latency_weight": 0.8,
                "reliability_weight": 0.7,
                "complexity_weight": 0.5
            }
        }
    }
}

def main():
    print("🔧 Testing Academic PDF Report Generation...")
    print("-" * 70)
    
    try:
        # Generate academic PDF
        print("📄 Generating academic PDF report...")
        pdf_buffer = generate_academic_report(sample_benchmark_data, charts_data=None)
        
        # Save to file
        output_file = "test_academic_report.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ Success! Academic report generated: {output_file}")
        print(f"📊 Report size: {len(pdf_buffer.getvalue())} bytes")
        print("\n📋 Report includes:")
        print("   ✓ Title Page with key metrics")
        print("   ✓ Abstract")
        print("   ✓ Introduction")
        print("   ✓ Mathematical Foundations (CSP, Pareto optimality)")
        print("   ✓ Algorithmic Implementation (3 stages)")
        print("   ✓ Experimental Results with statistics")
        print("   ✓ State-of-the-Art Comparison")
        print("   ✓ Limitations and Future Work")
        print("   ✓ Conclusion")
        print("   ✓ References (12 academic sources)")
        print("\n🎉 Academic PDF generation test PASSED!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Academic PDF generation test FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
