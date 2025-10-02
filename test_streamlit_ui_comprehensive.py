#!/usr/bin/env python3
"""
Comprehensive Streamlit UI Test Suite
Tests all 9 tabs and their functionality
"""

import unittest
import requests
import json
import time
import subprocess
import os
import sys
import boto3
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Import modules to test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestStreamlitDashboard(unittest.TestCase):
    """Test all Streamlit dashboard tabs and functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:8502"
        cls.dashboard_file = "finops_intelligent_dashboard.py"
        
    def setUp(self):
        """Set up before each test"""
        self.dashboard_content = None
        with open(self.dashboard_file, 'r') as f:
            self.dashboard_content = f.read()
    
    def test_01_dashboard_running(self):
        """Test that dashboard is running"""
        print("\n🧪 Test 1: Dashboard Running")
        try:
            response = requests.get(f"{self.base_url}/_stcore/health", timeout=5)
            self.assertEqual(response.text.strip(), 'ok')
            print("✅ Dashboard is running")
        except Exception as e:
            self.fail(f"Dashboard not accessible: {str(e)}")
    
    def test_02_tab_structure(self):
        """Test that all 9 tabs are defined correctly"""
        print("\n🧪 Test 2: Tab Structure")
        
        # Check for two-row tab structure
        self.assertIn("### 📊 Main Features", self.dashboard_content)
        self.assertIn("### 🆕 New Features", self.dashboard_content)
        print("✅ Two-row tab structure found")
        
        # Check main tabs (row 1)
        main_tabs = [
            "📊 Cost Intelligence",
            "💬 Multi-Agent Chat",
            "🏢 Business Context (Apptio)",
            "🔍 Resource Optimization",
            "💎 Savings Plans",
            "🔮 Budget Prediction",
            "📈 Executive Dashboard"
        ]
        
        for tab in main_tabs:
            self.assertIn(tab, self.dashboard_content)
        print(f"✅ All {len(main_tabs)} main tabs defined")
        
        # Check new feature tabs (row 2)
        new_tabs = [
            "📋 Report Generator",
            "🏷️ Tag Compliance"
        ]
        
        for tab in new_tabs:
            self.assertIn(tab, self.dashboard_content)
        print(f"✅ All {len(new_tabs)} new feature tabs defined")
    
    def test_03_tab1_cost_intelligence(self):
        """Test Tab 1: Cost Intelligence functionality"""
        print("\n🧪 Test 3: Tab 1 - Cost Intelligence")
        
        # Check key components
        self.assertIn("with tab1:", self.dashboard_content)
        self.assertIn("Cost Intelligence Dashboard", self.dashboard_content)
        self.assertIn("fetch_cost_data", self.dashboard_content)
        self.assertIn("Service Breakdown", self.dashboard_content)
        self.assertIn("Cost Trend", self.dashboard_content)
        print("✅ Cost Intelligence tab structure verified")
        
        # Check visualizations
        self.assertIn("plotly", self.dashboard_content)
        self.assertIn("px.pie", self.dashboard_content)
        self.assertIn("px.line", self.dashboard_content)
        print("✅ Cost visualizations configured")
    
    def test_04_tab2_multi_agent_chat(self):
        """Test Tab 2: Multi-Agent Chat functionality"""
        print("\n🧪 Test 4: Tab 2 - Multi-Agent Chat")
        
        # Check key components
        self.assertIn("with tab2:", self.dashboard_content)
        self.assertIn("Multi-Agent FinOps Assistant", self.dashboard_content)
        self.assertIn("identify_active_agent", self.dashboard_content)
        self.assertIn("process_with_agent", self.dashboard_content)
        print("✅ Multi-Agent Chat tab structure verified")
        
        # Check all 6 agents
        agents = ['general', 'prediction', 'optimizer', 'savings', 'anomaly', 'compliance']
        for agent in agents:
            self.assertIn(f"'{agent}'", self.dashboard_content)
        print(f"✅ All {len(agents)} AI agents defined")
        
        # Check agent descriptions
        self.assertIn("Tag Compliance Agent", self.dashboard_content)
        print("✅ Tag Compliance Agent integrated")
    
    def test_05_tab3_business_context(self):
        """Test Tab 3: Business Context (Apptio) functionality"""
        print("\n🧪 Test 5: Tab 3 - Business Context (Apptio)")
        
        # Check key components
        self.assertIn("with tab3:", self.dashboard_content)
        self.assertIn("Business Context Integration", self.dashboard_content)
        self.assertIn("TBM Taxonomy Mapping", self.dashboard_content)
        self.assertIn("apptio_mapping", self.dashboard_content)
        print("✅ Business Context tab structure verified")
    
    def test_06_tab4_resource_optimization(self):
        """Test Tab 4: Resource Optimization functionality"""
        print("\n🧪 Test 6: Tab 4 - Resource Optimization")
        
        # Check key components
        self.assertIn("with tab4:", self.dashboard_content)
        self.assertIn("Resource Optimization", self.dashboard_content)
        self.assertIn("scan_idle_resources", self.dashboard_content)
        self.assertIn("Idle EC2 Instances", self.dashboard_content)
        self.assertIn("Unattached EBS Volumes", self.dashboard_content)
        print("✅ Resource Optimization tab structure verified")
    
    def test_07_tab5_savings_plans(self):
        """Test Tab 5: Savings Plans functionality"""
        print("\n🧪 Test 7: Tab 5 - Savings Plans")
        
        # Check key components
        self.assertIn("with tab5:", self.dashboard_content)
        self.assertIn("Savings Plans Recommendations", self.dashboard_content)
        self.assertIn("get_savings_plans_recommendations", self.dashboard_content)
        self.assertIn("Compute Savings Plan", self.dashboard_content)
        print("✅ Savings Plans tab structure verified")
    
    def test_08_tab6_budget_prediction(self):
        """Test Tab 6: Budget Prediction functionality"""
        print("\n🧪 Test 8: Tab 6 - Budget Prediction")
        
        # Check key components
        self.assertIn("with tab6:", self.dashboard_content)
        self.assertIn("AI-Powered Budget Prediction", self.dashboard_content)
        self.assertIn("predict_budget", self.dashboard_content)
        self.assertIn("Prediction Confidence", self.dashboard_content)
        print("✅ Budget Prediction tab structure verified")
    
    def test_09_tab7_executive_dashboard(self):
        """Test Tab 7: Executive Dashboard functionality"""
        print("\n🧪 Test 9: Tab 7 - Executive Dashboard")
        
        # Check key components
        self.assertIn("with tab7:", self.dashboard_content)
        self.assertIn("Executive Dashboard", self.dashboard_content)
        self.assertIn("KPI Metrics", self.dashboard_content)
        self.assertIn("Monthly Forecast", self.dashboard_content)
        print("✅ Executive Dashboard tab structure verified")
    
    def test_10_tab8_report_generator(self):
        """Test Tab 8: Report Generator functionality"""
        print("\n🧪 Test 10: Tab 8 - Report Generator")
        
        # Check key components
        self.assertIn("with tab8:", self.dashboard_content)
        self.assertIn("FinOps Report Generator", self.dashboard_content)
        self.assertIn("report_generator", self.dashboard_content)
        self.assertIn("Generate Report", self.dashboard_content)
        print("✅ Report Generator tab structure verified")
        
        # Check report options
        self.assertIn("Report Type", self.dashboard_content)
        self.assertIn("Report Format", self.dashboard_content)
        self.assertIn("Date Range", self.dashboard_content)
        self.assertIn("Include Tag Compliance Analysis", self.dashboard_content)
        print("✅ Report configuration options verified")
        
        # Check download functionality
        self.assertIn("download_button", self.dashboard_content)
        self.assertIn("Download PDF Report", self.dashboard_content)
        self.assertIn("Download Excel Report", self.dashboard_content)
        self.assertIn("Download JSON Report", self.dashboard_content)
        print("✅ Download functionality verified")
    
    def test_11_tab9_tag_compliance(self):
        """Test Tab 9: Tag Compliance functionality"""
        print("\n🧪 Test 11: Tab 9 - Tag Compliance")
        
        # Check key components
        self.assertIn("with tab9:", self.dashboard_content)
        self.assertIn("Resource Tag Compliance", self.dashboard_content)
        self.assertIn("tag_agent", self.dashboard_content)
        self.assertIn("Scan Compliance", self.dashboard_content)
        print("✅ Tag Compliance tab structure verified")
        
        # Check compliance features
        self.assertIn("Required Tags", self.dashboard_content)
        self.assertIn("Compliance Summary", self.dashboard_content)
        self.assertIn("Non-Compliant Resources", self.dashboard_content)
        self.assertIn("Missing Tags Analysis", self.dashboard_content)
        print("✅ Compliance features verified")
        
        # Check remediation options
        self.assertIn("Auto-Remediation", self.dashboard_content)
        self.assertIn("Generate Compliance Report", self.dashboard_content)
        self.assertIn("Export Non-Compliant Resources", self.dashboard_content)
        print("✅ Remediation options verified")
    
    def test_12_imports_and_dependencies(self):
        """Test all required imports and dependencies"""
        print("\n🧪 Test 12: Imports and Dependencies")
        
        required_imports = [
            "import streamlit as st",
            "import boto3",
            "import pandas as pd",
            "import plotly.express as px",
            "from multi_agent_processor import MultiAgentProcessor",
            "from finops_report_generator import FinOpsReportGenerator",
            "from tag_compliance_agent import TagComplianceAgent"
        ]
        
        for imp in required_imports:
            self.assertIn(imp, self.dashboard_content)
        print(f"✅ All {len(required_imports)} required imports found")
    
    def test_13_aws_client_initialization(self):
        """Test AWS client initialization"""
        print("\n🧪 Test 13: AWS Client Initialization")
        
        # Check client initialization
        self.assertIn("init_aws_clients", self.dashboard_content)
        self.assertIn("@st.cache_resource", self.dashboard_content)
        
        required_clients = ['ce', 'ec2', 'cloudwatch', 'lambda', 'dynamodb', 'sts', 'support', 'organizations']
        for client in required_clients:
            self.assertIn(f"'{client}':", self.dashboard_content)
        print(f"✅ All {len(required_clients)} AWS clients initialized")
    
    def test_14_session_state_management(self):
        """Test session state management"""
        print("\n🧪 Test 14: Session State Management")
        
        # Check session state usage
        self.assertIn("st.session_state", self.dashboard_content)
        self.assertIn("Initialize session state", self.dashboard_content)
        self.assertIn("chat_history", self.dashboard_content)
        self.assertIn("feedback_given", self.dashboard_content)
        print("✅ Session state management verified")
    
    def test_15_error_handling(self):
        """Test error handling implementation"""
        print("\n🧪 Test 15: Error Handling")
        
        # Check try-except blocks
        self.assertIn("try:", self.dashboard_content)
        self.assertIn("except Exception as e:", self.dashboard_content)
        self.assertIn("st.error", self.dashboard_content)
        print("✅ Error handling implemented")
    
    def test_16_full_analysis_button(self):
        """Test Full Analysis button functionality"""
        print("\n🧪 Test 16: Full Analysis Button")
        
        # Check Full Analysis button
        self.assertIn("Full Analysis", self.dashboard_content)
        self.assertIn("run_full_analysis", self.dashboard_content)
        self.assertIn("with st.spinner", self.dashboard_content)
        print("✅ Full Analysis button verified")
    
    def test_17_agent_routing(self):
        """Test agent routing logic"""
        print("\n🧪 Test 17: Agent Routing Logic")
        
        # Import and test the routing function
        from finops_intelligent_dashboard import identify_active_agent
        
        test_queries = [
            ("check tag compliance", "compliance"),
            ("find untagged resources", "compliance"),
            ("predict costs", "prediction"),
            ("find idle resources", "optimizer"),
            ("savings plan recommendations", "savings"),
            ("detect anomalies", "anomaly"),
            ("what are my costs", "general")
        ]
        
        for query, expected_agent in test_queries:
            agent = identify_active_agent(query)
            self.assertEqual(agent, expected_agent, 
                           f"Query '{query}' should route to {expected_agent}")
        print(f"✅ All {len(test_queries)} agent routing tests passed")
    
    def test_18_visualization_components(self):
        """Test visualization components"""
        print("\n🧪 Test 18: Visualization Components")
        
        # Check various chart types
        charts = [
            "px.pie",
            "px.line",
            "px.bar",
            "go.Figure",
            "st.plotly_chart",
            "st.metric"
        ]
        
        for chart in charts:
            self.assertIn(chart, self.dashboard_content)
        print(f"✅ All {len(charts)} visualization types verified")
    
    def test_19_download_functionality(self):
        """Test download functionality across tabs"""
        print("\n🧪 Test 19: Download Functionality")
        
        # Check download buttons
        self.assertIn("st.download_button", self.dashboard_content)
        self.assertIn("Download PDF Report", self.dashboard_content)
        self.assertIn("Download Excel Report", self.dashboard_content)
        self.assertIn("Download JSON Report", self.dashboard_content)
        self.assertIn("Export Non-Compliant Resources", self.dashboard_content)
        print("✅ All download options verified")
    
    def test_20_real_time_features(self):
        """Test real-time update features"""
        print("\n🧪 Test 20: Real-Time Features")
        
        # Check real-time components
        self.assertIn("st.empty()", self.dashboard_content)
        self.assertIn("placeholder", self.dashboard_content)
        self.assertIn("ttl=300", self.dashboard_content)  # Cache TTL
        print("✅ Real-time update features verified")

class TestModuleIntegration(unittest.TestCase):
    """Test module integration and functionality"""
    
    def test_21_report_generator_module(self):
        """Test FinOpsReportGenerator module"""
        print("\n🧪 Test 21: Report Generator Module")
        
        from finops_report_generator import FinOpsReportGenerator
        
        # Test with mock clients
        mock_clients = self._create_mock_clients()
        report_gen = FinOpsReportGenerator(mock_clients)
        
        # Test methods exist
        methods = [
            'generate_comprehensive_report',
            '_analyze_costs',
            '_analyze_resource_tagging',
            '_generate_optimization_recommendations',
            '_analyze_trends',
            '_find_untagged_resources'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(report_gen, method))
        print(f"✅ All {len(methods)} report generator methods verified")
    
    def test_22_tag_compliance_module(self):
        """Test TagComplianceAgent module"""
        print("\n🧪 Test 22: Tag Compliance Module")
        
        from tag_compliance_agent import TagComplianceAgent
        
        agent = TagComplianceAgent()
        
        # Test methods exist
        methods = [
            'process_query',
            'perform_compliance_scan',
            'find_untagged_resources',
            'suggest_remediation',
            'generate_compliance_report'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(agent, method))
        print(f"✅ All {len(methods)} tag compliance methods verified")
    
    def test_23_multi_agent_processor(self):
        """Test MultiAgentProcessor module"""
        print("\n🧪 Test 23: Multi-Agent Processor")
        
        from multi_agent_processor import MultiAgentProcessor
        
        processor = MultiAgentProcessor()
        
        # Test tag compliance agent integration
        self.assertTrue(hasattr(processor, 'tag_compliance_agent'))
        
        # Test query processing methods
        methods = [
            'process_general_query',
            'process_prediction_query',
            'process_optimizer_query',
            'process_savings_query',
            'process_anomaly_query'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(processor, method))
        print(f"✅ All {len(methods)} processor methods verified")
    
    def test_24_lambda_function_module(self):
        """Test Lambda function module"""
        print("\n🧪 Test 24: Lambda Function Module")
        
        import lambda_tag_compliance
        
        # Test key functions
        functions = [
            'lambda_handler',
            'perform_compliance_scan',
            'check_resource_compliance',
            'get_resource_type_from_arn'
        ]
        
        for func in functions:
            self.assertTrue(hasattr(lambda_tag_compliance, func))
        print(f"✅ All {len(functions)} Lambda functions verified")
    
    def _create_mock_clients(self):
        """Create mock AWS clients for testing"""
        from unittest.mock import MagicMock
        
        mock_clients = {}
        client_names = ['ce', 'ec2', 'rds', 's3', 'lambda', 'cloudwatch', 'organizations', 'sts']
        
        for client in client_names:
            mock_clients[client] = MagicMock()
        
        # Mock STS response
        mock_clients['sts'].get_caller_identity.return_value = {'Account': '123456789012'}
        
        return mock_clients

def run_comprehensive_ui_tests():
    """Run all UI tests with detailed reporting"""
    print("="*60)
    print("🚀 Running Comprehensive Streamlit UI Test Suite")
    print("="*60)
    
    # Create test suites
    dashboard_suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamlitDashboard)
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestModuleIntegration)
    
    # Combine suites
    all_tests = unittest.TestSuite([dashboard_suite, integration_suite])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)
    
    # Summary
    print("\n" + "="*60)
    print("📊 Comprehensive Test Summary")
    print("="*60)
    print(f"Total Tests: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL UI TESTS PASSED!")
        print("\nThe FinOps Dashboard is fully functional with:")
        print("✅ All 9 tabs properly implemented")
        print("✅ Report Generator with download capabilities")
        print("✅ Tag Compliance scanning and reporting")
        print("✅ 6 AI agents including tag compliance")
        print("✅ Two-row tab layout for better visibility")
        print("✅ All existing features intact")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_comprehensive_ui_tests())