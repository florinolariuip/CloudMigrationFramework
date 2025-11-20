#!/usr/bin/env python3
"""
Test script to verify PDF report generation for CMOv4.
"""

import sys
import json
from cmov4.report_generator import generate_cmov4_report

# Sample solution data
sample_solution = {
    "cost": 1250.50,
    "latency": 12.5,
    "providers": 3,
    "score": 0.92,
    "configuration": {
        "web": {"provider": "AWS", "service": "EC2", "instance_type": "t3.medium"},
        "compute": {"provider": "Azure", "service": "VM", "instance_type": "Standard_D2s_v3"},
        "database": {"provider": "GCP", "service": "Cloud SQL", "instance_type": "db-n1-standard-2"},
        "cache": {"provider": "AWS", "service": "ElastiCache", "instance_type": "cache.t3.micro"},
        "storage": {"provider": "AWS", "service": "S3", "instance_type": "Standard"},
    },
    "providerDistribution": {
        "AWS": 3,
        "Azure": 1,
        "GCP": 1
    },
    "pareto_rank": 1,
    "explanations": [
        "Cost-effective solution within budget constraints",
        "Balanced latency across all components",
        "Multi-cloud strategy provides redundancy"
    ]
}

# Sample scenario info
sample_scenario_info = {
    "scenario_name": "Test E-Commerce Platform",
    "architecture_pattern": "microservices",
    "components_count": 5,
    "max_budget": 2000,
    "max_latency": 20,
    "requests_per_month": 1000000,
    "cross_az_gb": 100,
    "internet_egress_gb": 500,
    "ebs_gb": 200,
    "rds_backup_gb": 50,
    "s3_gb": 1000,
    "preferred_provider": "AWS",
    "prioritize_cost": True,
    "prioritize_performance": False,
    "search_strategy": "adaptive",
    "sample_size": 100
}

def main():
    print("🔧 Testing CMOv4 PDF Report Generation...")
    print("-" * 60)
    
    try:
        # Generate PDF
        print("📄 Generating PDF report...")
        pdf_buffer = generate_cmov4_report(sample_solution, sample_scenario_info)
        
        # Save to file
        output_file = "test_cmov4_report.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ Success! PDF report generated: {output_file}")
        print(f"📊 Report size: {len(pdf_buffer.getvalue())} bytes")
        print("\n🎉 PDF generation test PASSED!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  PDF generation test FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
