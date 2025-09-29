import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class RISavingsPlansAnalyzer:
    def __init__(self):
        self.ce_client = boto3.client('ce')
        self.ec2_client = boto3.client('ec2')
        
    def get_ri_utilization(self, days: int = 30) -> Dict[str, Any]:
        """Get Reserved Instance utilization data"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get RI utilization
            response = self.ce_client.get_reservation_utilization(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY'
            )
            
            utilization_data = []
            total_hours = 0
            used_hours = 0
            total_cost = 0
            realized_savings = 0
            
            for result in response['UtilizationsByTime']:
                date = result['TimePeriod']['Start']
                util = result.get('Total', {})
                
                utilization_percentage = float(util.get('UtilizationPercentage', '0'))
                purchased_hours = float(util.get('PurchasedHours', '0'))
                used_hours_period = float(util.get('TotalActualHours', '0'))
                amortized_upfront = float(util.get('AmortizedUpfrontFee', '0'))
                amortized_recurring = float(util.get('AmortizedRecurringFee', '0'))
                realized_savings_period = float(util.get('RealizedSavings', '0'))
                
                total_hours += purchased_hours
                used_hours += used_hours_period
                total_cost += amortized_upfront + amortized_recurring
                realized_savings += realized_savings_period
                
                utilization_data.append({
                    'date': date,
                    'utilization_percentage': utilization_percentage,
                    'purchased_hours': purchased_hours,
                    'used_hours': used_hours_period,
                    'cost': amortized_upfront + amortized_recurring,
                    'realized_savings': realized_savings_period
                })
            
            return {
                'utilization_data': utilization_data,
                'summary': {
                    'average_utilization': (used_hours / total_hours * 100) if total_hours > 0 else 0,
                    'total_purchased_hours': total_hours,
                    'total_used_hours': used_hours,
                    'total_cost': total_cost,
                    'total_realized_savings': realized_savings
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting RI utilization: {str(e)}")
            return {}
    
    def get_savings_plans_utilization(self, days: int = 30) -> Dict[str, Any]:
        """Get Savings Plans utilization data"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get Savings Plans utilization
            response = self.ce_client.get_savings_plans_utilization(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY'
            )
            
            utilization_data = []
            total_commitment = 0
            total_used = 0
            total_savings = 0
            
            for result in response.get('SavingsPlansUtilizationsByTime', []):
                date = result['TimePeriod']['Start']
                util = result.get('Total', {})
                
                utilization_percentage = float(util.get('UtilizationPercentage', '0'))
                total_commitment_period = float(util.get('TotalCommitment', '0'))
                used_commitment = float(util.get('UsedCommitment', '0'))
                savings = float(util.get('NetSavings', '0'))
                
                total_commitment += total_commitment_period
                total_used += used_commitment
                total_savings += savings
                
                utilization_data.append({
                    'date': date,
                    'utilization_percentage': utilization_percentage,
                    'total_commitment': total_commitment_period,
                    'used_commitment': used_commitment,
                    'unused_commitment': total_commitment_period - used_commitment,
                    'net_savings': savings
                })
            
            return {
                'utilization_data': utilization_data,
                'summary': {
                    'average_utilization': (total_used / total_commitment * 100) if total_commitment > 0 else 0,
                    'total_commitment': total_commitment,
                    'total_used': total_used,
                    'total_unused': total_commitment - total_used,
                    'total_net_savings': total_savings
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Savings Plans utilization: {str(e)}")
            return {}
    
    def get_ri_coverage(self, days: int = 30) -> Dict[str, Any]:
        """Get Reserved Instance coverage data"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get RI coverage
            response = self.ce_client.get_reservation_coverage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['HoursPercentage', 'CostPercentage']
            )
            
            coverage_data = []
            total_hours = 0
            covered_hours = 0
            total_cost = 0
            covered_cost = 0
            
            for result in response['CoveragesByTime']:
                date = result['TimePeriod']['Start']
                coverage = result.get('Total', {})
                
                hours_percentage = float(coverage.get('CoverageHours', {}).get('CoverageHoursPercentage', '0'))
                cost_percentage = float(coverage.get('CoverageCost', {}).get('CoverageCostPercentage', '0'))
                
                on_demand_hours = float(coverage.get('CoverageHours', {}).get('OnDemandHours', '0'))
                reserved_hours = float(coverage.get('CoverageHours', {}).get('ReservedHours', '0'))
                total_hours_period = on_demand_hours + reserved_hours
                
                total_hours += total_hours_period
                covered_hours += reserved_hours
                
                coverage_data.append({
                    'date': date,
                    'hours_coverage_percentage': hours_percentage,
                    'cost_coverage_percentage': cost_percentage,
                    'on_demand_hours': on_demand_hours,
                    'reserved_hours': reserved_hours,
                    'total_hours': total_hours_period
                })
            
            return {
                'coverage_data': coverage_data,
                'summary': {
                    'average_hours_coverage': (covered_hours / total_hours * 100) if total_hours > 0 else 0,
                    'total_hours': total_hours,
                    'covered_hours': covered_hours,
                    'on_demand_hours': total_hours - covered_hours
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting RI coverage: {str(e)}")
            return {}
    
    def get_savings_plans_coverage(self, days: int = 30) -> Dict[str, Any]:
        """Get Savings Plans coverage data"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get Savings Plans coverage
            response = self.ce_client.get_savings_plans_coverage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY'
            )
            
            coverage_data = []
            total_spend = 0
            covered_spend = 0
            
            for result in response.get('SavingsPlansCoverages', []):
                date = result['TimePeriod']['Start']
                coverage = result.get('Coverage', {})
                
                spend_covered_by_sp = float(coverage.get('SpendCoveredBySavingsPlan', '0'))
                on_demand_cost = float(coverage.get('OnDemandCost', '0'))
                total_cost = float(coverage.get('TotalCost', '0'))
                coverage_percentage = float(coverage.get('CoveragePercentage', '0'))
                
                total_spend += total_cost
                covered_spend += spend_covered_by_sp
                
                coverage_data.append({
                    'date': date,
                    'coverage_percentage': coverage_percentage,
                    'spend_covered_by_sp': spend_covered_by_sp,
                    'on_demand_cost': on_demand_cost,
                    'total_cost': total_cost
                })
            
            return {
                'coverage_data': coverage_data,
                'summary': {
                    'average_coverage': (covered_spend / total_spend * 100) if total_spend > 0 else 0,
                    'total_spend': total_spend,
                    'covered_spend': covered_spend,
                    'on_demand_spend': total_spend - covered_spend
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Savings Plans coverage: {str(e)}")
            return {}
    
    def get_ri_recommendations(self) -> Dict[str, Any]:
        """Get Reserved Instance purchase recommendations"""
        try:
            response = self.ce_client.get_reservation_purchase_recommendation(
                Service='EC2',
                PaymentOption='ALL_UPFRONT',
                Term='ONE_YEAR',
                LookbackPeriodInDays='SIXTY_DAYS'
            )
            
            recommendations = []
            total_estimated_savings = 0
            
            for rec in response.get('Recommendations', []):
                rec_details = rec.get('RecommendationDetails', [])
                for detail in rec_details:
                    instance_details = detail.get('InstanceDetails', {}).get('EC2InstanceDetails', {})
                    
                    estimated_monthly_savings = float(detail.get('EstimatedMonthlySavingsAmount', '0'))
                    total_estimated_savings += estimated_monthly_savings
                    
                    recommendations.append({
                        'instance_type': instance_details.get('InstanceType'),
                        'instance_family': instance_details.get('InstanceFamily'),
                        'region': instance_details.get('Region'),
                        'availability_zone': instance_details.get('AvailabilityZone'),
                        'platform': instance_details.get('Platform'),
                        'tenancy': instance_details.get('Tenancy'),
                        'recommended_count': detail.get('RecommendedNumberOfInstancesToPurchase'),
                        'estimated_monthly_savings': estimated_monthly_savings,
                        'estimated_savings_percentage': float(detail.get('EstimatedSavingsPercentage', '0')),
                        'upfront_cost': float(detail.get('UpfrontCost', '0'))
                    })
            
            return {
                'recommendations': recommendations,
                'summary': {
                    'total_recommendations': len(recommendations),
                    'total_estimated_monthly_savings': total_estimated_savings
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting RI recommendations: {str(e)}")
            return {}
    
    def get_savings_plans_recommendations(self) -> Dict[str, Any]:
        """Get Savings Plans purchase recommendations"""
        try:
            response = self.ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='ALL_UPFRONT',
                LookbackPeriodInDays='SIXTY_DAYS'
            )
            
            recommendation = response.get('SavingsPlansPurchaseRecommendation', {})
            
            return {
                'recommendation': {
                    'hourly_commitment_to_purchase': float(recommendation.get('HourlyCommitmentToPurchase', '0')),
                    'estimated_savings_amount': float(recommendation.get('EstimatedSavingsAmount', '0')),
                    'estimated_savings_percentage': float(recommendation.get('EstimatedSavingsPercentage', '0')),
                    'estimated_monthly_savings': float(recommendation.get('EstimatedMonthlySavingsAmount', '0')),
                    'upfront_cost': float(recommendation.get('UpfrontCost', '0'))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Savings Plans recommendations: {str(e)}")
            return {}
    
    def identify_optimization_opportunities(self, ri_data: Dict[str, Any], 
                                         sp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify RI and Savings Plans optimization opportunities"""
        opportunities = []
        
        # Check RI utilization
        if ri_data.get('utilization'):
            ri_util_summary = ri_data['utilization'].get('summary', {})
            avg_utilization = ri_util_summary.get('average_utilization', 100)
            
            if avg_utilization < 80:
                opportunities.append({
                    'type': 'low_ri_utilization',
                    'current_utilization': avg_utilization,
                    'recommendation': f'Reserved Instances are only {avg_utilization:.1f}% utilized. Consider modifying or exchanging underutilized RIs.',
                    'priority': 'high' if avg_utilization < 50 else 'medium',
                    'estimated_waste_percent': 100 - avg_utilization
                })
        
        # Check Savings Plans utilization
        if sp_data.get('utilization'):
            sp_util_summary = sp_data['utilization'].get('summary', {})
            avg_utilization = sp_util_summary.get('average_utilization', 100)
            
            if avg_utilization < 90:
                opportunities.append({
                    'type': 'low_sp_utilization',
                    'current_utilization': avg_utilization,
                    'recommendation': f'Savings Plans are only {avg_utilization:.1f}% utilized. Review your commitment and usage patterns.',
                    'priority': 'high' if avg_utilization < 70 else 'medium',
                    'estimated_waste_percent': 100 - avg_utilization
                })
        
        # Check RI coverage
        if ri_data.get('coverage'):
            ri_cov_summary = ri_data['coverage'].get('summary', {})
            avg_coverage = ri_cov_summary.get('average_hours_coverage', 0)
            
            if avg_coverage < 70:
                opportunities.append({
                    'type': 'low_ri_coverage',
                    'current_coverage': avg_coverage,
                    'recommendation': f'Only {avg_coverage:.1f}% of eligible usage is covered by RIs. Consider purchasing additional Reserved Instances.',
                    'priority': 'high' if avg_coverage < 50 else 'medium'
                })
        
        # Check Savings Plans coverage
        if sp_data.get('coverage'):
            sp_cov_summary = sp_data['coverage'].get('summary', {})
            avg_coverage = sp_cov_summary.get('average_coverage', 0)
            
            if avg_coverage < 70:
                opportunities.append({
                    'type': 'low_sp_coverage',
                    'current_coverage': avg_coverage,
                    'recommendation': f'Only {avg_coverage:.1f}% of eligible spend is covered by Savings Plans. Consider purchasing additional Savings Plans.',
                    'priority': 'medium'
                })
        
        # Add RI recommendations if available
        if ri_data.get('recommendations'):
            ri_rec_summary = ri_data['recommendations'].get('summary', {})
            if ri_rec_summary.get('total_recommendations', 0) > 0:
                opportunities.append({
                    'type': 'ri_purchase_opportunity',
                    'recommendation_count': ri_rec_summary['total_recommendations'],
                    'estimated_monthly_savings': ri_rec_summary.get('total_estimated_monthly_savings', 0),
                    'recommendation': 'New Reserved Instance purchase opportunities identified',
                    'priority': 'high'
                })
        
        # Add SP recommendations if available
        if sp_data.get('recommendations'):
            sp_rec = sp_data['recommendations'].get('recommendation', {})
            if sp_rec.get('hourly_commitment_to_purchase', 0) > 0:
                opportunities.append({
                    'type': 'sp_purchase_opportunity',
                    'hourly_commitment': sp_rec['hourly_commitment_to_purchase'],
                    'estimated_monthly_savings': sp_rec.get('estimated_monthly_savings', 0),
                    'recommendation': 'New Savings Plans purchase opportunity identified',
                    'priority': 'high'
                })
        
        return opportunities

def lambda_handler(event, context):
    """AWS Lambda handler for RI and Savings Plans analysis"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize the analyzer
        analyzer = RISavingsPlansAnalyzer()
        
        # Extract parameters from the event
        action = event.get('action', 'analyze_all')
        days = event.get('days', 30)
        
        # Perform analysis based on action
        if action == 'analyze_utilization':
            ri_utilization = analyzer.get_ri_utilization(days)
            sp_utilization = analyzer.get_savings_plans_utilization(days)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'ri_utilization': ri_utilization,
                    'savings_plans_utilization': sp_utilization,
                    'analysis_period_days': days
                })
            }
            
        elif action == 'analyze_coverage':
            ri_coverage = analyzer.get_ri_coverage(days)
            sp_coverage = analyzer.get_savings_plans_coverage(days)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'ri_coverage': ri_coverage,
                    'savings_plans_coverage': sp_coverage,
                    'analysis_period_days': days
                })
            }
            
        elif action == 'get_recommendations':
            ri_recommendations = analyzer.get_ri_recommendations()
            sp_recommendations = analyzer.get_savings_plans_recommendations()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'ri_recommendations': ri_recommendations,
                    'savings_plans_recommendations': sp_recommendations
                })
            }
            
        elif action == 'analyze_all':
            # Comprehensive analysis
            ri_data = {
                'utilization': analyzer.get_ri_utilization(days),
                'coverage': analyzer.get_ri_coverage(days),
                'recommendations': analyzer.get_ri_recommendations()
            }
            
            sp_data = {
                'utilization': analyzer.get_savings_plans_utilization(days),
                'coverage': analyzer.get_savings_plans_coverage(days),
                'recommendations': analyzer.get_savings_plans_recommendations()
            }
            
            opportunities = analyzer.identify_optimization_opportunities(ri_data, sp_data)
            
            # Calculate summary
            total_potential_savings = 0
            high_priority_count = 0
            
            # Add RI recommendation savings
            if ri_data['recommendations'].get('summary'):
                total_potential_savings += ri_data['recommendations']['summary'].get('total_estimated_monthly_savings', 0)
            
            # Add SP recommendation savings
            if sp_data['recommendations'].get('recommendation'):
                total_potential_savings += sp_data['recommendations']['recommendation'].get('estimated_monthly_savings', 0)
            
            for opp in opportunities:
                if opp.get('priority') == 'high':
                    high_priority_count += 1
                
                # Add estimated monthly savings to each opportunity
                if opp.get('estimated_monthly_savings'):
                    opp['estimated_monthly_savings'] = opp.get('estimated_monthly_savings', 0)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'summary': {
                        'potential_monthly_savings': total_potential_savings,
                        'high_priority_recommendations': high_priority_count,
                        'total_recommendations': len(opportunities),
                        'ri_average_utilization': ri_data['utilization'].get('summary', {}).get('average_utilization', 0),
                        'sp_average_utilization': sp_data['utilization'].get('summary', {}).get('average_utilization', 0),
                        'ri_average_coverage': ri_data['coverage'].get('summary', {}).get('average_hours_coverage', 0),
                        'sp_average_coverage': sp_data['coverage'].get('summary', {}).get('average_coverage', 0)
                    },
                    'ri_data': ri_data,
                    'savings_plans_data': sp_data,
                    'recommendations': opportunities,
                    'analysis_period_days': days
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'supported_actions': ['analyze_utilization', 'analyze_coverage', 'get_recommendations', 'analyze_all']
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'action': 'analyze_all',
        'days': 30
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))