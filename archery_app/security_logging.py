# archery_app/security_logging.py

import streamlit as st
import mysql.connector
from datetime import datetime
import json
from archery_app.database import get_connection

# Define security event types
class SecurityEventType:
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILURE = "AUTH_LOGIN_FAILURE"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_PASSWORD_CHANGE = "AUTH_PASSWORD_CHANGE"
    USER_PRIVILEGE_CHANGE = "USER_PRIVILEGE_CHANGE"
    USER_ACCOUNT_CREATE = "USER_ACCOUNT_CREATE"
    USER_ACCOUNT_DELETE = "USER_ACCOUNT_DELETE"
    DATA_CREATE = "DATA_CREATE"
    DATA_UPDATE = "DATA_UPDATE"
    DATA_DELETE = "DATA_DELETE"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    POTENTIAL_INJECTION = "POTENTIAL_INJECTION"
    APPLICATION_ERROR = "APPLICATION_ERROR"
    ARCHER_CREATE = "ARCHER_CREATE"
    SCORE_SUBMIT = "SCORE_SUBMIT"
    SCORE_APPROVE = "SCORE_APPROVE"
    COMPETITION_CREATE = "COMPETITION_CREATE"
    COMPETITION_UPDATE = "COMPETITION_UPDATE"

# Define severity levels
class SecuritySeverity:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# Get event severity based on event type
def get_event_severity(event_type):
    # Define which events are considered critical, errors, warnings
    critical_events = [
        SecurityEventType.SECURITY_VIOLATION,
        SecurityEventType.POTENTIAL_INJECTION
    ]
    
    error_events = [
        SecurityEventType.AUTH_LOGIN_FAILURE,
        SecurityEventType.APPLICATION_ERROR
    ]
    
    warning_events = [
        SecurityEventType.USER_PRIVILEGE_CHANGE,
        SecurityEventType.USER_ACCOUNT_DELETE,
        SecurityEventType.DATA_DELETE
    ]
    
    if event_type in critical_events:
        return SecuritySeverity.CRITICAL
    elif event_type in error_events:
        return SecuritySeverity.ERROR
    elif event_type in warning_events:
        return SecuritySeverity.WARNING
    else:
        return SecuritySeverity.INFO

# Log a security event
def log_security_event(event_type, description, user_id=None, archer_id=None, ip_address=None, request_details=None, action_url=None):
    """
    Log a security event to the SecurityLog table.
    
    Args:
        event_type (str): Type of security event
        description (str): Description of the event
        user_id (int, optional): UserID associated with the event
        archer_id (int, optional): ArcherID associated with the event
        ip_address (str, optional): IP address of the client
        request_details (dict, optional): Additional details about the request
        action_url (str, optional): URL/path of the action being performed
    """
    try:
        # Get current user ID from session state if not provided
        if user_id is None and "user_id" in st.session_state:
            user_id = st.session_state.user_id
            
        # Get archer ID from session state if not provided
        if archer_id is None and "archer_id" in st.session_state:
            archer_id = st.session_state.archer_id
        
        # Determine severity based on event type
        severity = get_event_severity(event_type)
        
        # Convert request details to JSON string if provided
        if request_details is not None:
            if isinstance(request_details, dict):
                request_details = json.dumps(request_details)
            else:
                request_details = str(request_details)
        
        # Connect to database
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert log entry
        query = """
        INSERT INTO SecurityLog (
            EventTime, UserID, ArcherID, IPAddress, EventType, 
            Description, Severity, ActionURL, RequestDetails, IsReviewed
        ) VALUES (
            NOW(), %s, %s, %s, %s, %s, %s, %s, %s, FALSE
        )
        """
        
        cursor.execute(query, (
            user_id, 
            archer_id, 
            ip_address, 
            event_type, 
            description, 
            severity, 
            action_url, 
            request_details
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        # Print error to console but don't disrupt application flow
        print(f"Error logging security event: {e}")
        return False

# Get list of security logs (for admin interface)
def get_security_logs(
    start_date=None, 
    end_date=None, 
    user_id=None, 
    event_type=None, 
    severity=None, 
    is_reviewed=None,
    limit=100,
    offset=0
):
    """
    Get security logs with optional filtering.
    
    Args:
        start_date (datetime, optional): Filter logs after this date
        end_date (datetime, optional): Filter logs before this date
        user_id (int, optional): Filter logs by user ID
        event_type (str, optional): Filter logs by event type
        severity (str, optional): Filter logs by severity
        is_reviewed (bool, optional): Filter logs by review status
        limit (int, optional): Maximum number of logs to return
        offset (int, optional): Offset for pagination
        
    Returns:
        list: List of security log entries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query with potential filters
        query = """
        SELECT l.*, 
               u1.Username as UserName,
               CONCAT(a.FirstName, ' ', a.LastName) as ArcherName,
               u2.Username as ReviewedByName
        FROM SecurityLog l
        LEFT JOIN AppUser u1 ON l.UserID = u1.UserID
        LEFT JOIN Archer a ON l.ArcherID = a.ArcherID
        LEFT JOIN AppUser u2 ON l.ReviewedBy = u2.UserID
        WHERE 1=1
        """
        
        params = []
        
        # Add filters if provided
        if start_date:
            query += " AND l.EventTime >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND l.EventTime <= %s"
            params.append(end_date)
            
        if user_id:
            query += " AND l.UserID = %s"
            params.append(user_id)
            
        if event_type:
            query += " AND l.EventType = %s"
            params.append(event_type)
            
        if severity:
            query += " AND l.Severity = %s"
            params.append(severity)
            
        if is_reviewed is not None:
            query += " AND l.IsReviewed = %s"
            params.append(is_reviewed)
        
        # Add ordering and limits
        query += " ORDER BY l.EventTime DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return logs
        
    except Exception as e:
        print(f"Error fetching security logs: {e}")
        return []

# Mark a log entry as reviewed
def mark_log_as_reviewed(log_id, reviewed_by):
    """
    Mark a security log entry as reviewed.
    
    Args:
        log_id (int): ID of the log entry
        reviewed_by (int): UserID of the reviewer
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        UPDATE SecurityLog
        SET IsReviewed = TRUE, ReviewedBy = %s, ReviewedAt = NOW()
        WHERE LogID = %s
        """
        
        cursor.execute(query, (reviewed_by, log_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error marking log as reviewed: {e}")
        return False

# Mark multiple log entries as reviewed
def mark_multiple_logs_as_reviewed(log_ids, reviewed_by):
    """
    Mark multiple security log entries as reviewed.
    
    Args:
        log_ids (list): List of log IDs to mark as reviewed
        reviewed_by (int): UserID of the reviewer
        
    Returns:
        tuple: (success_count, failed_count)
    """
    if not log_ids:
        return 0, 0
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Convert list to comma-separated string for SQL IN clause
        log_ids_str = ','.join(map(str, log_ids))
        
        query = f"""
        UPDATE SecurityLog
        SET IsReviewed = TRUE, ReviewedBy = %s, ReviewedAt = NOW()
        WHERE LogID IN ({log_ids_str})
        """
        
        cursor.execute(query, (reviewed_by,))
        affected_rows = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return affected_rows, len(log_ids) - affected_rows
        
    except Exception as e:
        print(f"Error marking multiple logs as reviewed: {e}")
        return 0, len(log_ids)

# Get summary of security events (for dashboard)
def get_security_summary(days=7):
    """
    Get a summary of security events for the dashboard.
    
    Args:
        days (int): Number of days to include in the summary
        
    Returns:
        dict: Summary statistics
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get count by severity
        query_severity = """
        SELECT Severity, COUNT(*) as Count
        FROM SecurityLog
        WHERE EventTime >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY Severity
        """
        
        cursor.execute(query_severity, (days,))
        severity_counts = cursor.fetchall()
        
        # Get count by event type
        query_event_type = """
        SELECT EventType, COUNT(*) as Count
        FROM SecurityLog
        WHERE EventTime >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY EventType
        """
        
        cursor.execute(query_event_type, (days,))
        event_type_counts = cursor.fetchall()
        
        # Get total count
        query_total = """
        SELECT COUNT(*) as Total
        FROM SecurityLog
        WHERE EventTime >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        
        cursor.execute(query_total, (days,))
        total_count = cursor.fetchone()["Total"]
        
        # Get unreviewed count
        query_unreviewed = """
        SELECT COUNT(*) as Unreviewed
        FROM SecurityLog
        WHERE IsReviewed = FALSE
        AND EventTime >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        
        cursor.execute(query_unreviewed, (days,))
        unreviewed_count = cursor.fetchone()["Unreviewed"]
        
        cursor.close()
        conn.close()
        
        return {
            "total": total_count,
            "unreviewed": unreviewed_count,
            "by_severity": severity_counts,
            "by_event_type": event_type_counts
        }
        
    except Exception as e:
        print(f"Error getting security summary: {e}")
        return {
            "total": 0,
            "unreviewed": 0,
            "by_severity": [],
            "by_event_type": []
        }