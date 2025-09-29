# FinOps Copilot

## Overview

FinOps Copilot is an AI-powered multi-agent system built on AWS Bedrock that provides comprehensive AWS cost optimization insights and recommendations. The system leverages specialized agents, Model Context Protocol (MCP) servers, and Agent-to-Agent (A2A) communication to analyze AWS costs, resource utilization, and tagging compliance, and generate actionable cost-saving recommendations.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for different AWS services and optimization strategies
- **Comprehensive Cost Analysis**: Detailed cost trend analysis, service breakdown, and forecasting
- **Resource Optimization**: Recommendations for right-sizing, reserved instances, and other cost-saving opportunities
- **Tagging and Environment Tracking**: Analysis of tagging compliance and cost allocation by environment
- **Interactive Visualizations**: Rich visualizations of cost trends, service breakdown, and optimization opportunities
- **Executive Summaries**: Concise summaries of key findings and recommendations for stakeholders

## System Architecture

The FinOps Copilot system consists of the following components:

### Agents

- **Orchestrator Agent**: Coordinates the activities of all other agents
- **Service Agents**: Specialize in specific AWS services (EC2, S3, RDS)
- **Strategy Agents**: Specialize in cross-service optimization strategies

### MCP Servers

- **Cost Explorer MCP Server**: Provides access to AWS Cost Explorer data
- **CloudWatch MCP Server**: Provides access to AWS CloudWatch metrics
- **Tagging MCP Server**: Provides access to AWS resource tagging data

### Analysis Components

- **Cost Analyzer**: Provides comprehensive cost analysis functionality
- **Tagging Analyzer**: Provides comprehensive tagging analysis functionality

### Communication Framework

- **A2A Communication Server**: Facilitates communication between agents
- **A2A Client**: Enables agents to communicate with each other

## Getting Started

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured with appropriate credentials
- Python 3.8 or higher
- Node.js 14 or higher
- Docker (for local testing)

### Installation

#### Local Development

1. Clone the repository:

```bash
git clone https://github.com/yourusername/finops-copilot.git
cd finops-copilot
```

2. Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
cd ..
```

3. Install frontend dependencies:

```bash
cd frontend
pip install -r requirements.txt
cd ..
```

4. Configure AWS credentials:

```bash
aws configure
```

5. Set up local environment variables:

```bash
cp .env.example .env
# Edit .env file with your configuration
```

6. Start the backend services:

```bash
cd backend
python local_server.py
```

7. Start the frontend:

```bash
cd frontend
streamlit run app.py
```

8. Access the application:

Open your web browser and navigate to `http://localhost:8501`.

#### AWS Deployment

1. Clone the repository:

```bash
git clone https://github.com/yourusername/finops-copilot.git
cd finops-copilot
```

2. Configure deployment parameters:

```bash
cd deployment
cp config.json.example config.json
# Edit config.json with your configuration
```

3. Deploy the solution:

```bash
./deploy.sh
```

4. Access the application:

The deployment script will output the URL of the Streamlit dashboard.

## Documentation

- [Architecture Documentation](/documentation/architecture_diagram.md)
- [User Guide](/documentation/user_guide.md)
- [Technical Documentation](/documentation/technical_documentation.md)
- [Deployment Guide](/documentation/deployment_guide.md)

## Testing

To run the tests, use the test runner script:

```bash
cd tests
./run_tests.py --all
```

This will run all tests and generate a report in the `tests/reports/` directory.

To run specific tests, use the following options:

```bash
# Run unit tests
./run_tests.py --unit

# Run integration tests
./run_tests.py --integration

# Run end-to-end tests
./run_tests.py --e2e

# Run performance tests
./run_tests.py --performance

# Run security tests
./run_tests.py --security
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- AWS Bedrock team for providing the foundation models and agent capabilities
- AWS Cost Explorer team for providing the cost data APIs
- The open-source community for providing the tools and libraries used in this project
