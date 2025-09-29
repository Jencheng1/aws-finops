# FinOps Copilot: AWS Cost Intelligence with MCP Integration

FinOps Copilot is an AI-powered multi-agent system built on AWS Bedrock that provides comprehensive AWS cost optimization insights and recommendations. The system leverages specialized agents, Model Context Protocol (MCP) servers, and Agent-to-Agent (A2A) communication to analyze AWS costs, resource utilization, and tagging compliance, and generate actionable cost-saving recommendations.

## Architecture

The FinOps Copilot system consists of the following components:

### MCP Servers

- **IBM Cloudability MCP Server**: Provides access to IBM Cloudability cost data and optimization recommendations
- **Apptio MCP Server**: Provides access to Apptio cost data and optimization recommendations
- **AWS Cost Explorer MCP Server**: Provides access to AWS Cost Explorer data and Savings Plans recommendations
- **AWS Resource Intelligence MCP Server**: Provides access to AWS resource utilization data and idle resource detection

### AWS Bedrock Agents

- **Orchestrator Agent**: Coordinates the activities of all other agents
- **Cost Analysis Agent**: Analyzes cost data from multiple sources
- **Resource Optimization Agent**: Identifies opportunities to optimize AWS resources
- **Savings Plan Recommendation Agent**: Provides recommendations for AWS Savings Plans

### Chatbot Interface

- **Streamlit Application**: Provides a web-based interface for interacting with the system
- **Natural Language Query Processing**: Allows users to ask questions in natural language
- **Interactive Visualizations**: Displays cost data and trends in an easy-to-understand format
- **Actionable Recommendations**: Provides specific recommendations for cost optimization

## Features

- **Comprehensive Cost Analysis**: Detailed cost trend analysis, service breakdown, and forecasting
- **Resource Optimization**: Recommendations for right-sizing, reserved instances, and other cost-saving opportunities
- **Tagging and Environment Tracking**: Analysis of tagging compliance and cost allocation by environment
- **Interactive Visualizations**: Rich visualizations of cost trends, service breakdown, and optimization opportunities
- **Executive Summaries**: Concise summaries of key findings and recommendations for stakeholders

## Getting Started

### Prerequisites

- Python 3.10 or higher
- AWS account with appropriate permissions
- IBM Cloudability account (optional)
- Apptio account (optional)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/finops-copilot.git
cd finops-copilot
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=your_region
export CLOUDABILITY_API_KEY=your_cloudability_api_key
export APPTIO_API_KEY=your_apptio_api_key
export APPTIO_ENV_ID=your_apptio_env_id
```

### Running the MCP Servers

1. Start the IBM Cloudability MCP server:

```bash
python cloudability_mcp_server.py
```

2. Start the Apptio MCP server:

```bash
python apptio_mcp_server.py
```

3. Start the AWS Cost Explorer MCP server:

```bash
python aws_cost_explorer_mcp_server.py
```

4. Start the AWS Resource Intelligence MCP server:

```bash
python aws_resource_intelligence_mcp_server.py
```

### Running the Chatbot Interface

```bash
streamlit run aws_cost_chatbot.py
```

## Usage

1. Open the chatbot interface in your web browser at `http://localhost:8501`.
2. Use the sidebar to set filters for time period, services, accounts, regions, and tags.
3. Ask questions about your AWS costs and resource usage in natural language.
4. View the responses, visualizations, and recommendations provided by the system.

## Example Queries

- "What's my AWS cost breakdown for the last month?"
- "How can I optimize my EC2 costs?"
- "Do I have any idle resources that I can remove?"
- "What Savings Plans would you recommend for my usage?"
- "How has my S3 cost trend changed over the past 3 months?"

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AWS Bedrock team for providing the multi-agent collaboration capability
- IBM Cloudability and Apptio for their cost management platforms
- Model Context Protocol (MCP) for enabling seamless integration between AI applications and external systems
