# AWS Architecture Diagram Guidelines - Research Findings

## Key Guidelines for Physical View Diagrams (AWS Architectural Diagrams):

1. **Consistency is Key**: Use the latest official AWS diagramming icon set consistently. Don't mix different versions of icon sets.

2. **Focus and Clarity**: Depict one or at most two flows in a single diagram. Don't try to showcase every flow and resource in one diagram.

3. **Proper Scoping**: 
   - Show AWS account boundaries, even for single-account solutions
   - Represent global, regional, and zonal AWS services according to their scopes
   - S3 is global (inside account but not within VPC)
   - VPC is regional (should live in a region)

4. **Visual Organization**:
   - Put the title on top, communicating the system and diagram's purpose
   - Use standard conventions (private subnets with blue background, public subnets with green)
   - Show logical grouping with boxes and intermittent lines
   - Use different colors for different traffic flows to avoid too many lines

5. **Flow Representation**:
   - Check arrow directions for proper flow depiction
   - Show return traffic with intermittent arrows
   - Avoid too many connection lines - use colors or skip connections when necessary

6. **Maintenance**: 
   - Ensure periodic review and maintenance of diagrams
   - At least one diagram should represent the exact production environment

## Icon Resources:
- AWS provides official icon sets for consistency
- Available for multiple diagramming tools
- Should not mix vendor-specific symbols in logical views
- Use simple shapes for components in logical views

## Best Practices for FinOps Copilot Diagram:
- Keep it high-level and simple
- Use directional arrows to show data flow
- Group related components logically
- Focus on the multi-agent architecture and data flow
- Show AWS services integration clearly
