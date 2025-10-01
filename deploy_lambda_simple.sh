#!/bin/bash
# Simple Lambda deployment without large dependencies

echo "Deploying Lambda functions (simplified)..."

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/FinOpsLambdaRole"

# Deploy each function
for func in budget_predictor resource_optimizer feedback_processor; do
    echo "Deploying $func..."
    
    # Create zip with just the Python file
    cd lambda_functions
    zip ${func}.zip ${func}_lambda.py
    
    # Create or update function
    aws lambda create-function \
        --function-name finops-${func//_/-} \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler ${func}_lambda.lambda_handler \
        --zip-file fileb://${func}.zip \
        --timeout 60 \
        --memory-size 256 \
        --region $REGION 2>/dev/null || \
    aws lambda update-function-code \
        --function-name finops-${func//_/-} \
        --zip-file fileb://${func}.zip \
        --region $REGION
    
    rm ${func}.zip
    cd ..
    
    echo "✅ Deployed finops-${func//_/-}"
done

echo "✅ Lambda deployment complete!"