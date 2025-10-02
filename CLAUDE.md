# FinOps Platform Context for Claude

## Project Overview
This is an AI-powered FinOps platform that provides cost optimization, budget prediction, resource management, comprehensive reporting, and tag compliance for AWS environments.

## Active Services

### 1. FinOps Dashboard (Port 8502)
- **File**: `finops_intelligent_dashboard.py`
- **Direct URL**: http://localhost:8502
- **Nginx URL**: http://your-ec2-ip/ (port 80)
- **Features**: 
  - Real-time AWS cost visualization
  - AI budget predictions
  - Resource optimization recommendations
  - Human-in-the-loop feedback system
  - Cost anomaly detection
  - Full Analysis button (fixed and working)
  - **NEW: Report Generator tab** - Generate PDF/Excel/JSON reports
  - **NEW: Tag Compliance tab** - Monitor and enforce resource tagging

### 2. Apptio Reconciliation Dashboard (Port 8504)
- **File**: `apptio_mcp_reconciliation.py`
- **Direct URL**: http://localhost:8504
- **Nginx URL**: http://your-ec2-ip/apptio (port 80)
- **Features**:
  - AWS expense to Apptio TBM mapping
  - Cost reconciliation
  - Service categorization

### 3. MCP Services
- **Cost Explorer MCP** (Port 8001): `aws_cost_explorer_mcp_server.py`
- **Apptio MCP** (Port 8002): `apptio_mcp_server.py`
- **Resource Intelligence MCP** (Port 8004): `aws_resource_intelligence_mcp_server.py`
- **Cloudability MCP** (Port 8005): `cloudability_mcp_server.py`

## Quick Start After Reboot

```bash
cd /home/ec2-user/finops/aws-finops
./start_finops_after_reboot.sh
```

## Python Version
- Using Python 3.7.16
- Note: No walrus operator (:=) support
- No streamlit.chat_input support (older streamlit version)

## Important Files
- `STARTUP_GUIDE.md` - Detailed startup instructions
- `start_finops_after_reboot.sh` - Quick start script
- `setup_systemd_services.sh` - Auto-start setup
- `finops_nginx.conf` - Nginx reverse proxy configuration
- **NEW: `finops_report_generator.py`** - Report generation module
- **NEW: `tag_compliance_agent.py`** - Tag compliance AI agent
- **NEW: `lambda_tag_compliance.py`** - Lambda function for tag enforcement
- **NEW: `test_finops_features.py`** - Test suite for new features
- **NEW: `rollback_finops_updates.sh`** - Emergency rollback script

## AWS Services Used
- AWS Cost Explorer API
- EC2 API
- DynamoDB (for feedback storage and tag compliance history)
- CloudWatch
- IAM
- Lambda (tag-compliance-checker function)
- Resource Groups Tagging API
- S3, RDS (for tag compliance scanning)

## Known Working Configuration
- FinOps Dashboard: `finops_intelligent_dashboard.py` on port 8502
- Apptio Reconciliation: `apptio_mcp_reconciliation.py` on port 8504
- Do NOT use `finops_dashboard.py` (has Python 3.8+ syntax)
- Do NOT use `enhanced_integrated_dashboard.py` (has Python 3.8+ syntax)
- Do NOT use `enhanced_dashboard_with_feedback.py` (not the correct version)

## Nginx Configuration
- Main dashboard accessible at http://your-ec2-ip/
- Apptio dashboard accessible at http://your-ec2-ip/apptio
- Configuration file: `/etc/nginx/conf.d/finops.conf`
- Nginx handles URL rewriting for Apptio path

## Recent Updates (2025-10-02)
- **NEW: FinOps Report Generator**
  - Comprehensive PDF/Excel/JSON reports
  - Cost analysis, trends, and optimization recommendations
  - Tag compliance reporting
  - Executive and technical report templates
- **NEW: Tag Compliance System**
  - AI-powered tag compliance agent
  - Automatic scanning and remediation suggestions
  - Integration with multi-agent chatbot
  - Lambda function for automated enforcement
  - Compliance trends and analytics
- **Enhanced Multi-Agent System**
  - Added 6th AI agent: Tag Compliance Agent
  - Improved chatbot routing for tag-related queries
- **Test Suite**
  - Comprehensive test cases for all new features
  - Rollback mechanism for quick recovery

## Recent Fixes (2025-10-02)
- Fixed Full Analysis button in finops_intelligent_dashboard.py
- Fixed Apptio nginx routing with URL rewriting
- Created backup: finops_intelligent_dashboard.py.backup
- **FIXED: Lambda function error** - Deployed tag-compliance-checker Lambda
  - Function ARN: `arn:aws:lambda:us-east-1:637423485585:function:tag-compliance-checker`
  - DynamoDB table: `tag-compliance-history`
  - IAM role: `tag-compliance-lambda-role`
- **Backup created**: `backups/20251002_035036/` containing all main Streamlit apps

## Troubleshooting
- If services fail to start, check Python version compatibility
- Ensure AWS credentials are configured: `aws configure list`
- Check logs in the project directory (*.log files)
- Port 8501 may conflict with Docker, use 8502 instead
- For nginx issues: `sudo nginx -t` and `sudo tail -f /var/log/nginx/error.log`
- **Tag Compliance Lambda errors**: Check CloudWatch logs for `tag-compliance-checker`
- **Report generation errors**: Ensure Lambda has proper permissions for all resource types

## Tag Compliance System Details
- **Lambda Function**: `tag-compliance-checker` 
  - Actions: scan, report, remediate, get_resource
  - Required tags: Environment, Owner, CostCenter, Project
  - Scans EC2, RDS, S3, and all resources via Resource Groups Tagging API
- **Dashboard Integration**: Tab 9 in main FinOps dashboard
- **Compliance Rate**: Currently 0.3% (371/372 resources non-compliant)
- **Test Scripts**:
  - `test_tag_compliance_integration.py` - Integration tests
  - `test_use_cases.py` - Real-world scenario tests
  - `deploy_lambda_compliance.py` - Lambda deployment script