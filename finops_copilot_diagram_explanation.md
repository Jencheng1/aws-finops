# FinOps Copilot: System Architecture and Data Flow Diagrams

## 1. High-Level Architecture Diagram

The high-level architecture diagram illustrates the main components of the FinOps Copilot system and how they interact with each other:

- **User Interface Layer**: The Streamlit chatbot interface where users can ask natural language questions about AWS costs and resource usage.
- **Agent Layer**: AWS Bedrock agents that process user queries and coordinate the retrieval and analysis of data.
- **MCP Server Layer**: Model Context Protocol servers that provide standardized interfaces to various data sources.
- **Data Source Layer**: External systems and APIs that provide cost and resource data.

The diagram shows how data flows from the user through the system and back, with each layer performing specific functions in the process.

## 2. Detailed Data Flow Diagram

The data flow diagram provides a sequence-based view of how information moves through the system when a user asks a question:

1. **Query Processing**: The user's natural language query is processed by the Orchestrator Agent to determine intent.
2. **Agent Delegation**: Based on the query intent, the Orchestrator delegates to specialized agents:
   - Cost Analysis Agent for cost-related queries
   - Resource Optimization Agent for resource utilization queries
   - Savings Plan Agent for savings plan recommendations
3. **MCP Integration**: Each agent communicates with appropriate MCP servers to retrieve data.
4. **Data Aggregation**: The agents consolidate and analyze data from multiple sources.
5. **Response Generation**: The Orchestrator combines insights from all agents to generate a comprehensive response.
6. **Visualization**: The chatbot interface creates visualizations based on the data and presents them to the user.

## 3. MCP Server Implementation Diagram

The MCP server implementation diagram shows the class structure of the four MCP servers:

- **CloudabilityMCPServer**: Provides access to IBM Cloudability data and features.
- **ApptioMCPServer**: Provides access to Apptio data and features.
- **AWSCostExplorerMCPServer**: Provides access to AWS Cost Explorer data and features.
- **AWSResourceIntelligenceMCPServer**: Provides access to AWS resource utilization data and features.

Each server implements the MCP interface and provides specialized tools for accessing and formatting data from its respective source.

## 4. AWS Bedrock Agent Implementation Diagram

The AWS Bedrock agent implementation diagram shows the internal structure of each agent:

- **Orchestrator Agent**: Coordinates the activities of all other agents and manages the overall response generation process.
- **Cost Analysis Agent**: Specializes in retrieving and analyzing cost data from multiple sources.
- **Resource Optimization Agent**: Specializes in identifying resource optimization opportunities.
- **Savings Plan Agent**: Specializes in generating savings plan recommendations.

Each agent consists of:
- A Large Language Model (LLM) for natural language understanding and generation
- An Action Group that defines the operations the agent can perform
- A Knowledge Base that stores domain-specific information

## Key Integration Points

1. **MCP Protocol**: Standardized interface between AWS Bedrock agents and external data sources.
2. **Agent-to-Agent Communication**: Coordinated by the Orchestrator Agent to ensure comprehensive analysis.
3. **Visualization Generation**: Transforms raw data into interactive visualizations in the chatbot interface.
4. **Natural Language Processing**: Converts user queries into structured data requests and analysis results back into natural language responses.

## Implementation Benefits

1. **Modularity**: Each component can be developed, tested, and updated independently.
2. **Extensibility**: New data sources can be added by implementing additional MCP servers.
3. **Scalability**: The multi-agent architecture allows for parallel processing of complex queries.
4. **User-Friendliness**: The natural language interface makes complex cost analysis accessible to non-technical users.
