"""
Multi-Agent Processor with Real AWS API Integration
"""

import boto3
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from tag_compliance_agent import TagComplianceAgent

class MultiAgentProcessor:
    def __init__(self):
        """Initialize AWS clients and agents"""
        self.ce = boto3.client('ce')
        self.ec2 = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
        self.lambda_client = boto3.client('lambda')
        self.dynamodb = boto3.resource('dynamodb')
        self.support = boto3.client('support', region_name='us-east-1')
        
        # Initialize specialized agents
        self.tag_compliance_agent = TagComplianceAgent()
        
    def process_prediction_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """Budget Prediction Agent - Real ML predictions"""
        try:
            # Try Lambda first
            response = self.lambda_client.invoke(
                FunctionName='finops-budget-predictor',
                Payload=json.dumps({
                    'days_ahead': 30,
                    'user_id': context.get('user_id', 'unknown')
                })
            )
            
            if response['StatusCode'] == 200:
                result = json.loads(response['Payload'].read())
                body = json.loads(result['body'])
                predictions = body.get('predictions', {})
                
                response_text = f"""📈 **Budget Prediction Analysis Complete!**

Based on your historical AWS spending patterns, here's my forecast:

**30-Day Forecast**:
• Total Predicted Cost: **${predictions['summary']['total_predicted_cost']:,.2f}**
• Daily Average: **${predictions['summary']['average_daily_cost']:,.2f}**
• Trend: **{predictions['summary']['trend'].title()}**
• Confidence Level: **{predictions['summary']['confidence_level']}**

**Weekly Breakdown**:
• Week 1: ${predictions['summary']['total_predicted_cost'] * 0.23:,.2f}
• Week 2: ${predictions['summary']['total_predicted_cost'] * 0.24:,.2f}
• Week 3: ${predictions['summary']['total_predicted_cost'] * 0.26:,.2f}
• Week 4: ${predictions['summary']['total_predicted_cost'] * 0.27:,.2f}

💡 **Recommendation**: {'Consider increasing your budget allocation' if predictions['summary']['trend'] == 'increasing' else 'Your costs are stable, maintain current budget'}."""
                
                return response_text, predictions
        except:
            pass
        
        # Fallback to direct Cost Explorer API
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            # Get historical cost data
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            # Extract costs
            costs = [float(r['Total']['UnblendedCost']['Amount']) for r in response['ResultsByTime']]
            avg_cost = sum(costs) / len(costs) if costs else 100
            
            # Simple trend analysis
            if len(costs) >= 7:
                recent_avg = sum(costs[-7:]) / 7
                older_avg = sum(costs[:-7]) / (len(costs) - 7)
                trend = "increasing" if recent_avg > older_avg * 1.05 else "stable"
            else:
                trend = "stable"
            
            # Calculate predictions
            total_30_day = avg_cost * 30
            
            response_text = f"""📈 **Budget Prediction Analysis Complete!**

Based on your last 30 days of AWS spending:

**30-Day Forecast**:
• Total Predicted Cost: **${total_30_day:,.2f}**
• Daily Average: **${avg_cost:,.2f}**
• Current Trend: **{trend}**
• Based on: {len(costs)} days of historical data

**Monthly Breakdown**:
• Week 1: ${total_30_day * 0.23:,.2f}
• Week 2: ${total_30_day * 0.24:,.2f}
• Week 3: ${total_30_day * 0.26:,.2f}
• Week 4: ${total_30_day * 0.27:,.2f}

**Cost Analysis**:
• Highest Daily Cost: ${max(costs):,.2f}
• Lowest Daily Cost: ${min(costs):,.2f}
• Cost Variance: {((max(costs) - min(costs)) / avg_cost * 100):.1f}%

💡 **Tip**: Enable AWS Budgets for automatic cost alerts."""
            
            return response_text, {"total": total_30_day, "daily_avg": avg_cost, "trend": trend}
            
        except Exception as e:
            return f"Error getting prediction: {str(e)}", {}
    
    def process_optimizer_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """Resource Optimization Agent - Real resource scanning"""
        try:
            # Try Lambda first
            response = self.lambda_client.invoke(
                FunctionName='finops-resource-optimizer',
                Payload=json.dumps({
                    'scan_days': 7,
                    'user_id': context.get('user_id', 'unknown')
                })
            )
            
            if response['StatusCode'] == 200:
                result = json.loads(response['Payload'].read())
                body = json.loads(result['body'])
                opt_results = body.get('optimization_results', {})
                
                response_text = f"""🔍 **Resource Optimization Scan Complete!**

I've identified the following optimization opportunities:

**Idle Resources Found**:
• Stopped EC2 Instances: **{opt_results['summary']['stopped_instances_count']}**
• Unattached EBS Volumes: **{opt_results['summary']['unattached_volumes_count']}**
• Unused Elastic IPs: **{opt_results['summary']['unused_eips_count']}**
• Underutilized Instances: **{opt_results['summary']['underutilized_instances_count']}**

💰 **Potential Monthly Savings**: **${opt_results['total_monthly_savings']:,.2f}**

**Top Recommendations**:
1. Clean up unattached EBS volumes
2. Release unused Elastic IPs
3. Terminate stopped instances not needed
4. Right-size underutilized instances

Would you like me to generate a cleanup script?"""
                
                return response_text, opt_results
        except:
            pass
        
        # Fallback to direct EC2/CloudWatch scan
        try:
            opt_results = {
                'stopped_instances': [],
                'unattached_volumes': [],
                'unused_eips': [],
                'underutilized_instances': [],
                'orphaned_snapshots': [],
                'total_monthly_savings': 0.0
            }
            
            # 1. Scan stopped EC2 instances
            instances = self.ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'stopped':
                        # Get EBS storage size
                        storage_gb = sum(vol.get('Size', 8) for vol in instance.get('BlockDeviceMappings', []))
                        monthly_cost = storage_gb * 0.10
                        
                        opt_results['stopped_instances'].append({
                            'instance_id': instance['InstanceId'],
                            'instance_type': instance['InstanceType'],
                            'storage_gb': storage_gb,
                            'monthly_cost': round(monthly_cost, 2)
                        })
                        opt_results['total_monthly_savings'] += monthly_cost
            
            # 2. Scan unattached volumes
            volumes = self.ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )
            for vol in volumes['Volumes']:
                monthly_cost = vol['Size'] * 0.10
                opt_results['unattached_volumes'].append({
                    'volume_id': vol['VolumeId'],
                    'size_gb': vol['Size'],
                    'monthly_cost': round(monthly_cost, 2)
                })
                opt_results['total_monthly_savings'] += monthly_cost
            
            # 3. Scan unused Elastic IPs
            addresses = self.ec2.describe_addresses()
            for addr in addresses['Addresses']:
                if 'InstanceId' not in addr and 'NetworkInterfaceId' not in addr:
                    monthly_cost = 3.6  # $0.005/hour * 720 hours
                    opt_results['unused_eips'].append({
                        'public_ip': addr['PublicIp'],
                        'monthly_cost': monthly_cost
                    })
                    opt_results['total_monthly_savings'] += monthly_cost
            
            # 4. Check underutilized instances
            running_instances = self.ec2.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            for reservation in running_instances['Reservations']:
                for instance in reservation['Instances']:
                    try:
                        # Get CPU utilization
                        cpu_stats = self.cloudwatch.get_metric_statistics(
                            Namespace='AWS/EC2',
                            MetricName='CPUUtilization',
                            Dimensions=[{'Name': 'InstanceId', 'Value': instance['InstanceId']}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['Average']
                        )
                        
                        if cpu_stats['Datapoints']:
                            avg_cpu = sum(dp['Average'] for dp in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
                            if avg_cpu < 10:
                                opt_results['underutilized_instances'].append({
                                    'instance_id': instance['InstanceId'],
                                    'instance_type': instance['InstanceType'],
                                    'avg_cpu_percent': round(avg_cpu, 2)
                                })
                    except:
                        pass
            
            # 5. Scan orphaned snapshots
            try:
                snapshots = self.ec2.describe_snapshots(OwnerIds=['self'])
                volumes = self.ec2.describe_volumes()
                volume_ids = [v['VolumeId'] for v in volumes['Volumes']]
                
                for snapshot in snapshots['Snapshots']:
                    # Check if snapshot's volume still exists
                    if snapshot.get('VolumeId') and snapshot['VolumeId'] not in volume_ids:
                        size_gb = snapshot.get('VolumeSize', 0)
                        monthly_cost = size_gb * 0.05  # $0.05 per GB-month for snapshots
                        opt_results['orphaned_snapshots'].append({
                            'snapshot_id': snapshot['SnapshotId'],
                            'size_gb': size_gb,
                            'volume_id': snapshot['VolumeId'],  # No longer exists
                            'start_time': snapshot.get('StartTime', '').isoformat() if 'StartTime' in snapshot else 'Unknown',
                            'monthly_cost': round(monthly_cost, 2)
                        })
                        opt_results['total_monthly_savings'] += monthly_cost
            except:
                pass
            
            # Add summary
            opt_results['summary'] = {
                'stopped_instances_count': len(opt_results['stopped_instances']),
                'unattached_volumes_count': len(opt_results['unattached_volumes']),
                'unused_eips_count': len(opt_results['unused_eips']),
                'underutilized_instances_count': len(opt_results['underutilized_instances']),
                'orphaned_snapshots_count': len(opt_results['orphaned_snapshots'])
            }
            opt_results['total_monthly_savings'] = round(opt_results['total_monthly_savings'], 2)
            
            response_text = f"""🔍 **Resource Optimization Scan Complete!**

Here's what I found in your AWS account:

**Resource Summary**:
• Stopped EC2 Instances: **{opt_results['summary']['stopped_instances_count']}**
• Unattached EBS Volumes: **{opt_results['summary']['unattached_volumes_count']}**
• Unused Elastic IPs: **{opt_results['summary']['unused_eips_count']}**
• Underutilized Instances: **{opt_results['summary']['underutilized_instances_count']}**
• Orphaned Snapshots: **{opt_results['summary']['orphaned_snapshots_count']}**

💰 **Estimated Monthly Waste**: **${opt_results['total_monthly_savings']:.2f}**

**Quick Actions**:
1. **Stopped Instances**: ${sum(i['monthly_cost'] for i in opt_results['stopped_instances']):.2f}/month
2. **Unattached Volumes**: ${sum(v['monthly_cost'] for v in opt_results['unattached_volumes']):.2f}/month
3. **Unused EIPs**: ${sum(e['monthly_cost'] for e in opt_results['unused_eips']):.2f}/month

💡 **Annual Savings Potential**: ${opt_results['total_monthly_savings'] * 12:.2f}"""
            
            return response_text, opt_results
            
        except Exception as e:
            return f"Error during optimization scan: {str(e)}", {}
    
    def process_savings_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """Savings Plan Agent - Real recommendations"""
        # Get Savings Plan recommendations - NO FALLBACK
        recommendations = self.ce.get_savings_plans_purchase_recommendation(
            SavingsPlansType='COMPUTE_SP',
            TermInYears='ONE_YEAR',
            PaymentOption='ALL_UPFRONT',
            LookbackPeriodInDays='SIXTY_DAYS'
        )
        
        if 'SavingsPlansPurchaseRecommendation' in recommendations:
            rec = recommendations['SavingsPlansPurchaseRecommendation']
            hourly = float(rec.get('HourlyCommitmentToPurchase', 0))
            savings = float(rec.get('EstimatedSavingsAmount', 0))
            
            if hourly > 0:
                response_text = f"""💎 **Savings Plan Recommendation Ready!**

Based on your last 60 days of usage:

**Recommended Commitment**:
• Hourly Commitment: **${hourly:.2f}/hour**
• Annual Commitment: **${hourly * 8760:,.2f}**
• Estimated Annual Savings: **${savings:,.2f}**
• ROI: **{(savings / (hourly * 8760) * 100):.1f}%**

**Plan Details**:
• Type: Compute Savings Plan
• Term: 1 Year
• Payment: All Upfront (best discount)

**Coverage Analysis**:
Your current on-demand spend would be reduced by approximately {(savings / (hourly * 8760) * 100):.0f}%

💡 **Next Step**: Review and purchase in AWS Console > Cost Management > Savings Plans"""
            else:
                response_text = """💎 **Savings Plan Analysis Complete!**

Your current usage pattern doesn't show significant opportunity for Savings Plans at this time.

**Why?**
• Low or irregular compute usage
• Already have good coverage
• Usage pattern is too variable

💡 **Alternative Recommendations**:
1. Consider Spot Instances for fault-tolerant workloads
2. Use Auto Scaling to optimize capacity
3. Review Reserved Instances for steady-state workloads"""
            
            return response_text, {"hourly": hourly, "savings": savings}
        else:
            raise Exception("Savings Plan recommendation data not available")
    
    def process_anomaly_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """Anomaly Detection Agent - Real anomaly detection"""
        # Get last 7 days of costs - NO FALLBACK
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # Analyze for anomalies
        daily_totals = []
        service_spikes = []
        
        for i, result in enumerate(response['ResultsByTime']):
            daily_total = sum(float(g['Metrics']['UnblendedCost']['Amount']) 
                            for g in result['Groups'])
            daily_totals.append(daily_total)
            
            # Check for service-level spikes
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if i > 0 and cost > 50:  # Significant cost
                    prev_result = response['ResultsByTime'][i-1]
                    prev_cost = next((float(g['Metrics']['UnblendedCost']['Amount']) 
                                    for g in prev_result['Groups'] 
                                    if g['Keys'][0] == service), 0)
                    if prev_cost > 0 and cost > prev_cost * 1.5:  # 50% increase
                        service_spikes.append({
                            'service': service,
                            'date': result['TimePeriod']['Start'],
                            'increase': ((cost - prev_cost) / prev_cost * 100)
                        })
        
        # Calculate statistics
        avg_daily = sum(daily_totals) / len(daily_totals) if daily_totals else 0
        max_daily = max(daily_totals) if daily_totals else 0
        
        anomalies_found = len(service_spikes) > 0 or (max_daily > avg_daily * 1.5)
        
        if anomalies_found:
            response_text = f"""🚨 **Cost Anomaly Detection Results**

⚠️ I've detected unusual spending patterns:

**Daily Cost Analysis** (Last 7 days):
• Average Daily Cost: ${avg_daily:.2f}
• Highest Daily Cost: ${max_daily:.2f}
• Variation: {((max_daily - avg_daily) / avg_daily * 100):.1f}% above average

**Service-Level Anomalies**:"""
            
            for spike in service_spikes[:3]:
                response_text += f"\n• **{spike['service']}**: {spike['increase']:.0f}% increase on {spike['date']}"
            
            response_text += """

**Recommended Actions**:
1. Review the services with cost spikes
2. Check for unused resources that were created
3. Verify no unauthorized usage
4. Set up CloudWatch billing alerts

Would you like me to investigate a specific service?"""
        else:
            response_text = f"""✅ **Cost Anomaly Detection Results**

Good news! No significant anomalies detected.

**Daily Cost Analysis** (Last 7 days):
• Average Daily Cost: ${avg_daily:.2f}
• Maximum Daily Cost: ${max_daily:.2f}
• Cost Stability: ✅ Normal variation

**Status**: Your spending patterns are consistent and predictable.

💡 **Proactive Tips**:
1. Set up billing alerts at ${avg_daily * 1.5:.2f}/day
2. Enable AWS Budgets for automatic notifications
3. Review costs weekly to catch issues early"""
        
        return response_text, {"anomalies": len(service_spikes), "avg_daily": avg_daily}
    
    def process_general_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """General FinOps Assistant - Cost overview and guidance"""
        # Get current month costs with DAILY granularity for better accuracy
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1).date()
        # AWS Cost Explorer requires end date to be after start date
        end_date = now.date() + timedelta(days=1)
        
        # Use DAILY granularity and aggregate
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        if response['ResultsByTime']:
            # Aggregate costs by service across all days
            service_costs = {}
            total_cost = 0.0
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service not in service_costs:
                        service_costs[service] = 0.0
                    service_costs[service] += cost
                    total_cost += cost
            
            # Get top 5 services
            services = list(service_costs.items())
            services.sort(key=lambda x: x[1], reverse=True)
            top_services = services[:5]
            
            days_elapsed = (end_date - start_date).days
            daily_avg = total_cost / max(1, days_elapsed)
            projected_monthly = daily_avg * 30
            
            response_text = f"""💰 **AWS Cost Overview**

Here's your current month summary:

**Month-to-Date Spend**: ${total_cost:,.2f}
**Days Elapsed**: {days_elapsed}
**Daily Average**: ${daily_avg:.2f}
**Projected Monthly**: ${projected_monthly:,.2f}

**Top 5 Services by Cost**:"""
            
            for service, cost in top_services:
                pct = (cost / total_cost * 100) if total_cost > 0 else 0
                response_text += f"\n• {service}: ${cost:.2f} ({pct:.1f}%)"
            
            response_text += """

**Available Actions**:
- Ask me to "predict next month's costs"
- Say "find idle resources" to save money
- Request "savings plan recommendations"
- Check for "cost anomalies"

What would you like to explore?"""
            
            return response_text, {"total_cost": total_cost, "top_services": top_services}
        else:
            raise Exception("No cost data available for current month")
            
    def process_general_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """General FinOps query processor with tag compliance routing"""
        # Check for tag compliance queries first
        query_lower = query.lower()
        if any(word in query_lower for word in ['tag', 'compliance', 'untagged', 'missing tags']):
            return self.tag_compliance_agent.process_query(query, context)
        
        # Otherwise process as regular cost query
        return self._process_cost_query(query, context)
    
    def _process_cost_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """Process regular cost queries"""
        # This is the original general query logic
        try:
            # Get current month costs
            today = datetime.now()
            start_date = today.replace(day=1)
            end_date = today
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Aggregate costs by service across all days
            service_costs = {}
            total_cost = 0.0
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service not in service_costs:
                        service_costs[service] = 0.0
                    service_costs[service] += cost
                    total_cost += cost
            
            # Get top 5 services
            services = list(service_costs.items())
            services.sort(key=lambda x: x[1], reverse=True)
            top_services = services[:5]
            
            days_elapsed = (end_date - start_date).days
            daily_avg = total_cost / max(1, days_elapsed)
            projected_monthly = daily_avg * 30
            
            response_text = f"""💰 **AWS Cost Overview**

Here's your current month summary:

**Month-to-Date Spend**: ${total_cost:,.2f}
**Days Elapsed**: {days_elapsed}
**Daily Average**: ${daily_avg:.2f}
**Projected Monthly**: ${projected_monthly:,.2f}

**Top 5 Services by Cost**:"""
            
            for service, cost in top_services:
                pct = (cost / total_cost * 100) if total_cost > 0 else 0
                response_text += f"\n• {service}: ${cost:.2f} ({pct:.1f}%)"
            
            response_text += """

**Available Actions**:
- Ask me to "predict next month's costs"
- Say "find idle resources" to save money
- Request "savings plan recommendations"
- Check for "cost anomalies"

What would you like to explore?"""
            
            return response_text, {"total_cost": total_cost, "top_services": top_services}
        
        except Exception as e:
            return f"I encountered an error while fetching cost data: {str(e)}", {}