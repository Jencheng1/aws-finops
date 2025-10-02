# EC2 Restart Procedure for FinOps Platform

## Quick Start (Recommended)

After EC2 reboot or restart, run:

```bash
cd /home/ec2-user/finops/aws-finops
./start_finops_after_reboot.sh
```

This will automatically start all services and verify they're running correctly.

## Manual Start (if needed)

If the quick start script fails, you can manually start services:

### 1. Start Main FinOps Dashboard
```bash
cd /home/ec2-user/finops/aws-finops
nohup python3 -m streamlit run finops_intelligent_dashboard.py \
    --server.port 8502 \
    --server.address 0.0.0.0 \
    > dashboard_8502.log 2>&1 &
```

### 2. Start Apptio Reconciliation Dashboard
```bash
nohup python3 -m streamlit run apptio_mcp_reconciliation.py \
    --server.port 8504 \
    --server.address 0.0.0.0 \
    > apptio_8504.log 2>&1 &
```

### 3. Start MCP Services (Optional)
```bash
# Cost Explorer MCP
nohup python3 aws_cost_explorer_mcp_server.py --port 8001 > mcp_cost_explorer.log 2>&1 &

# Apptio MCP
nohup python3 apptio_mcp_server.py --port 8002 > mcp_apptio.log 2>&1 &

# Resource Intelligence MCP
nohup python3 aws_resource_intelligence_mcp_server.py --port 8004 > mcp_resource.log 2>&1 &

# Cloudability MCP
nohup python3 cloudability_mcp_server.py --port 8005 > mcp_cloudability.log 2>&1 &
```

## Verify Services Are Running

### 1. Check Process Status
```bash
ps aux | grep -E "streamlit|mcp" | grep -v grep
```

### 2. Check Port Usage
```bash
netstat -tulnp | grep -E "8502|8504|8001|8002|8004|8005"
```

### 3. Check Lambda Function
```bash
aws lambda get-function --function-name tag-compliance-checker
```

If Lambda is missing, deploy it:
```bash
cd /home/ec2-user/finops/aws-finops
python3 deploy_lambda_compliance.py
```

### 4. Test Endpoints
```bash
# Test main dashboard
curl -s http://localhost:8502 | head -20

# Test Apptio dashboard
curl -s http://localhost:8504 | head -20

# Test Lambda
aws lambda invoke --function-name tag-compliance-checker \
    --payload '{"action": "scan"}' response.json && cat response.json
```

## Access URLs

After services are started, access them at:

**Via Nginx (Port 80):**
- Main Dashboard: `http://YOUR-EC2-IP/`
- Apptio Dashboard: `http://YOUR-EC2-IP/apptio`

**Direct Access:**
- Main Dashboard: `http://YOUR-EC2-IP:8502`
- Apptio Dashboard: `http://YOUR-EC2-IP:8504`

## Troubleshooting

### Service Won't Start
1. Check if port is already in use: `lsof -i :PORT`
2. Kill existing process: `pkill -f "streamlit run"`
3. Check logs: `tail -f dashboard_8502.log`

### Lambda Function Errors
1. Check CloudWatch logs: 
   ```bash
   aws logs tail /aws/lambda/tag-compliance-checker --follow
   ```
2. Verify IAM role exists: `tag-compliance-lambda-role`
3. Check DynamoDB table exists: `tag-compliance-history`

### Nginx Not Working
1. Check nginx status: `sudo systemctl status nginx`
2. Test configuration: `sudo nginx -t`
3. Restart nginx: `sudo systemctl restart nginx`
4. Check logs: `sudo tail -f /var/log/nginx/error.log`

### AWS Credentials Issues
1. Check configuration: `aws configure list`
2. Verify IAM role: `aws sts get-caller-identity`
3. Test permissions: `aws ce get-cost-and-usage --help`

## Important Notes

- Python version: 3.7.16 (no walrus operator support)
- Main services must run on ports 8502 and 8504 (not 8501/8503)
- MCP services are optional but enhance functionality
- Tag compliance requires Lambda function to be deployed
- All services log to `.log` files in the project directory

## Emergency Rollback

If something goes wrong after updates:

```bash
cd /home/ec2-user/finops/aws-finops

# Restore from backup
cp backups/20251002_035036/* .

# Restart services
./start_finops_after_reboot.sh
```

## Service Dependencies

1. **AWS Services Required:**
   - Cost Explorer API
   - EC2, RDS, S3 APIs
   - Lambda
   - DynamoDB
   - IAM with proper permissions

2. **Python Dependencies:**
   - All in requirements.txt
   - Use `pip3 install -r requirements.txt` if needed

3. **System Dependencies:**
   - Nginx (for reverse proxy)
   - Port 80, 8502, 8504 must be accessible

## Contact

For issues, check:
- Logs in `/home/ec2-user/finops/aws-finops/*.log`
- CloudWatch logs for Lambda functions
- AWS service health dashboard