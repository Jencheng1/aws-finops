#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified EC2 drill-down section for the dashboard
This replaces the complex broken section
"""

def render_ec2_drilldown(st, selected_service, days_lookback, resource_costs, group_type, clients, datetime, pd, px):
    """Render EC2 drill-down section in streamlit"""
    
    # For EC2, show comprehensive instance details
    if selected_service == 'AmazonEC2':
        st.info("💡 **Note**: Cost Explorer groups EC2 costs by usage type (EBS volumes, snapshots, etc.). Below are all your EC2 instances with detailed metrics.")
        
        # Show the usage type breakdown first
        st.markdown("### 📊 EC2 Cost Breakdown by Usage Type")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Top usage types by cost
            st.markdown("**💰 Top Usage Types:**")
            top_resources = sorted(resource_costs.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if top_resources:
                resource_df = pd.DataFrame(top_resources, columns=['Usage Type', 'Total Cost'])
                resource_df['Total Cost'] = resource_df['Total Cost'].apply(lambda x: f"${x:,.2f}")
                
                # Create bar chart
                fig = px.bar(resource_df, x='Total Cost', y='Usage Type', orientation='h')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart of usage types
            st.markdown("**📊 Cost Distribution:**")
            fig_pie = px.pie(values=[x[1] for x in top_resources], 
                            names=[x[0] for x in top_resources])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Now show EC2 instances
        st.markdown("### 🖥️ EC2 Instance Details")
        
        try:
            # Import the utility function
            import sys
            sys.path.append('.')
            from get_ec2_details_with_costs import get_ec2_instance_details_with_costs
            
            # Get comprehensive EC2 data
            with st.spinner("Fetching EC2 instance data with real-time metrics..."):
                df_ec2_details, ec2_summary = get_ec2_instance_details_with_costs(days_lookback=days_lookback)
            
            # Display EC2 summary metrics
            metric_cols = st.columns(6)
            with metric_cols[0]:
                st.metric("Total Instances", ec2_summary['total_instances'])
            with metric_cols[1]:
                st.metric("Running", ec2_summary['running_instances'])
            with metric_cols[2]:
                st.metric("Stopped", ec2_summary['stopped_instances'])
            with metric_cols[3]:
                st.metric("Underutilized", ec2_summary['underutilized_count'])
            with metric_cols[4]:
                st.metric("Monthly Cost", f"${ec2_summary['total_monthly_cost']:,.0f}")
            with metric_cols[5]:
                st.metric("Savings Potential", f"${ec2_summary['potential_monthly_savings']:,.0f}")
            
            # Show instance table
            st.markdown("**📋 Instance List:**")
            
            # Simple display of all instances
            if not df_ec2_details.empty:
                # Select columns to display
                display_columns = ['Instance ID', 'Name', 'Type', 'State', 'CPU Avg %', 'Monthly Cost', 'Optimization']
                display_df = df_ec2_details[display_columns].copy()
                
                # Color code by optimization status
                def highlight_rows(row):
                    if row['Optimization'] == 'Underutilized':
                        return ['background-color: #fff3cd'] * len(row)
                    elif row['Optimization'] == 'Stop to save':
                        return ['background-color: #f8d7da'] * len(row)
                    else:
                        return [''] * len(row)
                
                styled_df = display_df.style.apply(highlight_rows, axis=1)
                st.dataframe(styled_df, use_container_width=True, height=400)
                
                # Download button
                csv = df_ec2_details.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full EC2 Details CSV",
                    data=csv,
                    file_name=f"ec2_instances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Show optimization opportunities
                if ec2_summary['underutilized_count'] > 0 or ec2_summary['stopped_instances'] > 0:
                    st.markdown("### 💡 Optimization Recommendations")
                    
                    if ec2_summary['underutilized_count'] > 0:
                        underutilized = df_ec2_details[df_ec2_details['Optimization'] == 'Underutilized']
                        st.warning(f"⚠️ {len(underutilized)} instances have CPU < 10% - consider downsizing")
                        
                    if ec2_summary['stopped_instances'] > 0:
                        stopped = df_ec2_details[df_ec2_details['State'] == 'stopped']
                        st.info(f"💰 {len(stopped)} stopped instances still incurring storage costs")
            else:
                st.warning("No EC2 instances found in this account")
                
        except Exception as e:
            st.error(f"Could not load detailed EC2 instance data: {str(e)[:100]}")
            st.info("Showing cost breakdown by usage type only.")
    
    # For non-EC2 services, show standard breakdown
    else:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.info(f"**📋 Resource Type**: {group_type.replace('_', ' ').title()}")
        
        with col2:
            # Top resources by cost
            st.markdown("**💰 Top Resources by Cost:**")
            top_resources = sorted(resource_costs.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if top_resources:
                resource_df = pd.DataFrame(top_resources, columns=['Resource', 'Total Cost'])
                resource_df['Total Cost'] = resource_df['Total Cost'].apply(lambda x: f"${x:,.2f}")
                resource_df['Resource'] = resource_df['Resource'].apply(lambda x: x[:40] + '...' if len(x) > 40 else x)
                st.dataframe(resource_df, use_container_width=True)