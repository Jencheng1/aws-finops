#!/usr/bin/env python3
"""Simple test with 9 tabs to verify Streamlit behavior"""

import streamlit as st

st.set_page_config(page_title="Test 9 Tabs", layout="wide")

st.title("Testing 9 Tabs Display")

# Create 9 tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Tab 1",
    "Tab 2", 
    "Tab 3",
    "Tab 4",
    "Tab 5",
    "Tab 6",
    "Tab 7",
    "Tab 8 - NEW",
    "Tab 9 - NEW"
])

with tab1:
    st.header("This is Tab 1")
    
with tab2:
    st.header("This is Tab 2")
    
with tab3:
    st.header("This is Tab 3")
    
with tab4:
    st.header("This is Tab 4")
    
with tab5:
    st.header("This is Tab 5")
    
with tab6:
    st.header("This is Tab 6")
    
with tab7:
    st.header("This is Tab 7")
    
with tab8:
    st.header("This is Tab 8 - NEW FEATURE")
    st.write("Report Generator would go here")
    
with tab9:
    st.header("This is Tab 9 - NEW FEATURE")
    st.write("Tag Compliance would go here")