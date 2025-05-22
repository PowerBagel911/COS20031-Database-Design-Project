# archery_app/security_admin.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from archery_app.security_logging import (
    get_security_logs, 
    mark_log_as_reviewed,
    mark_multiple_logs_as_reviewed,
    get_security_summary,
    SecurityEventType,
    SecuritySeverity
)

def security_logs_admin():
    st.title("Security Audit Logs")
    
    # Check if user has admin privileges
    if not st.session_state.is_admin:
        st.error("You do not have permission to access this page.")
        return
    
    # Create tabs for Summary and Log Details
    tab1, tab2 = st.tabs(["Security Dashboard", "Log Details"])
    
    with tab1:
        display_security_dashboard()
        
    with tab2:
        display_log_details()

def display_security_dashboard():
    st.header("Security Dashboard")
    
    # Time range selection
    col1, col2 = st.columns(2)
    with col1:
        time_range = st.selectbox(
            "Time Range", 
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
            index=1
        )
    
    # Convert time range to days
    if time_range == "Last 24 Hours":
        days = 1
    elif time_range == "Last 7 Days":
        days = 7
    elif time_range == "Last 30 Days":
        days = 30
    else:
        days = 365 * 10  # Effectively all time
    
    # Get summary statistics
    summary = get_security_summary(days)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Events", summary["total"])
    
    with col2:
        st.metric("Unreviewed", summary["unreviewed"])
    
    # Calculate critical and error events
    critical_count = sum(item["Count"] for item in summary["by_severity"] 
                        if item["Severity"] == SecuritySeverity.CRITICAL)
    error_count = sum(item["Count"] for item in summary["by_severity"] 
                     if item["Severity"] == SecuritySeverity.ERROR)
    
    with col3:
        st.metric("Critical Events", critical_count)
        
    with col4:
        st.metric("Error Events", error_count)
    
    # Display recent critical and error events
    st.subheader("Recent Critical and Error Events")
    
    # Get recent critical and error events
    logs = get_security_logs(
        start_date=datetime.now() - timedelta(days=days),
        severity=SecuritySeverity.CRITICAL,  # Change to a single value or fix the function
        limit=10
    )
    
    if logs:
        # Create a dataframe for display
        df = pd.DataFrame(logs)
        
        # Format the EventTime column
        df["EventTime"] = pd.to_datetime(df["EventTime"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Select columns to display
        display_df = df[["EventTime", "Severity", "EventType", "Description", "UserName"]]
        
        # Rename columns for better display
        display_df = display_df.rename(columns={
            "EventTime": "Time",
            "UserName": "User"
        })
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No critical or error events in the selected time period.")

def display_log_details():
    st.header("Security Log Details")
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
        end_date = st.date_input("End Date", value=datetime.now())
    
    with col2:
        # Event type filter
        event_types = [
            "All Types",
            SecurityEventType.AUTH_LOGIN_SUCCESS,
            SecurityEventType.AUTH_LOGIN_FAILURE,
            SecurityEventType.AUTH_LOGOUT,
            SecurityEventType.AUTH_PASSWORD_CHANGE,
            SecurityEventType.USER_PRIVILEGE_CHANGE,
            SecurityEventType.USER_ACCOUNT_CREATE,
            SecurityEventType.USER_ACCOUNT_DELETE,
            SecurityEventType.DATA_CREATE,
            SecurityEventType.DATA_UPDATE,
            SecurityEventType.DATA_DELETE,
            SecurityEventType.SECURITY_VIOLATION,
            SecurityEventType.POTENTIAL_INJECTION,
            SecurityEventType.APPLICATION_ERROR
        ]
        selected_event_type = st.selectbox("Event Type", event_types)
        
        # Convert "All Types" to None for the filter
        event_type_filter = None if selected_event_type == "All Types" else selected_event_type
    
    with col3:
        # Severity filter
        severities = [
            "All Severities",
            SecuritySeverity.INFO,
            SecuritySeverity.WARNING,
            SecuritySeverity.ERROR,
            SecuritySeverity.CRITICAL
        ]
        selected_severity = st.selectbox("Severity", severities)
        
        # Convert "All Severities" to None for the filter
        severity_filter = None if selected_severity == "All Severities" else selected_severity
    
    # Review status filter
    review_status = st.radio(
        "Review Status",
        ["All", "Unreviewed Only", "Reviewed Only"],
        horizontal=True
    )
    
    # Convert review status to boolean for filter
    if review_status == "Unreviewed Only":
        is_reviewed = False
    elif review_status == "Reviewed Only":
        is_reviewed = True
    else:
        is_reviewed = None
    
    # Get logs with the applied filters
    logs = get_security_logs(
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time()),
        event_type=event_type_filter,
        severity=severity_filter,
        is_reviewed=is_reviewed,
        limit=100
    )
    
    if logs:
        # Create a dataframe for display
        df = pd.DataFrame(logs)
        
        # Format the EventTime column
        df["EventTime"] = pd.to_datetime(df["EventTime"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a formatted dataframe for display
        display_df = df[[
            "LogID", "EventTime", "Severity", "EventType", 
            "Description", "UserName", "ArcherName", "IsReviewed"
        ]]
        
        # Rename columns for better display
        display_df = display_df.rename(columns={
            "LogID": "ID",
            "EventTime": "Time",
            "UserName": "User",
            "ArcherName": "Archer",
            "IsReviewed": "Reviewed"
        })
        
        # Convert boolean to Yes/No
        display_df["Reviewed"] = display_df["Reviewed"].map({True: "Yes", False: "No"})
        
        # Display the logs
        st.dataframe(display_df, use_container_width=True)
        
        # Add functionality to mark logs as reviewed
        st.subheader("Mark Logs as Reviewed")
        
        # Create tabs for single log review and bulk review
        review_tab1, review_tab2 = st.tabs(["Review Single Log", "Bulk Review"])
        
        with review_tab1:
            log_id_to_review = st.number_input("Log ID to Mark as Reviewed", min_value=1, step=1)
            
            if st.button("Mark as Reviewed"):
                if mark_log_as_reviewed(log_id_to_review, st.session_state.user_id):
                    st.success(f"Log ID {log_id_to_review} marked as reviewed.")
                    st.rerun()  # Refresh the page to show updated status
                else:
                    st.error("Failed to mark log as reviewed. Please check the Log ID.")
        
        with review_tab2:
            # Filter unreviewed logs for multi-select
            unreviewed_logs = [log for log in logs if not log["IsReviewed"]]
            
            if unreviewed_logs:
                st.write(f"There are {len(unreviewed_logs)} unreviewed logs matching your filters.")
                
                # Create options for multi-select
                options = {
                    f"ID: {log['LogID']} - {log['EventTime']} - {log['EventType']}": log["LogID"] 
                    for log in unreviewed_logs
                }
                
                # Multi-select for logs
                selected_options = st.multiselect(
                    "Select logs to mark as reviewed",
                    options=list(options.keys())
                )
                
                # Get log IDs from selected options
                selected_log_ids = [options[option] for option in selected_options]
                
                # Review all visible logs option
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mark Selected Logs as Reviewed", disabled=len(selected_log_ids) == 0):
                        success_count, failed_count = mark_multiple_logs_as_reviewed(
                            selected_log_ids, 
                            st.session_state.user_id
                        )
                        if success_count > 0:
                            st.success(f"Successfully marked {success_count} logs as reviewed.")
                            if failed_count > 0:
                                st.warning(f"Failed to mark {failed_count} logs as reviewed.")
                            st.rerun()  # Refresh the page to show updated status
                        else:
                            st.error("Failed to mark logs as reviewed.")
                
                with col2:
                    # Option to mark all visible unreviewed logs as reviewed
                    all_unreviewed_ids = [log["LogID"] for log in unreviewed_logs]
                    if st.button(f"Mark All {len(all_unreviewed_ids)} Unreviewed Logs", disabled=len(all_unreviewed_ids) == 0):
                        success_count, failed_count = mark_multiple_logs_as_reviewed(
                            all_unreviewed_ids, 
                            st.session_state.user_id
                        )
                        if success_count > 0:
                            st.success(f"Successfully marked {success_count} logs as reviewed.")
                            if failed_count > 0:
                                st.warning(f"Failed to mark {failed_count} logs as reviewed.")
                            st.rerun()  # Refresh the page to show updated status
                        else:
                            st.error("Failed to mark logs as reviewed.")
            else:
                st.info("No unreviewed logs found matching your filters.")
    else:
        st.info("No logs found matching the selected filters.")