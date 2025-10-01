#!/usr/bin/env python3
"""
Create Lambda deployment packages with dependencies
"""

import os
import zipfile
import shutil
import subprocess
import sys

def create_lambda_package(function_name, handler_file):
    """Create a deployment package for Lambda function"""
    print(f"\nCreating package for {function_name}...")
    
    # Create temp directory
    temp_dir = f"/tmp/{function_name}"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Copy handler file
    shutil.copy(handler_file, temp_dir)
    
    # Create requirements file based on function
    requirements = []
    
    if 'budget' in function_name:
        requirements = ['pandas', 'numpy', 'scikit-learn']
    elif 'feedback' in function_name:
        requirements = ['boto3']
    else:
        requirements = ['boto3']
    
    if requirements:
        req_file = f"{temp_dir}/requirements.txt"
        with open(req_file, 'w') as f:
            f.write('\n'.join(requirements))
        
        # Install dependencies
        print(f"Installing dependencies: {', '.join(requirements)}")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '-r', req_file,
            '-t', temp_dir,
            '--no-deps'
        ], capture_output=True)
    
    # Create ZIP file
    zip_file = f"{function_name}.zip"
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print(f"✓ Created {zip_file} ({os.path.getsize(zip_file) / 1024 / 1024:.2f} MB)")
    return zip_file

# Create packages
packages = [
    ('finops-budget-predictor', 'budget_predictor_lambda.py'),
    ('finops-resource-optimizer', 'resource_optimizer_lambda.py'),
    ('finops-feedback-processor', 'feedback_processor_lambda.py')
]

for function_name, handler_file in packages:
    if os.path.exists(handler_file):
        create_lambda_package(function_name, handler_file)
    else:
        print(f"✗ Handler file not found: {handler_file}")