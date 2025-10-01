#!/bin/bash
# Deploy Lambda functions to AWS

echo "=================================================="
echo "DEPLOYING LAMBDA FUNCTIONS"
echo "=================================================="

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
ROLE_NAME="FinOpsLambdaRole"

echo "AWS Account: $ACCOUNT_ID"
echo "Region: $REGION"

# Create IAM role for Lambda if it doesn't exist
echo -e "\n1. Creating IAM role..."
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# Check if role exists
aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1
if [ $? -ne 0 ]; then
    # Create trust policy
    cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json

    # Attach policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AWSCostExplorerServiceFullAccess

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AWSSupportAccess

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/ComprehendReadOnly

    echo "✅ IAM role created"
    sleep 10  # Wait for role to propagate
else
    echo "✅ IAM role already exists"
fi

# Create deployment packages
echo -e "\n2. Creating deployment packages..."

# Function 1: Budget Predictor
echo "Packaging budget-predictor..."
mkdir -p lambda-packages/budget-predictor
cp lambda_functions/budget_predictor_lambda.py lambda-packages/budget-predictor/lambda_function.py
cp budget_prediction_agent.py lambda-packages/budget-predictor/
cd lambda-packages/budget-predictor
# Only install what's not in Lambda runtime
pip3 install -t . pandas numpy scikit-learn --no-deps --quiet
# Create smaller package
zip -r ../budget-predictor.zip *.py -q
cd ../..

# Function 2: Resource Optimizer
echo "Packaging resource-optimizer..."
mkdir -p lambda-packages/resource-optimizer
cp lambda_functions/resource_optimizer_lambda.py lambda-packages/resource-optimizer/lambda_function.py
cd lambda-packages/resource-optimizer
pip3 install -t . boto3 --quiet
zip -r ../resource-optimizer.zip . -q
cd ../..

# Function 3: Feedback Processor
echo "Packaging feedback-processor..."
mkdir -p lambda-packages/feedback-processor
cp lambda_functions/feedback_processor_lambda.py lambda-packages/feedback-processor/lambda_function.py
cd lambda-packages/feedback-processor
pip3 install -t . boto3 --quiet
zip -r ../feedback-processor.zip . -q
cd ../..

echo "✅ Deployment packages created"

# Deploy functions
echo -e "\n3. Deploying Lambda functions..."

# Deploy Budget Predictor
echo "Deploying finops-budget-predictor..."
aws lambda create-function \
    --function-name finops-budget-predictor \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-packages/budget-predictor.zip \
    --timeout 300 \
    --memory-size 1024 \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Created finops-budget-predictor"
else
    aws lambda update-function-code \
        --function-name finops-budget-predictor \
        --zip-file fileb://lambda-packages/budget-predictor.zip
    echo "✅ Updated finops-budget-predictor"
fi

# Deploy Resource Optimizer
echo "Deploying finops-resource-optimizer..."
aws lambda create-function \
    --function-name finops-resource-optimizer \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-packages/resource-optimizer.zip \
    --timeout 300 \
    --memory-size 512 \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Created finops-resource-optimizer"
else
    aws lambda update-function-code \
        --function-name finops-resource-optimizer \
        --zip-file fileb://lambda-packages/resource-optimizer.zip
    echo "✅ Updated finops-resource-optimizer"
fi

# Deploy Feedback Processor
echo "Deploying finops-feedback-processor..."
aws lambda create-function \
    --function-name finops-feedback-processor \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-packages/feedback-processor.zip \
    --timeout 60 \
    --memory-size 256 \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Created finops-feedback-processor"
else
    aws lambda update-function-code \
        --function-name finops-feedback-processor \
        --zip-file fileb://lambda-packages/feedback-processor.zip
    echo "✅ Updated finops-feedback-processor"
fi

# Test functions
echo -e "\n4. Testing Lambda functions..."

# Test budget predictor
echo "Testing budget predictor..."
aws lambda invoke \
    --function-name finops-budget-predictor \
    --payload '{"days_ahead": 7, "months_history": 1}' \
    test-budget.json \
    --region $REGION

if [ -f test-budget.json ]; then
    echo "✅ Budget predictor test passed"
    cat test-budget.json | head -20
fi

# Clean up
rm -rf lambda-packages
rm -f trust-policy.json test-*.json

echo -e "\n=================================================="
echo "✅ LAMBDA DEPLOYMENT COMPLETED"
echo "=================================================="
echo "Functions deployed:"
echo "  - finops-budget-predictor"
echo "  - finops-resource-optimizer"
echo "  - finops-feedback-processor"
echo "=================================================="