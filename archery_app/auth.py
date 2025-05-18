import streamlit as st
import hashlib
from archery_app.database import get_connection

def initialize_auth_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "archer_id" not in st.session_state:
        st.session_state.archer_id = None
    if "archer_name" not in st.session_state:
        st.session_state.archer_name = None
    if "is_recorder" not in st.session_state:
        st.session_state.is_recorder = False
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

def login_user(username, password):
    try:
        # Hash the provided password directly
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user information
        query = """
        SELECT u.UserID, u.ArcherID, u.IsRecorder, u.IsAdmin, 
               CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName
        FROM AppUser u
        JOIN Archer a ON u.ArcherID = a.ArcherID
        WHERE u.Username = %s AND u.PasswordHash = %s
        """
        cursor.execute(query, (username, password_hash))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            # Set session state variables
            st.session_state.logged_in = True
            st.session_state.user_id = user["UserID"]
            st.session_state.archer_id = user["ArcherID"]
            st.session_state.archer_name = user["ArcherName"]
            st.session_state.is_recorder = user["IsRecorder"]
            st.session_state.is_admin = user["IsAdmin"]
            return True, "Login successful"
        else:
            # Try with the default pattern as fallback
            default_pattern = f"aAa{username}$%"
            default_hash = hashlib.sha256(default_pattern.encode()).hexdigest()
            
            if default_hash != password_hash:  # Only query again if hashes are different
                # Try again with the default pattern
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (username, default_hash))
                user = cursor.fetchone()
                cursor.close()
                
                if user:
                    # Set session state variables
                    st.session_state.logged_in = True
                    st.session_state.user_id = user["UserID"]
                    st.session_state.archer_id = user["ArcherID"]
                    st.session_state.archer_name = user["ArcherName"]
                    st.session_state.is_recorder = user["IsRecorder"]
                    st.session_state.is_admin = user["IsAdmin"]
                    return True, "Login successful"
            
            return False, "Invalid credentials. Please try again."
            
    except Exception as err:
        return False, f"Database error: {err}"

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.archer_id = None
    st.session_state.archer_name = None
    st.session_state.is_recorder = False
    st.session_state.is_admin = False

def login_page():
    st.title("Archery Club Database - Login")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("## Login")
        st.write("Please enter your credentials to access the system.")
        st.info("Username: Your Archer ID.\nPassword: aAa + Your Archer ID + $%")
        
        username = st.text_input("Username (Archer ID)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                success, message = login_user(username, password)
                if success:
                    st.success(message)
                    st.experimental_rerun()  # Refresh the page to show main app
                else:
                    st.error(message)
    
    with col2:
        st.write("## Welcome to the Archery Club Database")
        st.write("""
        This application allows archers to:
        - View personal scores
        - Record practice scores
        - View round definitions
        - View competition results
        
        Recorders can also:
        - Approve practice scores
        - Manage competitions
        - Generate competition results
        """)