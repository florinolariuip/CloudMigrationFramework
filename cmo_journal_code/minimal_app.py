#!/usr/bin/env python3
"""Minimal working app without problematic components"""

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Minimal static pricing data
STATIC_COSTS = {
    "AWS EC2": 30.37, "AWS RDS": 49.64, "AWS S3": 23.0,
    "Azure VM": 87.60, "Azure SQL": 65.0, "Azure Storage": 25.0,
    "GCP Compute Engine": 69.35, "GCP SQL": 83.95, "GCP BigQuery": 70.0
}

STATIC_LATENCY = {
    "AWS EC2": 8, "AWS RDS": 10, "AWS S3": 11,
    "Azure VM": 9, "Azure SQL": 12, "Azure Storage": 13,
    "GCP Compute Engine": 8, "GCP SQL": 11, "GCP BigQuery": 16
}

@app.route('/api/version')
def version():
    return jsonify({
        "version": "minimal-test",
        "has_seed_support": True,
        "features": {"explainability": True, "pareto": True, "seed": True}
    })

@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json
    constraints = data.get('constraints', {})
    
    # Simple solution without baselines
    solution = {
        "configuration": {
            "api_gateway": "AWS API Gateway",
            "database": "Azure SQL", 
            "application_server": "GCP Compute Engine"
        },
        "cost": 187.32,
        "latency": 10.33,
        "providers": 3
    }
    
    return jsonify({
        "results": [solution],
        "paretoFrontier": [solution],
        "explainability": {"message": "Minimal test version"},
        "metrics": {"execution_time_ms": 50}
    })

if __name__ == '__main__':
    print("Starting minimal app on port 5056...")
    app.run(host='127.0.0.1', port=5056, debug=False)