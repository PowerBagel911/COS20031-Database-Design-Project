import streamlit as st
import hashlib
from archery_app.database import get_connection
import secrets  # For generating secure random salts
from archery_app.security_logging import log_security_event, SecurityEventType
from archery_app.validators import sanitize_input, validate_string, ValidationError

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
def generate_salt():
    """Generate a cryptographically secure random salt"""
    return secrets.token_hex(32)  # 64 character hex string (32 bytes)

def hash_password(password, salt):
    """Create a salted hash of the password"""
    return hashlib.sha256((salt + password).encode()).hexdigest()

def login_user(username, password):
    try:
        # Sanitize inputs to prevent SQL injection
        username = sanitize_input(username)
        
        # Validate
        try:
            validate_string(username, "Username", min_length=1, max_length=50)
            validate_string(password, "Password", min_length=1)
        except ValidationError:
            # Log failed login due to validation
            log_security_event(
                event_type=SecurityEventType.AUTH_LOGIN_FAILURE,
                description=f"Login failed for username '{username}' - validation error"
            )
            return False, "Invalid credentials. Please try again."
            
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # First, get the user and their salt
        query = """
        SELECT u.UserID, u.ArcherID, u.Salt, u.PasswordHash, u.HashType, u.IsRecorder, u.IsAdmin, 
               CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName
        FROM AppUser u
        JOIN Archer a ON u.ArcherID = a.ArcherID
        WHERE u.Username = %s
        """
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if not user:
            # Log failed login - user not found
            log_security_event(
                event_type=SecurityEventType.AUTH_LOGIN_FAILURE,
                description=f"Login failed for username '{username}' - user not found"
            )
            return False, "Invalid credentials. Please try again."
        # Determine how to verify the password based on HashType
        is_valid = False
        
        if user['HashType'] == 'salted_sha256' and user['Salt']:
            # Verify using the stored salt
            calculated_hash = hash_password(password, user['Salt'])
            is_valid = (calculated_hash == user['PasswordHash'])
        else:
            # Legacy verification without salt
            legacy_hash = hashlib.sha256(password.encode()).hexdigest()
            is_valid = (legacy_hash == user['PasswordHash'])
            
            # If that fails, try with the default pattern
            if not is_valid:
                default_pattern = f"aAa{username}$%"
                default_hash = hashlib.sha256(default_pattern.encode()).hexdigest()
                is_valid = (default_hash == user['PasswordHash'])
                
                # If valid with default pattern, upgrade to salted hash
                if is_valid:
                    new_salt = generate_salt()
                    new_hash = hash_password(default_pattern, new_salt)
                    
                    # Update the user's password hash and salt
                    update_query = """
                    UPDATE AppUser 
                    SET PasswordHash = %s, Salt = %s, HashType = 'salted_sha256'
                    WHERE UserID = %s
                    """
                    cursor.execute(update_query, (new_hash, new_salt, user['UserID']))
                    conn.commit()

        cursor.close()
        conn.close()

        if is_valid:
            # Log successful login
            log_security_event(
                event_type=SecurityEventType.AUTH_LOGIN_SUCCESS,
                description=f"Successful login for user '{username}'",
                user_id=user["UserID"],
                archer_id=user["ArcherID"]
            )
            # Set session state variables
            st.session_state.logged_in = True
            st.session_state.user_id = user["UserID"]
            st.session_state.archer_id = user["ArcherID"]
            st.session_state.archer_name = user["ArcherName"]
            st.session_state.is_recorder = user["IsRecorder"]
            st.session_state.is_admin = user["IsAdmin"]
            st.session_state.current_page = "Home"
            return True, "Login successful"
        else:
            log_security_event(
                event_type=SecurityEventType.AUTH_LOGIN_FAILURE,
                description=f"Login failed for username '{username}' - invalid password",
                archer_id=user["ArcherID"]
            )
            return False, "Invalid credentials. Please try again."

    except Exception as err:
        return False, f"Database error: {err}"


def logout():
    # Log logout event if user is logged in
    if st.session_state.logged_in and st.session_state.user_id:
        log_security_event(
            event_type=SecurityEventType.AUTH_LOGOUT,
            description=f"User logged out",
            user_id=st.session_state.user_id,
            archer_id=st.session_state.archer_id
        )
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.archer_id = None
    st.session_state.archer_name = None
    st.session_state.is_recorder = False
    st.session_state.is_admin = False


def login_page():
    st.title("🏹 Archery Club Database")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Sign In")
        st.write("Please enter your credentials to access the system.")

        with st.container():
            st.info(
                "**Username:** Your Archer ID  \n**Default Password:** aAa + Your Archer ID + $%"
            )

            # Create a form to enable pressing Enter to submit
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username (Archer ID)")
                password = st.text_input("Password", type="password")

                # Submit button for the form
                submit_button = st.form_submit_button("Login", use_container_width=True)

                # Process login if form is submitted
                if submit_button:
                    if not username or not password:
                        st.error("Please enter both username and password.")
                    else:
                        success, message = login_user(username, password)
                        if success:
                            st.success(message)
                            st.rerun()  # Refresh the page to show main app
                        else:
                            st.error(message)

    with col2:
        st.header("Welcome to the Archery Club")

        with st.container():
            st.subheader("Application Features:")
            st.write(
                """
            This application allows you to:
            * View and record your archery scores
            * Check competition results
            * Access round definitions and rules
            * Manage competitions and archers (for recorders)
            * Administer user accounts (for admins)
            """
            )
