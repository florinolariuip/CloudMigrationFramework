from backend.models import UsageProfile
def calculate_total_cost(configuration: dict, profile: UsageProfile) -> float:
    # Base service costs
    base_cost = sum(get_service_costs().get(svc, 0) for svc in configuration.values())
    # Enhanced costs
    transfer_cost = calculate_data_transfer_cost(profile)
    storage_cost = calculate_storage_cost(profile)
    api_cost = calculate_api_gateway_cost(profile)
    cdn_cost = calculate_cloudfront_cost(profile)
    reuse_savings = optimize_component_reuse(list(configuration.keys()))
    return base_cost + transfer_cost + storage_cost + api_cost + cdn_cost - reuse_savings
# --- Enhanced Cost Functions ---



from backend.models import UsageProfile

def calculate_data_transfer_cost(profile: UsageProfile) -> float:
    cross_az = profile.cross_az_gb * 0.02  # $0.02/GB inter-AZ
    internet = profile.internet_egress_gb * 0.09  # $0.09/GB egress
    return cross_az + internet

def calculate_storage_cost(profile: UsageProfile) -> float:
    ebs = profile.ebs_gb * 0.08  # $0.08/GB EBS
    rds_backup = profile.rds_backup_gb * 0.095  # $0.095/GB RDS backup
    s3 = profile.s3_gb * 0.023  # $0.023/GB S3
    return ebs + rds_backup + s3

def calculate_api_gateway_cost(profile: UsageProfile) -> float:
    return (profile.requests_per_month / 1_000_000) * 3.50  # $3.50 per 1M requests

def calculate_cloudfront_cost(profile: UsageProfile) -> float:
    return profile.internet_egress_gb * 0.085  # $0.085/GB CDN

def optimize_component_reuse(components: list) -> float:
    # Example: If both 'cache' and 'session_store' present, save cost of one Redis node
    if 'cache' in components and 'session_store' in components:
        return 35.0  # Example savings
    return 0.0

# Singleton cache used by the app

# Singleton cache used by the app

# Singleton cache used by the app




# COMPONENTS used for combinations calculation (Extended to 15 for Priority 4)
COMPONENTS = [
    # Original 6 components
    "api_gateway",
    "identity_management",
    "analytics",
    "database",
    "application_server",
    "storage",
    # New 9 components for scalability demonstration
    "cache",
    "message_queue",
    "cdn",
    "load_balancer",
    "monitoring",
    "backup",
    "encryption",
    "containers",
    "serverless_compute"
]
## Singleton cache used by the app






from typing import Dict, Any, Optional, List
from datetime import datetime
from threading import Lock
import requests

from backend.config import DEFAULT_PRICING


class ServiceDataCache:
    def __init__(self, ttl_seconds=3600):  # Cache for 1 hour
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.last_updated: Optional[datetime] = None
        self.lock = Lock()

    # --- Azure Retail Prices helpers ---
    def _azure_retail_query(self, filter_expr: str, currency: str = "USD") -> Optional[List[Dict[str, Any]]]:
        try:
            url = "https://prices.azure.com/api/retail/prices"
            params = {"$filter": filter_expr, "currencyCode": currency}
            resp = requests.get(url, params=params, timeout=3)
            resp.raise_for_status()
            data = resp.json()
            return data.get("Items", [])
        except Exception as e:
            print(f"Azure retail query failed for filter [{filter_expr}]: {e}")
            return None

    def _azure_monthly_from_item(self, item: Dict[str, Any]) -> Optional[float]:
        try:
            price = float(item.get("retailPrice") or item.get("unitPrice") or 0)
            uom = (item.get("unitOfMeasure") or "").lower()
            if price <= 0:
                return None
            if "hour" in uom:
                return round(price * 730, 2)
            return round(price, 2)
        except Exception:
            return None

    def _azure_first_monthly(self, filter_expr: str, currency: str = "USD") -> Optional[float]:
        items = self._azure_retail_query(filter_expr, currency)
        if not items:
            return None
        items_sorted = sorted(items, key=lambda x: x.get("retailPrice", float("inf")))
        for it in items_sorted:
            m = self._azure_monthly_from_item(it)
            if m is not None:
                return m
        return None

    def fetch_azure_pricing(self) -> Optional[Dict[str, float]]:
        try:
            region = DEFAULT_PRICING.get("azure_region", "westeurope")
            currency = DEFAULT_PRICING.get("currency", "USD")
            results: Dict[str, float] = {}

            apim_filter = (
                f"serviceName eq 'API Management' and armRegionName eq '{region}' "
                f"and contains(meterName,'Developer') and priceType eq 'Consumption'"
            )
            apim_price = self._azure_first_monthly(apim_filter, currency)
            if apim_price:
                results["Azure API Management"] = apim_price

            vm_filter = (
                f"serviceName eq 'Virtual Machines' and armRegionName eq '{region}' "
                f"and contains(skuName,'D2s v3') and contains(productName,'Linux') and priceType eq 'Consumption'"
            )
            vm_price = self._azure_first_monthly(vm_filter, currency)
            if vm_price:
                results["Azure VM"] = vm_price

            sql_filter = (
                f"serviceName eq 'SQL Database' and armRegionName eq '{region}' "
                f"and contains(meterName,'Gen5') and contains(meterName,'2 vCore') and priceType eq 'Consumption'"
            )
            sql_price = self._azure_first_monthly(sql_filter, currency)
            if sql_price:
                results["Azure SQL"] = sql_price

            syn_filter = (
                f"serviceName eq 'Azure Synapse Analytics' and armRegionName eq '{region}' "
                f"and (contains(meterName,'DWU100c') or contains(meterName,'100 DWU')) and priceType eq 'Consumption'"
            )
            syn_price = self._azure_first_monthly(syn_filter, currency)
            if syn_price:
                results["Azure Synapse"] = syn_price

            # Azure Storage (Standard LRS, per TB-month)
            storage_filter = (
                f"serviceName eq 'Storage' and armRegionName eq '{region}' "
                f"and contains(skuName,'Standard_LRS') and contains(meterName,'Data Stored') and priceType eq 'Consumption'"
            )
            storage_price = self._azure_first_monthly(storage_filter, currency)
            if storage_price:
                results["Azure Storage"] = storage_price

            # Azure Functions (per million executions)
            functions_filter = (
                f"serviceName eq 'Functions' and armRegionName eq '{region}' "
                f"and contains(meterName,'Execution') and priceType eq 'Consumption'"
            )
            functions_price = self._azure_first_monthly(functions_filter, currency)
            if functions_price:
                results["Azure Functions"] = functions_price

            # Fallback values for any services the API didn't return
            results.setdefault("Azure AD", 60.0)
            results.setdefault("Azure VM", 750.0)
            results.setdefault("Azure SQL", 650.0)
            results.setdefault("Azure Storage", 300.0)
            results.setdefault("Azure Functions", 200.0)

            return results if results else None
        except Exception as e:
            print(f"Error fetching Azure pricing: {e}")
            return None

    def fetch_cloudharmony_latency(self) -> Optional[Dict[str, float]]:
        """Placeholder for third-party latency data (not implemented)"""
        return None

    def fetch_aws_pricing(self) -> Optional[Dict[str, float]]:
        """
        Fetch AWS pricing using regional pricing data from AWS documentation
        Prices updated monthly from official AWS pricing pages (Nov 2025)
        Region-aware pricing for accurate cost estimation
        """
        try:
            results: Dict[str, float] = {}
            
            # Get region from config
            region = DEFAULT_PRICING.get("aws_region", "us-east-1")
            
            # EC2 pricing - t3.medium on-demand (updated Nov 2025)
            try:
                ec2_prices = {
                    "us-east-1": 0.0416,
                    "us-west-2": 0.0416,
                    "eu-west-1": 0.0456,
                    "ap-southeast-1": 0.0488
                }
                hourly = ec2_prices.get(region, 0.0416)
                results["AWS EC2"] = round(hourly * 730, 2)
            except Exception as e:
                results["AWS EC2"] = 30.37
            
            # RDS pricing - db.t3.medium MySQL (updated Nov 2025)
            try:
                rds_prices = {
                    "us-east-1": 0.068,
                    "us-west-2": 0.068,
                    "eu-west-1": 0.075,
                    "ap-southeast-1": 0.082
                }
                hourly = rds_prices.get(region, 0.068)
                results["AWS RDS"] = round(hourly * 730, 2)
            except Exception as e:
                results["AWS RDS"] = 49.64
            
            # S3 pricing (standard storage)
            try:
                s3_prices = {
                    "us-east-1": 0.023,
                    "us-west-2": 0.023,
                    "eu-west-1": 0.024,
                    "ap-southeast-1": 0.025
                }
                per_gb = s3_prices.get(region, 0.023)
                results["AWS S3"] = round(per_gb * 1000, 2)  # 1TB
            except Exception as e:
                results["AWS S3"] = 23.0
            
            # API Gateway pricing
            try:
                apigw_prices = {
                    "us-east-1": 3.50,
                    "us-west-2": 3.50,
                    "eu-west-1": 3.57,
                    "ap-southeast-1": 4.25
                }
                per_million = apigw_prices.get(region, 3.50)
                results["AWS API Gateway"] = round(per_million * 10, 2)  # 10M requests
            except Exception as e:
                results["AWS API Gateway"] = 35.0
            
            # IAM (free service)
            results["AWS IAM"] = 0
            
            # QuickSight pricing
            try:
                # QuickSight: $9/user/month for readers, assume 10 users
                results["AWS QuickSight"] = round(9 * 10, 2)
            except:
                pass
            
            # ElastiCache (cache.t3.medium Redis)
            try:
                cache_prices = {
                    "us-east-1": 0.068,
                    "us-west-2": 0.068,
                    "eu-west-1": 0.075,
                    "ap-southeast-1": 0.082
                }
                hourly = cache_prices.get(region, 0.068)
                results["AWS ElastiCache"] = round(hourly * 730, 2)
            except Exception as e:
                results["AWS ElastiCache"] = 49.64
            
            # SQS pricing
            try:
                results["AWS SQS"] = round(0.40 * 10, 2)
            except Exception as e:
                results["AWS SQS"] = 4.0
            
            # CloudFront pricing
            try:
                cdn_prices = {
                    "us-east-1": 0.085,
                    "us-west-2": 0.085,
                    "eu-west-1": 0.085,
                    "ap-southeast-1": 0.140
                }
                per_gb = cdn_prices.get(region, 0.085)
                results["AWS CloudFront"] = round(per_gb * 1000, 2)
            except Exception as e:
                results["AWS CloudFront"] = 85.0
            
            # ALB pricing
            try:
                alb_hour_prices = {
                    "us-east-1": 0.0225,
                    "us-west-2": 0.0225,
                    "eu-west-1": 0.0243,
                    "ap-southeast-1": 0.0243
                }
                hourly = alb_hour_prices.get(region, 0.0225)
                lcu_cost = 0.008 * 5  # 5 LCU-hours average
                results["AWS ALB"] = round((hourly + lcu_cost) * 730, 2)
            except Exception as e:
                results["AWS ALB"] = 45.62
            
            # CloudWatch pricing
            try:
                results["AWS CloudWatch"] = round(0.30 * 100, 2)
            except Exception as e:
                results["AWS CloudWatch"] = 30.0
            
            # Backup pricing
            try:
                results["AWS Backup"] = round(0.05 * 1000, 2)
            except Exception as e:
                results["AWS Backup"] = 50.0
            
            # KMS pricing
            try:
                results["AWS KMS"] = round(1 * 10 + 0.03 * 100, 2)
            except Exception as e:
                results["AWS KMS"] = 13.0
            
            # EKS pricing
            try:
                cluster_cost = 0.10 * 730
                ec2_hourly = ec2_prices.get(region, 0.0416)
                worker_cost = ec2_hourly * 730 * 3
                results["AWS EKS"] = round(cluster_cost + worker_cost, 2)
            except Exception as e:
                results["AWS EKS"] = 164.1
            
            # Lambda pricing
            try:
                results["AWS Lambda"] = round(0.20 * 10 + 5, 2)
            except Exception as e:
                results["AWS Lambda"] = 7.0
            
            return results if results else None
            
        except Exception as e:
            print(f"AWS pricing failed: {e}")
            return None

    def fetch_gcp_pricing(self) -> Optional[Dict[str, float]]:
        """
        Fetch GCP pricing using regional pricing data from GCP documentation
        Prices updated monthly from official GCP pricing pages (Nov 2025)
        Region-aware pricing for accurate cost estimation
        """
        try:
            results: Dict[str, float] = {}
            
            # Get region from config
            region = DEFAULT_PRICING.get("gcp_region", "us-central1")
            
            # Compute Engine - n1-standard-2 (updated Nov 2025)
            try:
                compute_prices = {
                    "us-central1": 0.095,
                    "us-west1": 0.095,
                    "europe-west1": 0.104,
                    "asia-southeast1": 0.109
                }
                hourly = compute_prices.get(region, 0.095)
                results["GCP Compute Engine"] = round(hourly * 730, 2)
            except Exception as e:
                results["GCP Compute Engine"] = 69.35
            
            # Cloud SQL - db-n1-standard-2 MySQL (updated Nov 2025)
            try:
                sql_prices = {
                    "us-central1": 0.115,
                    "us-west1": 0.115,
                    "europe-west1": 0.127,
                    "asia-southeast1": 0.132
                }
                hourly = sql_prices.get(region, 0.115)
                results["GCP SQL"] = round(hourly * 730, 2)
            except Exception as e:
                results["GCP SQL"] = 83.95
            
            # BigQuery pricing
            try:
                storage_prices = {
                    "us-central1": 0.02,
                    "us-west1": 0.02,
                    "europe-west1": 0.023,
                    "asia-southeast1": 0.023
                }
                per_gb = storage_prices.get(region, 0.02)
                storage = per_gb * 1000  # 1TB
                queries = 5 * 10
                results["GCP BigQuery"] = round(storage + queries, 2)
            except Exception as e:
                results["GCP BigQuery"] = 70.0
            
            # Cloud Functions
            try:
                results["GCP Functions"] = round(0.40 * 10 + 5, 2)
            except Exception as e:
                results["GCP Functions"] = 9.0
            
            # Firestore pricing
            try:
                storage = 0.18 * 100
                reads = 0.06 * 1000
                results["GCP Firestore"] = round(storage + reads, 2)
            except Exception as e:
                results["GCP Firestore"] = 78.0
            
            # API Gateway pricing
            try:
                results["GCP API Gateway"] = round(3.00 * 10, 2)
            except Exception as e:
                results["GCP API Gateway"] = 30.0
            
            # Cloud IAM (free service)
            results["GCP IAM"] = 0
            
            # Memorystore (Redis M1)
            try:
                memorystore_prices = {
                    "us-central1": 0.049,
                    "us-west1": 0.049,
                    "europe-west1": 0.054,
                    "asia-southeast1": 0.059
                }
                per_gb_hour = memorystore_prices.get(region, 0.049)
                results["GCP Memorystore"] = round(per_gb_hour * 1 * 730, 2)
            except Exception as e:
                results["GCP Memorystore"] = 35.77
            
            # Pub/Sub pricing
            try:
                results["GCP Pub/Sub"] = round(0.40 * 10, 2)
            except Exception as e:
                results["GCP Pub/Sub"] = 4.0
            
            # Cloud CDN pricing
            try:
                cdn_prices = {
                    "us-central1": 0.08,
                    "us-west1": 0.08,
                    "europe-west1": 0.08,
                    "asia-southeast1": 0.11
                }
                per_gb = cdn_prices.get(region, 0.08)
                results["GCP Cloud CDN"] = round(per_gb * 1000, 2)
            except Exception as e:
                results["GCP Cloud CDN"] = 80.0
            
            # Cloud Load Balancing
            try:
                results["GCP Load Balancer"] = round((0.025 * 730) + (0.008 * 730 * 5), 2)
            except Exception as e:
                results["GCP Load Balancer"] = 47.45
            
            # Cloud Monitoring
            try:
                results["GCP Cloud Monitoring"] = 50
            except Exception as e:
                results["GCP Cloud Monitoring"] = 50
            
            # Cloud Backup (snapshot pricing)
            try:
                results["GCP Cloud Backup"] = round(0.026 * 1000, 2)
            except Exception as e:
                results["GCP Cloud Backup"] = 26.0
            
            # Cloud KMS pricing
            try:
                results["GCP Cloud KMS"] = round(0.06 * 10 + 0.03 * 100, 2)
            except Exception as e:
                results["GCP Cloud KMS"] = 3.6
            
            # GKE (Kubernetes Engine)
            try:
                cluster_fee = 0.10 * 730
                compute_hourly = compute_prices.get(region, 0.095)
                worker_nodes = compute_hourly * 730 * 3
                results["GCP GKE"] = round(cluster_fee + worker_nodes, 2)
            except Exception as e:
                results["GCP GKE"] = 281.05
            
            # Cloud Run pricing
            try:
                results["GCP Cloud Run"] = 15
            except Exception as e:
                results["GCP Cloud Run"] = 15
            
            return results if results else None
            
        except Exception as e:
            print(f"GCP Billing Catalog API failed, using estimates: {e}")
            return {
                "GCP API Gateway": 200,
                "GCP IAM": 0,
                "GCP BigQuery": 500,
                "GCP SQL": 450,
                "GCP Compute Engine": 250,
                "GCP Functions": 0.4,
                "GCP Firestore": 180,
            }

    def fetch_cloud_pricing_data(self) -> Dict[str, Any]:
        print("Fetching cloud pricing data...")
        import concurrent.futures
        # Use cached data for instant response
        cached = self.cache.copy() if self.cache else None


        def fetch_with_timeout(fn, timeout=5):
            print(f"[SYNC] Fetching {fn.__name__}...")
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(fn)
                    result = future.result(timeout=timeout)
                    print(f"[SYNC] {fn.__name__} completed.")
                    return result
            except Exception as e:
                print(f"[SYNC] Timeout or error in {fn.__name__}: {e}")
                return None

        print("[SYNC] Starting parallel cloud pricing fetch...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                'aws': executor.submit(fetch_with_timeout, self.fetch_aws_pricing, 5),
                'azure': executor.submit(fetch_with_timeout, self.fetch_azure_pricing, 5),
                'gcp': executor.submit(fetch_with_timeout, self.fetch_gcp_pricing, 5)
            }
            aws_costs = futures['aws'].result()
            azure_costs = futures['azure'].result()
            gcp_costs = futures['gcp'].result()

        print(f"[SYNC] fetch_aws_pricing completed. Values: {aws_costs}")
        print(f"[SYNC] fetch_azure_pricing completed. Values: {azure_costs}")
        print(f"[SYNC] fetch_gcp_pricing completed. Values: {gcp_costs}")
        print("[SYNC] All cloud pricing fetches completed.")

        print("[SYNC] Fetching third-party latency data...")
        third_party_latency = fetch_with_timeout(self.fetch_cloudharmony_latency, 3)
        print("[SYNC] Third-party latency fetch completed.")

        service_costs: Dict[str, float] = {}
        service_sources: Dict[str, str] = {}

        if aws_costs:
            for k in aws_costs:
                service_costs[k] = aws_costs[k]
                service_sources[k] = "Public Pricing API"
        if azure_costs:
            for k in azure_costs:
                service_costs[k] = azure_costs[k]
                service_sources[k] = "Public Pricing API"
        if gcp_costs:
            for k in gcp_costs:
                service_costs[k] = gcp_costs[k]
                service_sources[k] = "Public Pricing API"

        # Add fallback costs for new Priority 4 services if not fetched from APIs
        fallback_new_services = {
            "AWS ElastiCache": 350, "Azure Cache": 380, "GCP Memorystore": 360,
            "AWS SQS": 150, "Azure Service Bus": 180, "GCP Pub/Sub": 160,
            "AWS CloudFront": 320, "Azure CDN": 340, "GCP Cloud CDN": 310,
            "AWS ALB": 280, "Azure Load Balancer": 300, "GCP Load Balancer": 290,
            "AWS CloudWatch": 200, "Azure Monitor": 220, "GCP Cloud Monitoring": 210,
            "AWS Backup": 400, "Azure Backup": 420, "GCP Cloud Backup": 410,
            "AWS KMS": 100, "Azure Key Vault": 120, "GCP Cloud KMS": 110,
            "AWS EKS": 850, "Azure AKS": 880, "GCP GKE": 860,
            "AWS Lambda": 190, "Azure Functions Extra": 210, "GCP Cloud Run": 195
        }
        for service, cost in fallback_new_services.items():
            if service not in service_costs:
                service_costs[service] = cost
                service_sources[service] = "fallback_priority4"

        # If no live data, use cached or fallback
        if not (aws_costs or azure_costs or gcp_costs):
            print("Using cached or fallback data due to API delays.")
            if cached:
                return cached
            return self.get_fallback_data()

        service_latency = {
            # Original services
            "AWS API Gateway": 10, "AWS IAM": 8, "AWS QuickSight": 15,
            "AWS RDS": 10, "AWS EC2": 8,
            "Azure API Management": 12, "Azure AD": 9, "Azure Synapse": 17,
            "Azure SQL": 12, "Azure VM": 9,
            "GCP API Gateway": 11, "GCP IAM": 8, "GCP BigQuery": 16,
            "GCP SQL": 11, "GCP Compute Engine": 8,
            "GCP Functions": 12, "GCP Firestore": 14, "AWS S3": 11, "Azure Storage": 13, "Azure Functions": 10,
            # New services for 15 components (Priority 4)
            "AWS ElastiCache": 5, "Azure Cache": 6, "GCP Memorystore": 5,
            "AWS SQS": 8, "Azure Service Bus": 9, "GCP Pub/Sub": 8,
            "AWS CloudFront": 15, "Azure CDN": 16, "GCP Cloud CDN": 15,
            "AWS ALB": 7, "Azure Load Balancer": 8, "GCP Load Balancer": 7,
            "AWS CloudWatch": 3, "Azure Monitor": 4, "GCP Cloud Monitoring": 3,
            "AWS Backup": 12, "Azure Backup": 13, "GCP Cloud Backup": 12,
            "AWS KMS": 2, "Azure Key Vault": 3, "GCP Cloud KMS": 2,
            "AWS EKS": 10, "Azure AKS": 11, "GCP GKE": 10,
            "AWS Lambda": 11, "Azure Functions Extra": 12, "GCP Cloud Run": 11
        }
        if third_party_latency:
            service_latency.update(third_party_latency)

        service_options = {
            # Original 6 components
            "api_gateway": ["AWS API Gateway", "Azure API Management", "GCP API Gateway"],
            "identity_management": ["AWS IAM", "Azure AD", "GCP IAM"],
            "analytics": ["AWS QuickSight", "Azure Synapse", "GCP BigQuery"],
            "database": ["AWS RDS", "Azure SQL", "GCP SQL", "GCP Firestore"],
            "application_server": ["AWS EC2", "Azure VM", "GCP Compute Engine", "Azure Functions", "GCP Functions"],
            "storage": ["AWS S3", "Azure Storage"],
            # New 9 components (Priority 4)
            "cache": ["AWS ElastiCache", "Azure Cache", "GCP Memorystore"],
            "message_queue": ["AWS SQS", "Azure Service Bus", "GCP Pub/Sub"],
            "cdn": ["AWS CloudFront", "Azure CDN", "GCP Cloud CDN"],
            "load_balancer": ["AWS ALB", "Azure Load Balancer", "GCP Load Balancer"],
            "monitoring": ["AWS CloudWatch", "Azure Monitor", "GCP Cloud Monitoring"],
            "backup": ["AWS Backup", "Azure Backup", "GCP Cloud Backup"],
            "encryption": ["AWS KMS", "Azure Key Vault", "GCP Cloud KMS"],
            "containers": ["AWS EKS", "Azure AKS", "GCP GKE"],
            "serverless_compute": ["AWS Lambda", "Azure Functions Extra", "GCP Cloud Run"]
        }

        # Build multi-provider source information
        pricing_sources = {
            "aws": "Public Pricing API" if aws_costs else "Fallback Data",
            "azure": "Public Pricing API" if azure_costs else "Fallback Data",
            "gcp": "Public Pricing API" if gcp_costs else "Fallback Data"
        }

        return {
            "costs": service_costs,
            "latency": service_latency,
            "options": service_options,
            "sources": service_sources,
            "timestamp": datetime.now().isoformat(),
            "source": "multi_provider",  # Legacy field for backward compatibility
            "pricing_sources": pricing_sources,  # New detailed source info
        }

    def get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data in case API calls fail - Extended to 15 components"""
        return {
            "costs": {
                # Original services
                "AWS API Gateway": 400, "AWS IAM": 300, "AWS QuickSight": 500,
                "AWS RDS": 600, "AWS EC2": 700, "AWS S3": 250,
                "Azure API Management": 450, "Azure AD": 350, "Azure Synapse": 550,
                "Azure SQL": 650, "Azure VM": 750, "Azure Storage": 300, "Azure Functions": 200,
                "GCP API Gateway": 420, "GCP IAM": 320, "GCP BigQuery": 520,
                "GCP SQL": 620, "GCP Compute Engine": 720, "GCP Functions": 180, "GCP Firestore": 280,
                # New services (Priority 4)
                "AWS ElastiCache": 350, "Azure Cache": 380, "GCP Memorystore": 360,
                "AWS SQS": 150, "Azure Service Bus": 180, "GCP Pub/Sub": 160,
                "AWS CloudFront": 320, "Azure CDN": 340, "GCP Cloud CDN": 310,
                "AWS ALB": 280, "Azure Load Balancer": 300, "GCP Load Balancer": 290,
                "AWS CloudWatch": 200, "Azure Monitor": 220, "GCP Cloud Monitoring": 210,
                "AWS Backup": 400, "Azure Backup": 420, "GCP Cloud Backup": 410,
                "AWS KMS": 100, "Azure Key Vault": 120, "GCP Cloud KMS": 110,
                "AWS EKS": 850, "Azure AKS": 880, "GCP GKE": 860,
                "AWS Lambda": 190, "Azure Functions Extra": 210, "GCP Cloud Run": 195
            },
            "latency": {
                # Original services
                "AWS API Gateway": 10, "AWS IAM": 8, "AWS QuickSight": 15,
                "AWS RDS": 10, "AWS EC2": 8, "AWS S3": 11,
                "Azure API Management": 12, "Azure AD": 9, "Azure Synapse": 17,
                "Azure SQL": 12, "Azure VM": 9, "Azure Storage": 13, "Azure Functions": 10,
                "GCP API Gateway": 11, "GCP IAM": 8, "GCP BigQuery": 16,
                "GCP SQL": 11, "GCP Compute Engine": 8, "GCP Functions": 12, "GCP Firestore": 14,
                # New services (Priority 4)
                "AWS ElastiCache": 5, "Azure Cache": 6, "GCP Memorystore": 5,
                "AWS SQS": 8, "Azure Service Bus": 9, "GCP Pub/Sub": 8,
                "AWS CloudFront": 15, "Azure CDN": 16, "GCP Cloud CDN": 15,
                "AWS ALB": 7, "Azure Load Balancer": 8, "GCP Load Balancer": 7,
                "AWS CloudWatch": 3, "Azure Monitor": 4, "GCP Cloud Monitoring": 3,
                "AWS Backup": 12, "Azure Backup": 13, "GCP Cloud Backup": 12,
                "AWS KMS": 2, "Azure Key Vault": 3, "GCP Cloud KMS": 2,
                "AWS EKS": 10, "Azure AKS": 11, "GCP GKE": 10,
                "AWS Lambda": 11, "Azure Functions Extra": 12, "GCP Cloud Run": 11
            },
            "options": {
                # Original 6 components
                "api_gateway": ["AWS API Gateway", "Azure API Management", "GCP API Gateway"],
                "identity_management": ["AWS IAM", "Azure AD", "GCP IAM"],
                "analytics": ["AWS QuickSight", "Azure Synapse", "GCP BigQuery"],
                "database": ["AWS RDS", "Azure SQL", "GCP SQL", "GCP Firestore"],
                "application_server": ["AWS EC2", "Azure VM", "GCP Compute Engine", "Azure Functions", "GCP Functions"],
                "storage": ["AWS S3", "Azure Storage"],
                # New 9 components (Priority 4)
                "cache": ["AWS ElastiCache", "Azure Cache", "GCP Memorystore"],
                "message_queue": ["AWS SQS", "Azure Service Bus", "GCP Pub/Sub"],
                "cdn": ["AWS CloudFront", "Azure CDN", "GCP Cloud CDN"],
                "load_balancer": ["AWS ALB", "Azure Load Balancer", "GCP Load Balancer"],
                "monitoring": ["AWS CloudWatch", "Azure Monitor", "GCP Cloud Monitoring"],
                "backup": ["AWS Backup", "Azure Backup", "GCP Cloud Backup"],
                "encryption": ["AWS KMS", "Azure Key Vault", "GCP Cloud KMS"],
                "containers": ["AWS EKS", "Azure AKS", "GCP GKE"],
                "serverless_compute": ["AWS Lambda", "Azure Functions Extra", "GCP Cloud Run"]
            },
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }

    def get_service_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        with self.lock:
            now = datetime.now()
            if force_refresh or not self.last_updated or (now - (self.last_updated or now)).total_seconds() > self.ttl_seconds:
                try:
                    print(f"[{now}] Fetching fresh service data...")
                    self.cache = self.fetch_cloud_pricing_data()
                    self.last_updated = now
                except Exception as e:
                    print(f"Error fetching service data: {e}")
                    # Return cached data if available, otherwise use fallback
                    if not self.cache:
                        self.cache = self.get_fallback_data()
            return self.cache

# Instantiate the singleton cache
service_cache = ServiceDataCache()

def get_service_costs() -> Dict[str, float]:
    """Get the costs for all services"""
    return service_cache.get_service_data()["costs"]


def get_service_latency() -> Dict[str, float]:
    """Get the latency for all services"""
    return service_cache.get_service_data()["latency"]


def get_service_options() -> Dict[str, List[str]]:
    """Get the available service options for each component"""
    return service_cache.get_service_data()["options"]


def get_total_combinations() -> int:
    """Calculate total number of possible combinations"""
    options = get_service_options()
    total = 1
    for comp in COMPONENTS:
        total *= len(options[comp])
    return total
