        if st.button("🚀 Run Optimization Scan", type="primary"):
            with st.spinner("Scanning for optimization opportunities..."):
                # Use multi-agent processor (most reliable approach)
                try:
                    response, opt_results = processor.process_optimizer_query("Find idle resources", 
                                                                           {'user_id': st.session_state.user_id, 'session_id': 'optimization'})
                    
                    if opt_results and 'summary' in opt_results:
                        st.success("✅ Scan completed!")
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Stopped Instances", opt_results['summary']['stopped_instances_count'])
                        with col2:
                            st.metric("Unattached Volumes", opt_results['summary']['unattached_volumes_count'])
                        with col3:
                            st.metric("Unused EIPs", opt_results['summary']['unused_eips_count'])
                        with col4:
                            st.metric("Orphaned Snapshots", opt_results['summary']['orphaned_snapshots_count'])
                        with col5:
                            st.metric("Monthly Savings", f"${opt_results['total_monthly_savings']:,.2f}")
                        
                        # Show recommendations if opportunities found
                        total_opportunities = sum(opt_results['summary'].values())
                        if total_opportunities > 0:
                            st.subheader("💡 Optimization Recommendations")
                            if opt_results['summary']['stopped_instances_count'] > 0:
                                st.write("1. **Stopped Instances**: Terminate unused instances to save on storage costs")
                            if opt_results['summary']['unattached_volumes_count'] > 0:
                                st.write("2. **Unattached Volumes**: Delete unused volumes or create snapshots for backup")
                            if opt_results['summary']['unused_eips_count'] > 0:
                                st.write("3. **Elastic IPs**: Release unassociated Elastic IPs immediately")
                            if opt_results['summary']['underutilized_instances_count'] > 0:
                                st.write("4. **Underutilized Instances**: Right-size instances with <10% CPU usage")
                            if opt_results['summary']['orphaned_snapshots_count'] > 0:
                                st.write("5. **Orphaned Snapshots**: Delete snapshots of volumes that no longer exist")
                            
                            annual_savings = opt_results['total_monthly_savings'] * 12
                            st.success(f"🎯 **Total Optimization Potential**: ${opt_results['total_monthly_savings']:,.2f}/month (${annual_savings:,.2f}/year)")
                        else:
                            st.info("✨ Good news! No optimization opportunities found. Your resources are well-managed.")
                    else:
                        st.warning("Scan completed but no detailed results available")
                        
                except Exception as e:
                    st.error(f"Error during optimization scan: {str(e)[:100]}")
                    st.info("The multi-agent optimizer encountered an issue. Please try again or contact support.")