#!/usr/bin/env python3
import sys

try:
    # Test imports
    import finops_intelligent_dashboard
    import multi_agent_processor
    import finops_report_generator
    import tag_compliance_agent
    print('✅ All module imports successful')
    
    # Test basic functionality
    from multi_agent_processor import MultiAgentProcessor
    print('✅ MultiAgentProcessor import successful')
    
    from finops_report_generator import FinOpsReportGenerator
    print('✅ FinOpsReportGenerator import successful')
    
    from tag_compliance_agent import TagComplianceAgent
    print('✅ TagComplianceAgent import successful')
    
    print('')
    print('✅ Basic validation passed!')
    sys.exit(0)
except Exception as e:
    print('❌ Error: ' + str(e))
    sys.exit(1)