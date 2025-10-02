#!/usr/bin/env python3
"""
Tag Compliance AI Agent
Provides intelligent tag compliance analysis and recommendations
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

class TagComplianceAgent:
    """
    AI Agent for resource tag compliance management
    """
    
    def __init__(self):
        """
        Initialize the Tag Compliance Agent
        """
        self.ec2 = boto3.client('ec2')
        self.rds = boto3.client('rds')
        self.s3 = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')
        self.resource_tagging = boto3.client('resourcegroupstaggingapi')
        self.dynamodb = boto3.resource('dynamodb')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Required tags for compliance
        self.required_tags = ['Environment', 'Owner', 'CostCenter', 'Project']
        
        # Tag recommendations based on resource type
        self.tag_recommendations = {
            'ec2:instance': {
                'additional_recommended': ['Application', 'Team', 'Backup'],
                'naming_pattern': {
                    'Environment': ['dev', 'staging', 'prod', 'test'],
                    'Owner': 'email@company.com format',
                    'CostCenter': 'CC-XXXX format',
                    'Project': 'PROJECT-NAME format'
                }
            },
            'rds:instance': {
                'additional_recommended': ['BackupPolicy', 'DataClassification', 'MaintenanceWindow'],
                'naming_pattern': {
                    'Environment': ['dev', 'staging', 'prod', 'test'],
                    'DataClassification': ['public', 'internal', 'confidential', 'restricted']
                }
            },
            's3:bucket': {
                'additional_recommended': ['DataClassification', 'RetentionPolicy', 'AccessLevel'],
                'naming_pattern': {
                    'DataClassification': ['public', 'internal', 'confidential', 'restricted'],
                    'RetentionPolicy': ['7days', '30days', '90days', '1year', 'indefinite']
                }
            }
        }
    
    def process_query(self, query: str, context: Dict) -> Tuple[str, Dict]:
        """
        Process tag compliance related queries
        
        Args:
            query: User query
            context: Context information
            
        Returns:
            Response text and data
        """
        query_lower = query.lower()
        
        # Determine query intent
        if any(word in query_lower for word in ['scan', 'check', 'compliance', 'audit']):
            return self.perform_compliance_scan()
        elif any(word in query_lower for word in ['untagged', 'missing tags', 'non-compliant']):
            return self.find_untagged_resources()
        elif any(word in query_lower for word in ['fix', 'remediate', 'apply tags', 'tag resources']):
            return self.suggest_remediation()
        elif any(word in query_lower for word in ['report', 'summary', 'status']):
            return self.generate_compliance_report()
        elif any(word in query_lower for word in ['cost', 'impact', 'savings']):
            return self.analyze_cost_impact()
        elif any(word in query_lower for word in ['trend', 'history', 'improvement']):
            return self.analyze_compliance_trends()
        elif any(word in query_lower for word in ['policy', 'enforce', 'automate']):
            return self.suggest_tag_policies()
        else:
            return self.general_tag_guidance()
    
    def perform_compliance_scan(self) -> Tuple[str, Dict]:
        """
        Perform a comprehensive tag compliance scan
        """
        try:
            # Invoke Lambda function for detailed scan
            response = self.lambda_client.invoke(
                FunctionName='tag-compliance-checker',
                InvocationType='RequestResponse',
                Payload=json.dumps({'action': 'scan'})
            )
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                scan_data = json.loads(result['body'])
                
                # Generate response
                compliance_rate = scan_data.get('compliance_rate', 0)
                total_resources = scan_data.get('total_resources', 0)
                non_compliant = scan_data.get('non_compliant_count', 0)
                
                response_text = f"""
🔍 **Tag Compliance Scan Complete**

📊 **Overall Compliance Rate: {compliance_rate:.1f}%**

**Summary:**
• Total Resources Scanned: {total_resources}
• Compliant Resources: {scan_data.get('compliant_count', 0)} ✅
• Non-Compliant Resources: {non_compliant} ⚠️

**Missing Tags Breakdown:**
"""
                
                # Add missing tags summary
                missing_tags = scan_data.get('missing_tags_summary', {})
                for tag, count in sorted(missing_tags.items(), key=lambda x: x[1], reverse=True):
                    response_text += f"• {tag}: {count} resources missing this tag\n"
                
                # Add resource type breakdown
                response_text += "\n**Non-Compliance by Resource Type:**\n"
                resources_by_type = scan_data.get('resources_by_type', {})
                for res_type, counts in sorted(resources_by_type.items(), 
                                              key=lambda x: x[1].get('non_compliant', 0), 
                                              reverse=True)[:5]:
                    if counts.get('non_compliant', 0) > 0:
                        response_text += f"• {res_type}: {counts['non_compliant']}/{counts['total']} resources\n"
                
                # Add recommendations
                if compliance_rate < 80:
                    response_text += "\n⚠️ **Action Required:** Compliance rate is below 80%. "
                    response_text += "Consider implementing automated tagging policies."
                elif compliance_rate < 95:
                    response_text += "\n💡 **Recommendation:** Good progress! Focus on the remaining "
                    response_text += f"{non_compliant} resources to achieve full compliance."
                else:
                    response_text += "\n✅ **Excellent!** Your tagging compliance is very good."
                
                # Cost impact
                if 'summary' in scan_data and 'cost_impact' in scan_data['summary']:
                    cost_impact = scan_data['summary']['cost_impact']
                    response_text += f"\n\n💰 **Estimated Cost Impact:** ${cost_impact:,.2f}/month "
                    response_text += "for untagged resources (affects cost allocation accuracy)"
                
                return response_text, scan_data
            else:
                return "Error performing compliance scan. Please try again.", {}
                
        except Exception as e:
            # Fallback to direct scanning
            return self._direct_compliance_scan()
    
    def find_untagged_resources(self) -> Tuple[str, Dict]:
        """
        Find and report untagged resources
        """
        try:
            untagged_resources = []
            
            # Check EC2 instances
            instances = self.ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        missing_tags = [tag for tag in self.required_tags if tag not in tags]
                        
                        if missing_tags:
                            untagged_resources.append({
                                'type': 'EC2 Instance',
                                'id': instance['InstanceId'],
                                'name': tags.get('Name', 'Unnamed'),
                                'missing_tags': missing_tags,
                                'state': instance['State']['Name'],
                                'instance_type': instance.get('InstanceType', 'unknown')
                            })
            
            # Check EBS volumes
            volumes = self.ec2.describe_volumes()
            for volume in volumes['Volumes']:
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                missing_tags = [tag for tag in self.required_tags if tag not in tags]
                
                if missing_tags:
                    untagged_resources.append({
                        'type': 'EBS Volume',
                        'id': volume['VolumeId'],
                        'name': tags.get('Name', 'Unnamed'),
                        'missing_tags': missing_tags,
                        'state': volume['State'],
                        'size': f"{volume['Size']} GB"
                    })
            
            # Generate response
            if not untagged_resources:
                return "✅ Great news! All resources are properly tagged.", {'compliant': True}
            
            response_text = f"⚠️ **Found {len(untagged_resources)} resources with missing tags:**\n\n"
            
            # Group by resource type
            by_type = {}
            for resource in untagged_resources:
                res_type = resource['type']
                if res_type not in by_type:
                    by_type[res_type] = []
                by_type[res_type].append(resource)
            
            # Show top 10 resources
            shown_count = 0
            for res_type, resources in by_type.items():
                response_text += f"**{res_type}s:**\n"
                for resource in resources[:5]:
                    response_text += f"• {resource['id']} ({resource['name']})\n"
                    response_text += f"  Missing: {', '.join(resource['missing_tags'])}\n"
                    if 'instance_type' in resource:
                        response_text += f"  Type: {resource['instance_type']}, State: {resource['state']}\n"
                    shown_count += 1
                    if shown_count >= 10:
                        break
                if shown_count >= 10:
                    break
            
            if len(untagged_resources) > 10:
                response_text += f"\n... and {len(untagged_resources) - 10} more resources\n"
            
            response_text += "\n💡 **Quick Actions:**\n"
            response_text += "1. Use 'apply tags to resources' to auto-remediate\n"
            response_text += "2. Export full list with 'generate tagging report'\n"
            response_text += "3. Set up tag policies with 'create tag enforcement policy'"
            
            return response_text, {
                'untagged_resources': untagged_resources,
                'total_count': len(untagged_resources),
                'by_type': {k: len(v) for k, v in by_type.items()}
            }
            
        except Exception as e:
            return f"Error finding untagged resources: {str(e)}", {}
    
    def suggest_remediation(self) -> Tuple[str, Dict]:
        """
        Suggest tag remediation actions
        """
        try:
            # Get current non-compliant resources
            _, scan_data = self.find_untagged_resources()
            
            if not scan_data.get('untagged_resources'):
                return "✅ All resources are already tagged! No remediation needed.", {}
            
            untagged_resources = scan_data['untagged_resources']
            total_count = len(untagged_resources)
            
            response_text = f"""
🔧 **Tag Remediation Plan**

**Resources Requiring Tags:** {total_count}

**Recommended Approach:**

1️⃣ **Automated Tagging (Recommended)**
   • Apply default tags to all untagged resources
   • Default values:
     - Environment: 'production' (for running instances)
     - Owner: 'unassigned' (requires manual update)
     - CostCenter: 'CC-0000' (requires finance team input)
     - Project: 'unassigned' (requires project manager input)

2️⃣ **Bulk Tagging by Resource Type**
"""
            
            # Group recommendations by type
            by_type = scan_data.get('by_type', {})
            for res_type, count in by_type.items():
                response_text += f"   • {res_type}: {count} resources\n"
            
            response_text += """
3️⃣ **Tag Templates by Resource Type**
"""
            
            # Provide specific templates
            if 'EC2 Instance' in by_type:
                response_text += """
   **EC2 Instances:**
   ```
   Environment: [dev|staging|prod]
   Owner: [email@company.com]
   CostCenter: [CC-XXXX]
   Project: [project-name]
   Application: [app-name]
   Team: [team-name]
   ```
"""
            
            if 'RDS Instance' in by_type:
                response_text += """
   **RDS Instances:**
   ```
   Environment: [dev|staging|prod]
   Owner: [dba-email@company.com]
   CostCenter: [CC-XXXX]
   Project: [project-name]
   DataClassification: [public|internal|confidential]
   BackupPolicy: [daily|weekly|monthly]
   ```
"""
            
            response_text += """
4️⃣ **Enforcement Strategy**
   • Enable AWS Config rules for tag compliance
   • Set up Lambda function for auto-tagging new resources
   • Create IAM policy requiring tags for resource creation
   • Set up daily compliance reports

**Next Steps:**
• Type 'apply default tags' to start automated remediation
• Type 'export tagging template' to get CSV template for bulk updates
• Type 'create tag policy' to set up enforcement
"""
            
            remediation_plan = {
                'total_resources': total_count,
                'by_type': by_type,
                'estimated_time': f"{total_count * 0.5:.0f} minutes for manual tagging",
                'automation_available': True,
                'default_tags': {
                    'Environment': 'production',
                    'Owner': 'unassigned',
                    'CostCenter': 'CC-0000',
                    'Project': 'unassigned'
                }
            }
            
            return response_text, remediation_plan
            
        except Exception as e:
            return f"Error generating remediation suggestions: {str(e)}", {}
    
    def generate_compliance_report(self) -> Tuple[str, Dict]:
        """
        Generate a tag compliance report
        """
        try:
            # Get comprehensive compliance data
            response = self.lambda_client.invoke(
                FunctionName='tag-compliance-checker',
                InvocationType='RequestResponse',
                Payload=json.dumps({'action': 'report', 'report_type': 'detailed'})
            )
            
            result = json.loads(response['Payload'].read())
            report_data = json.loads(result['body'])
            
            # Generate report summary
            scan_results = report_data.get('scan_results', {})
            
            response_text = f"""
📊 **Tag Compliance Report**

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Executive Summary:**
• Overall Compliance Rate: {scan_results.get('compliance_rate', 0):.1f}%
• Total Resources: {scan_results.get('total_resources', 0)}
• Compliant Resources: {scan_results.get('compliant_count', 0)}
• Non-Compliant Resources: {scan_results.get('non_compliant_count', 0)}

**Compliance by Resource Type:**
"""
            
            # Add resource type breakdown
            resources_by_type = scan_results.get('resources_by_type', {})
            for res_type, counts in sorted(resources_by_type.items()):
                if counts['total'] > 0:
                    compliance_rate = (counts['compliant'] / counts['total'] * 100)
                    response_text += f"• {res_type}: {compliance_rate:.1f}% "
                    response_text += f"({counts['compliant']}/{counts['total']})\n"
            
            response_text += "\n**Tag Coverage Analysis:**\n"
            
            # Tag coverage
            missing_tags_summary = scan_results.get('missing_tags_summary', {})
            for tag in self.required_tags:
                missing_count = missing_tags_summary.get(tag, 0)
                coverage = ((scan_results.get('total_resources', 0) - missing_count) / 
                           scan_results.get('total_resources', 1) * 100)
                response_text += f"• {tag}: {coverage:.1f}% coverage\n"
            
            # High-risk resources
            if 'summary' in scan_results:
                high_risk_count = len(scan_results['summary'].get('high_risk_resources', []))
                if high_risk_count > 0:
                    response_text += f"\n⚠️ **High Risk:** {high_risk_count} critical resources "
                    response_text += "are missing tags (production systems, databases, etc.)\n"
            
            # Cost impact
            if 'summary' in scan_results and 'cost_impact' in scan_results['summary']:
                cost_impact = scan_results['summary']['cost_impact']
                annual_impact = cost_impact * 12
                response_text += f"\n💰 **Financial Impact:**\n"
                response_text += f"• Monthly: ${cost_impact:,.2f}\n"
                response_text += f"• Annual: ${annual_impact:,.2f}\n"
                response_text += "• Impact: Inaccurate cost allocation and chargebacks\n"
            
            response_text += """
📥 **Export Options:**
• Type 'download compliance report' for detailed PDF
• Type 'export non-compliant list' for CSV of untagged resources
• Type 'show compliance trends' for historical analysis
"""
            
            return response_text, report_data
            
        except Exception as e:
            return f"Error generating compliance report: {str(e)}", {}
    
    def analyze_cost_impact(self) -> Tuple[str, Dict]:
        """
        Analyze the cost impact of non-compliant resources
        """
        try:
            # Get non-compliant resources
            _, scan_data = self.find_untagged_resources()
            untagged_resources = scan_data.get('untagged_resources', [])
            
            if not untagged_resources:
                return "✅ All resources are tagged. No cost allocation issues!", {}
            
            # Estimate costs for untagged resources
            total_monthly_cost = 0
            cost_breakdown = {}
            
            # EC2 instances
            ec2_resources = [r for r in untagged_resources if r['type'] == 'EC2 Instance']
            for resource in ec2_resources:
                # Estimate based on instance type
                instance_type = resource.get('instance_type', 't3.micro')
                monthly_cost = self._estimate_instance_cost(instance_type)
                total_monthly_cost += monthly_cost
                
                if 'EC2 Instances' not in cost_breakdown:
                    cost_breakdown['EC2 Instances'] = {
                        'count': 0,
                        'monthly_cost': 0,
                        'resources': []
                    }
                
                cost_breakdown['EC2 Instances']['count'] += 1
                cost_breakdown['EC2 Instances']['monthly_cost'] += monthly_cost
                cost_breakdown['EC2 Instances']['resources'].append({
                    'id': resource['id'],
                    'type': instance_type,
                    'cost': monthly_cost
                })
            
            # EBS volumes
            ebs_resources = [r for r in untagged_resources if r['type'] == 'EBS Volume']
            for resource in ebs_resources:
                # Extract size from the resource
                size_str = resource.get('size', '0 GB')
                size_gb = int(size_str.split()[0]) if size_str else 0
                monthly_cost = size_gb * 0.10  # $0.10 per GB-month for gp2
                total_monthly_cost += monthly_cost
                
                if 'EBS Volumes' not in cost_breakdown:
                    cost_breakdown['EBS Volumes'] = {
                        'count': 0,
                        'monthly_cost': 0,
                        'total_size_gb': 0
                    }
                
                cost_breakdown['EBS Volumes']['count'] += 1
                cost_breakdown['EBS Volumes']['monthly_cost'] += monthly_cost
                cost_breakdown['EBS Volumes']['total_size_gb'] += size_gb
            
            # Generate response
            response_text = f"""
💰 **Cost Impact Analysis - Untagged Resources**

**Total Monthly Cost of Untagged Resources:** ${total_monthly_cost:,.2f}
**Annual Cost:** ${total_monthly_cost * 12:,.2f}

**Impact on Cost Management:**
• ❌ Cannot allocate ${total_monthly_cost:,.2f}/month to proper cost centers
• ❌ Unable to track project-specific spending
• ❌ No owner accountability for resource optimization
• ❌ Impossible to identify unused or underutilized resources by team

**Cost Breakdown by Resource Type:**
"""
            
            for res_type, details in cost_breakdown.items():
                response_text += f"\n**{res_type}:**\n"
                response_text += f"• Count: {details['count']}\n"
                response_text += f"• Monthly Cost: ${details['monthly_cost']:,.2f}\n"
                
                if res_type == 'EBS Volumes':
                    response_text += f"• Total Storage: {details['total_size_gb']} GB\n"
                elif res_type == 'EC2 Instances' and details['resources']:
                    # Show top 3 most expensive
                    top_instances = sorted(details['resources'], 
                                         key=lambda x: x['cost'], 
                                         reverse=True)[:3]
                    response_text += "• Top Cost Instances:\n"
                    for inst in top_instances:
                        response_text += f"  - {inst['id']} ({inst['type']}): "
                        response_text += f"${inst['cost']:.2f}/month\n"
            
            response_text += f"""
**Business Impact:**
• 📊 **Budgeting:** Cannot accurately forecast departmental costs
• 💸 **Chargebacks:** Unable to bill internal customers correctly
• 📈 **Optimization:** Missing savings opportunities worth ~{total_monthly_cost * 0.3:.0f}/month
• 🎯 **Compliance:** Failing audit requirements for cost tracking

**Recommended Actions:**
1. Tag all resources immediately to enable cost tracking
2. Set up automated tagging for new resources
3. Implement tag-based cost allocation reports
4. Create departmental dashboards based on tags
"""
            
            cost_impact_data = {
                'total_monthly_cost': total_monthly_cost,
                'annual_cost': total_monthly_cost * 12,
                'cost_breakdown': cost_breakdown,
                'potential_savings': total_monthly_cost * 0.3,  # 30% typical savings
                'unallocated_percentage': (total_monthly_cost / 
                                          (total_monthly_cost + 1000) * 100)  # Assume $1000 tagged
            }
            
            return response_text, cost_impact_data
            
        except Exception as e:
            return f"Error analyzing cost impact: {str(e)}", {}
    
    def analyze_compliance_trends(self) -> Tuple[str, Dict]:
        """
        Analyze tag compliance trends over time
        """
        try:
            # Get historical compliance data from Lambda/DynamoDB
            response = self.lambda_client.invoke(
                FunctionName='tag-compliance-checker',
                InvocationType='RequestResponse',
                Payload=json.dumps({'action': 'report', 'report_type': 'trends'})
            )
            
            result = json.loads(response['Payload'].read())
            trends_data = json.loads(result['body'])
            
            trends = trends_data.get('trends', [])
            
            if not trends:
                return "📊 No historical trend data available yet. Run regular scans to build trends.", {}
            
            # Analyze trends
            recent_rate = trends[0]['compliance_rate'] if trends else 0
            oldest_rate = trends[-1]['compliance_rate'] if trends else 0
            improvement = recent_rate - oldest_rate
            
            # Calculate average improvement rate
            if len(trends) > 1:
                daily_improvement = improvement / len(trends)
            else:
                daily_improvement = 0
            
            response_text = f"""
📈 **Tag Compliance Trend Analysis**

**Current Compliance Rate:** {recent_rate:.1f}%
**Historical Low:** {min(t['compliance_rate'] for t in trends):.1f}%
**Historical High:** {max(t['compliance_rate'] for t in trends):.1f}%

**Trend Summary:**
• Overall Change: {improvement:+.1f}% over {len(trends)} scans
• Average Daily Change: {daily_improvement:+.2f}%
• Trend Direction: {'📈 Improving' if improvement > 0 else '📉 Declining' if improvement < 0 else '➡️ Stable'}

**Compliance History:**
"""
            
            # Show recent history
            for i, trend in enumerate(trends[:5]):
                timestamp = datetime.fromisoformat(trend['timestamp'].replace('Z', '+00:00'))
                response_text += f"• {timestamp.strftime('%Y-%m-%d')}: "
                response_text += f"{trend['compliance_rate']:.1f}% "
                response_text += f"({trend['compliant_count']}/{trend['total_resources']})\n"
            
            # Predictions
            if daily_improvement > 0:
                days_to_100 = (100 - recent_rate) / daily_improvement
                response_text += f"\n🔮 **Projection:** At current rate, 100% compliance in {days_to_100:.0f} days\n"
            elif daily_improvement < 0:
                response_text += "\n⚠️ **Warning:** Compliance is declining. Immediate action needed!\n"
            
            # Recommendations based on trends
            response_text += "\n**Recommendations:**\n"
            
            if recent_rate < 80:
                response_text += "• 🚨 Implement mandatory tagging policies immediately\n"
                response_text += "• 🤖 Deploy automated tagging Lambda function\n"
                response_text += "• 📧 Send daily non-compliance reports to resource owners\n"
            elif recent_rate < 95:
                response_text += "• 📋 Focus on remaining non-compliant resources\n"
                response_text += "• 🎯 Set up preventive controls in AWS Config\n"
                response_text += "• 📊 Create team-specific compliance dashboards\n"
            else:
                response_text += "• ✅ Maintain current processes\n"
                response_text += "• 🔍 Regular audits to ensure continued compliance\n"
                response_text += "• 🏆 Celebrate the achievement with the team!\n"
            
            # Create trend chart data
            trend_chart_data = {
                'dates': [t['timestamp'] for t in trends],
                'compliance_rates': [t['compliance_rate'] for t in trends],
                'resource_counts': [t['total_resources'] for t in trends],
                'improvement_rate': daily_improvement,
                'projection': {
                    'days_to_100': days_to_100 if daily_improvement > 0 else None,
                    'projected_date': (datetime.now() + timedelta(days=days_to_100)).strftime('%Y-%m-%d') 
                                     if daily_improvement > 0 else None
                }
            }
            
            return response_text, trend_chart_data
            
        except Exception as e:
            return f"Error analyzing compliance trends: {str(e)}", {}
    
    def suggest_tag_policies(self) -> Tuple[str, Dict]:
        """
        Suggest tag enforcement policies
        """
        response_text = """
🛡️ **Tag Enforcement Policy Recommendations**

**1. AWS Organizations Tag Policies**
```json
{
  "tags": {
    "Environment": {
      "tag_key": "Environment",
      "tag_value": {
        "@@assign": ["dev", "staging", "prod", "test"]
      },
      "enforced_for": ["ec2:instance", "rds:db", "s3:bucket"]
    },
    "CostCenter": {
      "tag_key": "CostCenter",
      "tag_value": {
        "@@assign": "CC-*"
      },
      "enforced_for": ["ec2:*", "rds:*", "s3:*"]
    }
  }
}
```

**2. AWS Config Rules for Compliance**
• `required-tags` - Checks if resources have required tags
• `ec2-instance-tag-required` - EC2-specific tag requirements
• `rds-instance-tag-required` - RDS-specific tag requirements

**3. IAM Policy for Tag Enforcement**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": ["ec2:RunInstances"],
      "Resource": ["arn:aws:ec2:*:*:instance/*"],
      "Condition": {
        "StringNotLike": {
          "aws:RequestTag/Environment": ["dev", "staging", "prod"],
          "aws:RequestTag/Owner": "*",
          "aws:RequestTag/CostCenter": "CC-*"
        }
      }
    }
  ]
}
```

**4. Automated Tagging Lambda Function**
• Triggers on CloudTrail resource creation events
• Applies default tags based on:
  - Creator's IAM user/role
  - AWS account
  - Resource type
  - Creation time

**5. Tag Governance Process**
• **Daily:** Automated compliance scans
• **Weekly:** Non-compliance reports to managers
• **Monthly:** Tag policy review and updates
• **Quarterly:** Tag taxonomy optimization

**Implementation Steps:**
1. Deploy tag policies in AWS Organizations
2. Enable AWS Config rules
3. Update IAM policies
4. Deploy auto-tagging Lambda
5. Set up monitoring and alerting

Type 'deploy tag policy' to start implementation or 'export policy templates' for the full package.
"""
        
        policy_data = {
            'recommended_policies': [
                'AWS Organizations Tag Policies',
                'AWS Config Rules',
                'IAM Deny Policies',
                'Lambda Auto-tagging',
                'CloudWatch Alarms'
            ],
            'estimated_setup_time': '2-4 hours',
            'maintenance_effort': '1-2 hours/month',
            'compliance_improvement': '95%+ within 30 days'
        }
        
        return response_text, policy_data
    
    def general_tag_guidance(self) -> Tuple[str, Dict]:
        """
        Provide general tag compliance guidance
        """
        response_text = """
📚 **AWS Resource Tagging Best Practices Guide**

**Why Tagging Matters:**
• 💰 **Cost Allocation:** Track spending by project, team, or environment
• 🔍 **Resource Management:** Quickly find and manage resources
• 🛡️ **Security:** Apply tag-based access controls
• 📊 **Compliance:** Meet regulatory and audit requirements
• 🤖 **Automation:** Enable tag-based automation workflows

**Required Tags (Minimum):**
1. **Environment** - dev/staging/prod/test
2. **Owner** - Email of responsible person/team
3. **CostCenter** - Financial allocation code
4. **Project** - Project or application name

**Recommended Additional Tags:**
• **Application** - Specific application name
• **Team** - Responsible team name
• **BackupPolicy** - Backup requirements
• **DataClassification** - Security classification
• **CreatedDate** - Resource creation date
• **ExpirationDate** - For temporary resources

**Tag Naming Conventions:**
• Use consistent case (recommend: PascalCase)
• No spaces (use hyphens or underscores)
• Keep values short but descriptive
• Use standard abbreviations

**Common Tagging Mistakes to Avoid:**
❌ Inconsistent tag names (env vs Environment)
❌ Missing tags on new resources
❌ Generic values (e.g., Owner: "admin")
❌ Not updating tags when ownership changes
❌ Too many tags (stick to 10-15 max)

**Quick Commands:**
• 'scan compliance' - Check current compliance status
• 'find untagged resources' - List non-compliant resources
• 'apply tags' - Start remediation process
• 'create tag policy' - Set up enforcement
• 'show tag costs' - See financial impact

How can I help with your tagging compliance today?
"""
        
        guidance_data = {
            'required_tags': self.required_tags,
            'best_practices': [
                'Consistent naming',
                'Automated tagging',
                'Regular audits',
                'Policy enforcement',
                'Team training'
            ],
            'resources': {
                'AWS Tagging Guide': 'https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html',
                'Tag Policy Examples': 'https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html'
            }
        }
        
        return response_text, guidance_data
    
    def _direct_compliance_scan(self) -> Tuple[str, Dict]:
        """
        Perform direct compliance scan without Lambda
        """
        try:
            compliant_count = 0
            non_compliant_count = 0
            total_count = 0
            missing_tags_summary = {tag: 0 for tag in self.required_tags}
            
            # Scan EC2 instances
            instances = self.ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        total_count += 1
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        missing_tags = [tag for tag in self.required_tags if tag not in tags]
                        
                        if missing_tags:
                            non_compliant_count += 1
                            for tag in missing_tags:
                                missing_tags_summary[tag] += 1
                        else:
                            compliant_count += 1
            
            # Calculate compliance rate
            compliance_rate = (compliant_count / total_count * 100) if total_count > 0 else 100
            
            response_text = f"""
🔍 **Quick Compliance Scan Results**

📊 **Compliance Rate: {compliance_rate:.1f}%**

• Total Resources Scanned: {total_count}
• Compliant: {compliant_count} ✅
• Non-Compliant: {non_compliant_count} ⚠️

**Missing Tags:**
"""
            
            for tag, count in missing_tags_summary.items():
                if count > 0:
                    response_text += f"• {tag}: {count} resources\n"
            
            scan_data = {
                'compliance_rate': compliance_rate,
                'total_resources': total_count,
                'compliant_count': compliant_count,
                'non_compliant_count': non_compliant_count,
                'missing_tags_summary': missing_tags_summary
            }
            
            return response_text, scan_data
            
        except Exception as e:
            return f"Error performing compliance scan: {str(e)}", {}
    
    def _estimate_instance_cost(self, instance_type: str) -> float:
        """
        Estimate monthly cost for an EC2 instance type
        """
        # Simplified cost estimates (actual costs vary by region)
        cost_map = {
            't2.micro': 8.50,
            't2.small': 17.00,
            't2.medium': 34.00,
            't2.large': 68.00,
            't3.micro': 7.60,
            't3.small': 15.20,
            't3.medium': 30.40,
            't3.large': 60.80,
            'm5.large': 69.60,
            'm5.xlarge': 139.20,
            'm5.2xlarge': 278.40,
            'c5.large': 62.00,
            'c5.xlarge': 124.00
        }
        
        # Return estimated cost or default
        return cost_map.get(instance_type, 50.00) * 24 * 30  # Convert hourly to monthly