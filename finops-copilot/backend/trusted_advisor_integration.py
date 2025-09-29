#!/usr/bin/env python3
"""
AWS Trusted Advisor Integration Module

This module provides integration with AWS Trusted Advisor for comprehensive
monitoring and cost optimization recommendations.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrustedAdvisorIntegration:
    """Integration with AWS Trusted Advisor for cost optimization insights"""
    
    def __init__(self):
        """Initialize the Trusted Advisor integration"""
        try:
            self.support_client = boto3.client('support', region_name='us-east-1')  # Support API only available in us-east-1
            self.cloudtrail_client = boto3.client('cloudtrail')
            self.health_client = boto3.client('health', region_name='us-east-1')  # Health API only available in us-east-1
            self.ec2_client = boto3.client('ec2')
            logger.info("Trusted Advisor integration initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing Trusted Advisor integration: {str(e)}")
            raise
    
    async def get_trusted_advisor_checks(self, language: str = 'en') -> Dict[str, Any]:
        """
        Get all available Trusted Advisor checks
        
        Args:
            language: Language for check descriptions
        
        Returns:
            Dict containing available checks
        """
        try:
            response = self.support_client.describe_trusted_advisor_checks(language=language)
            
            checks_by_category = {}
            for check in response.get('checks', []):
                category = check.get('category', 'other')
                if category not in checks_by_category:
                    checks_by_category[category] = []
                
                checks_by_category[category].append({
                    'id': check.get('id'),
                    'name': check.get('name'),
                    'description': check.get('description'),
                    'metadata': check.get('metadata', [])
                })
            
            return {
                'checks_by_category': checks_by_category,
                'total_checks': len(response.get('checks', [])),
                'categories': list(checks_by_category.keys())
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'SubscriptionRequiredException':
                logger.warning("AWS Support plan required for Trusted Advisor API access")
                return {
                    'error': 'AWS Support plan required for Trusted Advisor API access',
                    'mock_data': self._get_mock_trusted_advisor_data()
                }
            else:
                logger.error(f"Error getting Trusted Advisor checks: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error getting Trusted Advisor checks: {str(e)}")
            raise
    
    async def get_check_result(self, check_id: str, language: str = 'en') -> Dict[str, Any]:
        """
        Get result for a specific Trusted Advisor check
        
        Args:
            check_id: ID of the check to retrieve
            language: Language for the result
        
        Returns:
            Dict containing check result
        """
        try:
            response = self.support_client.describe_trusted_advisor_check_result(
                checkId=check_id,
                language=language
            )
            
            result = response.get('result', {})
            
            processed_result = {
                'check_id': check_id,
                'status': result.get('status'),
                'timestamp': result.get('timestamp'),
                'resources_summary': result.get('resourcesSummary', {}),
                'category_specific_summary': result.get('categorySpecificSummary', {}),
                'flagged_resources': result.get('flaggedResources', []),
                'metadata': response.get('result', {}).get('categorySpecificSummary', {})
            }
            
            return processed_result
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'SubscriptionRequiredException':
                logger.warning(f"AWS Support plan required for check {check_id}")
                return {
                    'error': 'AWS Support plan required',
                    'check_id': check_id,
                    'mock_result': self._get_mock_check_result(check_id)
                }
            else:
                logger.error(f"Error getting check result for {check_id}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error getting check result for {check_id}: {str(e)}")
            raise
    
    async def get_cost_optimization_checks(self) -> Dict[str, Any]:
        """Get all cost optimization related Trusted Advisor checks"""
        try:
            all_checks = await self.get_trusted_advisor_checks()
            
            if 'error' in all_checks:
                return all_checks
            
            cost_checks = all_checks['checks_by_category'].get('cost_optimizing', [])
            
            # Get results for each cost optimization check
            cost_check_results = []
            for check in cost_checks:
                check_result = await self.get_check_result(check['id'])
                if 'error' not in check_result:
                    cost_check_results.append({
                        'check_info': check,
                        'result': check_result
                    })
            
            # Analyze and summarize cost optimization opportunities
            summary = self._analyze_cost_optimization_results(cost_check_results)
            
            return {
                'cost_checks': cost_check_results,
                'summary': summary,
                'total_checks': len(cost_checks),
                'checks_with_results': len(cost_check_results)
            }
            
        except Exception as e:
            logger.error(f"Error getting cost optimization checks: {str(e)}")
            raise
    
    def _analyze_cost_optimization_results(self, check_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cost optimization check results"""
        summary = {
            'total_flagged_resources': 0,
            'potential_monthly_savings': 0,
            'high_priority_issues': 0,
            'recommendations': [],
            'by_check_type': {}
        }
        
        for check_data in check_results:
            check_info = check_data['check_info']
            result = check_data['result']
            
            check_name = check_info['name']
            flagged_resources = result.get('flagged_resources', [])
            
            summary['total_flagged_resources'] += len(flagged_resources)
            
            # Estimate potential savings based on check type
            estimated_savings = self._estimate_savings_by_check_type(check_name, flagged_resources)
            summary['potential_monthly_savings'] += estimated_savings
            
            # Determine priority based on status and resource count
            if result.get('status') in ['error', 'warning'] and len(flagged_resources) > 0:
                summary['high_priority_issues'] += 1
            
            # Generate recommendations
            if flagged_resources:
                recommendation = self._generate_recommendation_for_check(check_name, flagged_resources)
                if recommendation:
                    summary['recommendations'].append(recommendation)
            
            # Track by check type
            summary['by_check_type'][check_name] = {
                'flagged_resources': len(flagged_resources),
                'estimated_savings': estimated_savings,
                'status': result.get('status')
            }
        
        return summary
    
    def _estimate_savings_by_check_type(self, check_name: str, flagged_resources: List[Dict[str, Any]]) -> float:
        """Estimate potential savings based on check type and flagged resources"""
        savings_estimates = {
            'Low Utilization Amazon EC2 Instances': 200,  # per instance per month
            'Underutilized Amazon EBS Volumes': 50,       # per volume per month
            'Unassociated Elastic IP Addresses': 5,       # per IP per month
            'Amazon RDS Idle DB Instances': 100,          # per instance per month
            'Amazon Route 53 Latency Resource Record Sets': 10,  # per record set per month
        }
        
        base_savings = savings_estimates.get(check_name, 25)  # Default $25 per resource
        return base_savings * len(flagged_resources)
    
    def _generate_recommendation_for_check(self, check_name: str, flagged_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate actionable recommendation based on check results"""
        recommendations_map = {
            'Low Utilization Amazon EC2 Instances': {
                'title': 'Right-size or terminate underutilized EC2 instances',
                'description': f'Found {len(flagged_resources)} EC2 instances with low utilization',
                'action': 'Review CPU utilization and consider downsizing or terminating',
                'priority': 'high'
            },
            'Underutilized Amazon EBS Volumes': {
                'title': 'Optimize EBS volume usage',
                'description': f'Found {len(flagged_resources)} underutilized EBS volumes',
                'action': 'Consider snapshot and delete, or resize volumes',
                'priority': 'medium'
            },
            'Unassociated Elastic IP Addresses': {
                'title': 'Release unused Elastic IP addresses',
                'description': f'Found {len(flagged_resources)} unassociated Elastic IPs',
                'action': 'Release unused Elastic IP addresses to avoid charges',
                'priority': 'high'
            }
        }
        
        return recommendations_map.get(check_name, {
            'title': f'Address {check_name} issues',
            'description': f'Found {len(flagged_resources)} flagged resources',
            'action': 'Review and optimize flagged resources',
            'priority': 'medium'
        })
    
    async def get_cloudtrail_insights(self, 
                                    start_time: datetime,
                                    end_time: datetime) -> Dict[str, Any]:
        """
        Get CloudTrail insights for API errors and throttling
        
        Args:
            start_time: Start time for the query
            end_time: End time for the query
        
        Returns:
            Dict containing CloudTrail insights
        """
        try:
            # Get CloudTrail events for API errors
            response = self.cloudtrail_client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'EventName',
                        'AttributeValue': 'ConsoleLogin'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                MaxItems=50
            )
            
            events = response.get('Events', [])
            
            # Analyze events for patterns
            api_errors = []
            throttling_events = []
            
            for event in events:
                event_name = event.get('EventName', '')
                error_code = event.get('ErrorCode', '')
                
                if error_code:
                    if 'Throttling' in error_code:
                        throttling_events.append(event)
                    else:
                        api_errors.append(event)
            
            return {
                'time_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'total_events': len(events),
                'api_errors': len(api_errors),
                'throttling_events': len(throttling_events),
                'error_details': api_errors[:10],  # Top 10 errors
                'throttling_details': throttling_events[:10]  # Top 10 throttling events
            }
            
        except Exception as e:
            logger.error(f"Error getting CloudTrail insights: {str(e)}")
            return {'error': str(e)}
    
    async def get_health_events(self) -> Dict[str, Any]:
        """Get AWS Personal Health Dashboard events"""
        try:
            # Get health events
            response = self.health_client.describe_events(
                filter={
                    'eventStatusCodes': ['open', 'upcoming'],
                    'eventTypeCategories': ['issue', 'scheduledChange']
                }
            )
            
            events = response.get('events', [])
            
            # Categorize events
            active_issues = []
            scheduled_changes = []
            
            for event in events:
                event_data = {
                    'arn': event.get('arn'),
                    'service': event.get('service'),
                    'event_type_code': event.get('eventTypeCode'),
                    'event_type_category': event.get('eventTypeCategory'),
                    'region': event.get('region'),
                    'start_time': event.get('startTime').isoformat() if event.get('startTime') else None,
                    'end_time': event.get('endTime').isoformat() if event.get('endTime') else None,
                    'last_updated_time': event.get('lastUpdatedTime').isoformat() if event.get('lastUpdatedTime') else None,
                    'status_code': event.get('statusCode')
                }
                
                if event.get('eventTypeCategory') == 'issue':
                    active_issues.append(event_data)
                elif event.get('eventTypeCategory') == 'scheduledChange':
                    scheduled_changes.append(event_data)
            
            return {
                'total_events': len(events),
                'active_issues': active_issues,
                'scheduled_changes': scheduled_changes,
                'summary': {
                    'active_issues_count': len(active_issues),
                    'scheduled_changes_count': len(scheduled_changes)
                }
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UnauthorizedOperation':
                logger.warning("Health API access requires Business or Enterprise support plan")
                return {
                    'error': 'Health API requires Business or Enterprise support plan',
                    'mock_data': self._get_mock_health_data()
                }
            else:
                logger.error(f"Error getting health events: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error getting health events: {str(e)}")
            return {'error': str(e)}
    
    def _get_mock_trusted_advisor_data(self) -> Dict[str, Any]:
        """Generate mock Trusted Advisor data for demo purposes"""
        return {
            'checks_by_category': {
                'cost_optimizing': [
                    {
                        'id': 'Qch7DwouX1',
                        'name': 'Low Utilization Amazon EC2 Instances',
                        'description': 'Checks for EC2 instances that have low utilization',
                        'metadata': ['Region', 'Instance ID', 'Instance Type', 'Estimated Monthly Savings']
                    },
                    {
                        'id': 'DAvU99Dc4C',
                        'name': 'Underutilized Amazon EBS Volumes',
                        'description': 'Checks for EBS volumes that are underutilized',
                        'metadata': ['Region', 'Volume ID', 'Volume Type', 'Monthly Storage Cost']
                    }
                ]
            },
            'total_checks': 2,
            'categories': ['cost_optimizing']
        }
    
    def _get_mock_check_result(self, check_id: str) -> Dict[str, Any]:
        """Generate mock check result for demo purposes"""
        mock_results = {
            'Qch7DwouX1': {
                'status': 'warning',
                'resources_summary': {'status': 'warning', 'resources_flagged': 3, 'resources_ignored': 0, 'resources_suppressed': 0},
                'flagged_resources': [
                    {'resourceId': 'i-1234567890abcdef0', 'region': 'us-east-1', 'status': 'warning'},
                    {'resourceId': 'i-0987654321fedcba0', 'region': 'us-west-2', 'status': 'warning'},
                    {'resourceId': 'i-abcdef1234567890', 'region': 'eu-west-1', 'status': 'warning'}
                ]
            },
            'DAvU99Dc4C': {
                'status': 'warning',
                'resources_summary': {'status': 'warning', 'resources_flagged': 2, 'resources_ignored': 0, 'resources_suppressed': 0},
                'flagged_resources': [
                    {'resourceId': 'vol-1234567890abcdef0', 'region': 'us-east-1', 'status': 'warning'},
                    {'resourceId': 'vol-0987654321fedcba0', 'region': 'us-west-2', 'status': 'warning'}
                ]
            }
        }
        
        return mock_results.get(check_id, {
            'status': 'ok',
            'resources_summary': {'status': 'ok', 'resources_flagged': 0},
            'flagged_resources': []
        })
    
    def _get_mock_health_data(self) -> Dict[str, Any]:
        """Generate mock health data for demo purposes"""
        return {
            'total_events': 2,
            'active_issues': [
                {
                    'service': 'EC2',
                    'event_type_code': 'AWS_EC2_INSTANCE_REBOOT_MAINTENANCE',
                    'event_type_category': 'issue',
                    'region': 'us-east-1',
                    'status_code': 'open'
                }
            ],
            'scheduled_changes': [
                {
                    'service': 'RDS',
                    'event_type_code': 'AWS_RDS_MAINTENANCE_SCHEDULED',
                    'event_type_category': 'scheduledChange',
                    'region': 'us-west-2',
                    'status_code': 'upcoming'
                }
            ],
            'summary': {
                'active_issues_count': 1,
                'scheduled_changes_count': 1
            }
        }

# Example usage and testing
async def main():
    """Main function for testing Trusted Advisor integration"""
    ta_integration = TrustedAdvisorIntegration()
    
    try:
        # Test cost optimization checks
        cost_checks = await ta_integration.get_cost_optimization_checks()
        print("Trusted Advisor Integration Test Results:")
        print(f"Cost optimization checks: {cost_checks.get('total_checks', 0)}")
        
        if 'summary' in cost_checks:
            summary = cost_checks['summary']
            print(f"Total flagged resources: {summary.get('total_flagged_resources', 0)}")
            print(f"Potential monthly savings: ${summary.get('potential_monthly_savings', 0):.2f}")
            print(f"High priority issues: {summary.get('high_priority_issues', 0)}")
        
        # Test health events
        health_events = await ta_integration.get_health_events()
        if 'error' not in health_events:
            print(f"Health events: {health_events.get('total_events', 0)}")
        
        # Test CloudTrail insights
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        cloudtrail_insights = await ta_integration.get_cloudtrail_insights(start_time, end_time)
        if 'error' not in cloudtrail_insights:
            print(f"CloudTrail events: {cloudtrail_insights.get('total_events', 0)}")
            print(f"API errors: {cloudtrail_insights.get('api_errors', 0)}")
            print(f"Throttling events: {cloudtrail_insights.get('throttling_events', 0)}")
        
        print("Trusted Advisor integration test completed successfully")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
