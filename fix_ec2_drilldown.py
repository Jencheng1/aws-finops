#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix for EC2 drill-down - to be integrated into dashboard
"""

# This is the corrected structure for the EC2 drill-down section
# Starting from line 490 in finops_intelligent_dashboard.py

ec2_drilldown_code = '''
                    # For EC2, show comprehensive instance details
                    if selected_service == 'AmazonEC2':
                        st.info("💡 **Note**: Cost Explorer groups EC2 costs by usage type. Below are all your EC2 instances with detailed metrics and costs.")
                        
                        try:
                            # Import the utility function
                            from get_ec2_details_with_costs import get_ec2_instance_details_with_costs
                            
                            # Get comprehensive EC2 data
                            with st.spinner("Fetching detailed EC2 instance data with real-time metrics..."):
                                df_ec2_details, ec2_summary = get_ec2_instance_details_with_costs(days_lookback=days_lookback)
                            
                            # Display EC2 summary metrics
                            st.markdown("**🖥️ EC2 Fleet Overview:**")
                            metric_cols = st.columns(6)
                            with metric_cols[0]:
                                st.metric("Total Instances", ec2_summary['total_instances'])
                            with metric_cols[1]:
                                st.metric("Running", ec2_summary['running_instances'], 
                                         delta=f"{ec2_summary['running_instances']}/{ec2_summary['total_instances']}")
                            with metric_cols[2]:
                                st.metric("Stopped", ec2_summary['stopped_instances'])
                            with metric_cols[3]:
                                st.metric("Underutilized", ec2_summary['underutilized_count'])
                            with metric_cols[4]:
                                st.metric("Monthly Cost", f"${ec2_summary['total_monthly_cost']:,.0f}")
                            with metric_cols[5]:
                                st.metric("Potential Savings", f"${ec2_summary['potential_monthly_savings']:,.0f}")
                            
                            # Detailed instance table with filtering
                            st.markdown("**📊 Detailed Instance Information:**")
                            
                            # Add filters
                            filter_cols = st.columns([2, 2, 2, 2])
                            with filter_cols[0]:
                                state_filter = st.multiselect(
                                    "State", 
                                    options=df_ec2_details['State'].unique().tolist(),
                                    default=df_ec2_details['State'].unique().tolist()
                                )
                            with filter_cols[1]:
                                type_filter = st.multiselect(
                                    "Instance Type",
                                    options=sorted(df_ec2_details['Type'].unique().tolist()),
                                    default=sorted(df_ec2_details['Type'].unique().tolist())
                                )
                            with filter_cols[2]:
                                optimization_filter = st.multiselect(
                                    "Optimization Status",
                                    options=df_ec2_details['Optimization'].unique().tolist(),
                                    default=df_ec2_details['Optimization'].unique().tolist()
                                )
                            with filter_cols[3]:
                                show_columns = st.multiselect(
                                    "Show Columns",
                                    options=['Instance ID', 'Name', 'Type', 'State', 'Region', 'AZ', 
                                            'Launch Time', 'CPU Avg %', 'CPU Max %', 'Network In (MB)', 
                                            'Network Out (MB)', 'Storage (GB)', f'{days_lookback}d Cost', 
                                            'Monthly Cost', 'Annual Cost', 'Optimization'],
                                    default=['Instance ID', 'Name', 'Type', 'State', 'CPU Avg %', 
                                            'Monthly Cost', 'Optimization']
                                )
                            
                            # Apply filters
                            filtered_df = df_ec2_details[
                                (df_ec2_details['State'].isin(state_filter)) &
                                (df_ec2_details['Type'].isin(type_filter)) &
                                (df_ec2_details['Optimization'].isin(optimization_filter))
                            ]
                            
                            # Display filtered dataframe
                            if not filtered_df.empty:
                                # Create a copy for display with formatted currency columns
                                display_df = filtered_df[show_columns].copy()
                                
                                # Format currency columns
                                currency_columns = ['Monthly Cost', 'Annual Cost', f'{days_lookback}d Cost']
                                for col in currency_columns:
                                    if col in display_df.columns:
                                        display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                                
                                # Display the dataframe
                                st.dataframe(display_df, use_container_width=True, height=400)
                                
                                # Download button for CSV export
                                csv = filtered_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download EC2 Details as CSV",
                                    data=csv,
                                    file_name=f"ec2_instance_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.warning("No instances match the selected filters")
                            
                            # Instance type distribution
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**📊 Instance Type Distribution:**")
                                type_counts = df_ec2_details['Type'].value_counts().head(10)
                                fig_types = px.bar(
                                    x=type_counts.values,
                                    y=type_counts.index,
                                    orientation='h',
                                    labels={'x': 'Count', 'y': 'Instance Type'}
                                )
                                fig_types.update_layout(height=300)
                                st.plotly_chart(fig_types, use_container_width=True)
                            
                            with col2:
                                st.markdown("**💰 Cost by Instance State:**")
                                state_costs = df_ec2_details.groupby('State')['Monthly Cost'].sum()
                                fig_state_costs = px.pie(
                                    values=state_costs.values,
                                    names=state_costs.index,
                                    hole=0.3
                                )
                                fig_state_costs.update_layout(height=300)
                                st.plotly_chart(fig_state_costs, use_container_width=True)
                            
                            # CPU utilization analysis
                            running_instances = df_ec2_details[df_ec2_details['State'] == 'running']
                            if not running_instances.empty:
                                st.markdown("**🔥 CPU Utilization Analysis (Running Instances):**")
                                
                                # Show underutilized instances
                                underutilized = running_instances[running_instances['CPU Avg %'] < 10]
                                if not underutilized.empty:
                                    st.warning(f"⚠️ {len(underutilized)} running instances have CPU utilization < 10%")
                                    with st.expander("View Underutilized Instances"):
                                        st.dataframe(
                                            underutilized[['Instance ID', 'Name', 'Type', 'CPU Avg %', 'Monthly Cost']],
                                            use_container_width=True
                                        )
                                        
                                        potential_savings = underutilized['Monthly Cost'].sum() * 0.5
                                        st.info(f"💡 Potential savings from rightsizing: ${potential_savings:,.2f}/month")
                            
                        except Exception as e:
                            st.error(f"Error fetching EC2 details: {str(e)[:200]}")
                            st.info("Showing cost breakdown by usage type instead.")
                    
                    # For all services (including EC2 if detailed view fails), show usage type breakdown
                    if selected_service != 'AmazonEC2' or 'df_ec2_details' not in locals():
                        # Display resource breakdown
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.info(f"**📋 Resource Type**: {group_type.replace('_', ' ').title()}")
                        
                        with col2:
                            # Top resources by cost
                            st.markdown("**💰 Top Resources by Cost:**")
                            top_resources = sorted(resource_costs.items(), key=lambda x: x[1], reverse=True)[:10]
                            
                            if top_resources:
                                # Create a more readable format
                                resource_df = pd.DataFrame(top_resources, columns=['Resource', 'Total Cost'])
                                resource_df['Total Cost'] = resource_df['Total Cost'].apply(lambda x: f"${x:,.2f}")
                                resource_df['Resource'] = resource_df['Resource'].apply(lambda x: x[:40] + '...' if len(x) > 40 else x)
                                st.dataframe(resource_df, use_container_width=True)
'''

print("Fix has been generated. This code should replace the broken section in finops_intelligent_dashboard.py")
print("The fix:")
print("1. Properly handles EC2 service detection")
print("2. Shows comprehensive instance details for EC2")
print("3. Falls back to usage type breakdown for other services")
print("4. Removes the broken col1/col2 structure that was causing issues")