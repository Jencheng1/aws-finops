#!/bin/bash

# FinOps Copilot Deployment Script
# This script deploys the FinOps Copilot solution to AWS

set -e

# Configuration
CONFIG_FILE="config.json"
TEMPLATE_DIR="cloudformation/templates"
LAMBDA_DIR="../lambda-functions"
FRONTEND_DIR="../frontend"
PACKAGE_DIR="package"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print error messages and exit
print_error_and_exit() {
    print_message "${RED}" "ERROR: $1"
    exit 1
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error_and_exit "$1 is required but not installed. Please install it and try again."
    fi
}

# Function to check if AWS CLI is configured
check_aws_cli() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error_and_exit "AWS CLI is not configured. Please run 'aws configure' and try again."
    fi
}

# Function to check if the config file exists
check_config_file() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error_and_exit "Config file $CONFIG_FILE not found."
    fi
}

# Function to get a value from the config file
get_config_value() {
    local key=$1
    local value=$(jq -r ".$key" "$CONFIG_FILE")
    if [ "$value" == "null" ]; then
        print_error_and_exit "Config value $key not found in $CONFIG_FILE."
    fi
    echo "$value"
}

# Function to get a parameter value from the config file
get_parameter_value() {
    local key=$1
    local value=$(jq -r ".Parameters.$key" "$CONFIG_FILE")
    if [ "$value" == "null" ]; then
        print_error_and_exit "Parameter $key not found in $CONFIG_FILE."
    fi
    echo "$value"
}

# Function to create a package directory
create_package_dir() {
    if [ -d "$PACKAGE_DIR" ]; then
        rm -rf "$PACKAGE_DIR"
    fi
    mkdir -p "$PACKAGE_DIR"
}

# Function to package Lambda functions
package_lambda_functions() {
    print_message "${BLUE}" "Packaging Lambda functions..."
    
    # Create a temporary directory for packaging
    local temp_dir=$(mktemp -d)
    
    # Package each Lambda function
    for lambda_file in "$LAMBDA_DIR"/*.py; do
        local lambda_name=$(basename "$lambda_file" .py)
        print_message "${YELLOW}" "Packaging $lambda_name..."
        
        # Create a zip file for the Lambda function
        cp "$lambda_file" "$temp_dir/lambda_function.py"
        cd "$temp_dir"
        zip -q "$lambda_name.zip" lambda_function.py
        cd - > /dev/null
        
        # Move the zip file to the package directory
        mv "$temp_dir/$lambda_name.zip" "$PACKAGE_DIR/$lambda_name.zip"
    done
    
    # Clean up
    rm -rf "$temp_dir"
    
    print_message "${GREEN}" "Lambda functions packaged successfully."
}

# Function to upload Lambda packages to S3
upload_lambda_packages() {
    local bucket_name=$1
    
    print_message "${BLUE}" "Uploading Lambda packages to S3..."
    
    # Create the S3 bucket if it doesn't exist
    if ! aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        print_message "${YELLOW}" "Creating S3 bucket $bucket_name..."
        aws s3api create-bucket --bucket "$bucket_name" --region $(get_config_value "Region")
    fi
    
    # Upload each Lambda package to S3
    for zip_file in "$PACKAGE_DIR"/*.zip; do
        local zip_name=$(basename "$zip_file")
        print_message "${YELLOW}" "Uploading $zip_name to S3..."
        aws s3 cp "$zip_file" "s3://$bucket_name/lambda/$zip_name"
    done
    
    print_message "${GREEN}" "Lambda packages uploaded successfully."
}

# Function to deploy the CloudFormation stack
deploy_cloudformation_stack() {
    local stack_name=$1
    local template_file=$2
    local region=$3
    
    print_message "${BLUE}" "Deploying CloudFormation stack $stack_name..."
    
    # Create parameter overrides
    local parameter_overrides=""
    for key in $(jq -r '.Parameters | keys[]' "$CONFIG_FILE"); do
        local value=$(get_parameter_value "$key")
        parameter_overrides="$parameter_overrides $key=$value"
    done
    
    # Deploy the CloudFormation stack
    aws cloudformation deploy \
        --template-file "$template_file" \
        --stack-name "$stack_name" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region "$region" \
        --parameter-overrides $parameter_overrides
    
    print_message "${GREEN}" "CloudFormation stack $stack_name deployed successfully."
}

# Function to deploy the Streamlit frontend
deploy_streamlit_frontend() {
    print_message "${BLUE}" "Deploying Streamlit frontend..."
    
    # Get the API endpoint and API key from the CloudFormation stack outputs
    local stack_name=$(get_config_value "StackName")
    local api_endpoint=$(aws cloudformation describe-stacks --stack-name "$stack_name" --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
    local api_key=$(aws cloudformation describe-stacks --stack-name "$stack_name" --query "Stacks[0].Outputs[?OutputKey=='ApiKey'].OutputValue" --output text)
    
    # Create a .streamlit directory in the frontend directory if it doesn't exist
    mkdir -p "$FRONTEND_DIR/.streamlit"
    
    # Create a config.toml file in the .streamlit directory
    cat > "$FRONTEND_DIR/.streamlit/config.toml" << EOF
[theme]
primaryColor = "#FF9900"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
EOF
    
    # Create a secrets.toml file in the .streamlit directory
    cat > "$FRONTEND_DIR/.streamlit/secrets.toml" << EOF
[api]
endpoint = "$api_endpoint"
key = "$api_key"
EOF
    
    print_message "${GREEN}" "Streamlit frontend deployed successfully."
}

# Function to print the deployment summary
print_deployment_summary() {
    local stack_name=$(get_config_value "StackName")
    local region=$(get_config_value "Region")
    
    print_message "${BLUE}" "Deployment Summary:"
    
    # Get the CloudFormation stack outputs
    local outputs=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" --query "Stacks[0].Outputs" --output json)
    
    # Print each output
    for output in $(echo "$outputs" | jq -r '.[] | @base64'); do
        local key=$(echo "$output" | base64 --decode | jq -r '.OutputKey')
        local value=$(echo "$output" | base64 --decode | jq -r '.OutputValue')
        print_message "${GREEN}" "$key: $value"
    done
}

# Main function
main() {
    print_message "${BLUE}" "Starting FinOps Copilot deployment..."
    
    # Check prerequisites
    check_command "aws"
    check_command "jq"
    check_command "zip"
    check_aws_cli
    check_config_file
    
    # Get configuration values
    local stack_name=$(get_config_value "StackName")
    local region=$(get_config_value "Region")
    local environment=$(get_parameter_value "Environment")
    
    # Create package directory
    create_package_dir
    
    # Package Lambda functions
    package_lambda_functions
    
    # Upload Lambda packages to S3
    local bucket_name="finops-copilot-assets-$environment-$(aws sts get-caller-identity --query "Account" --output text)"
    upload_lambda_packages "$bucket_name"
    
    # Deploy CloudFormation stack
    deploy_cloudformation_stack "$stack_name" "$TEMPLATE_DIR/main.yaml" "$region"
    
    # Deploy Streamlit frontend
    deploy_streamlit_frontend
    
    # Print deployment summary
    print_deployment_summary
    
    print_message "${GREEN}" "FinOps Copilot deployment completed successfully."
}

# Run the main function
main
