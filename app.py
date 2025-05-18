import streamlit as st
from datetime import datetime, date

# Import modules from the archery_app package
from archery_app.database import initialize_connection
from archery_app.auth import initialize_auth_state, login_page, logout
from archery_app.archer_pages import (
    view_personal_scores, 
    record_practice_score, 
    view_round_definitions,
    view_competition_results
)
from archery_app.recorder_pages import (
    manage_archers,
    approve_practice_scores,
    manage_competitions,
    generate_competition_results
)
from archery_app.admin_pages import (
    manage_users,
    manage_permissions
)

# Initialize connection and auth state
initialize_connection()
initialize_auth_state()

# Main page to choose procedure
def main_page():
    # Display user information
    st.sidebar.write(f"**Logged in as:** {st.session_state.archer_name}")
    if st.session_state.is_recorder:
        st.sidebar.write("**Role:** Recorder")
    elif st.session_state.is_admin:
        st.sidebar.write("**Role:** Administrator")
    else:
        st.sidebar.write("**Role:** Archer")
    
    if st.sidebar.button("Logout"):
        logout()
        st.experimental_rerun()  # Refresh to show login page
    
    st.sidebar.title("Menu")
    
    # Always available options
    options = [
        "View Personal Scores",
        "Record Practice Score",
        "View Round Definitions",
        "View Competition Results",
    ]
    
    # Recorder/Admin options
    if st.session_state.is_recorder or st.session_state.is_admin:
        options.extend([
            "Manage Archers",
            "Approve Practice Scores",
            "Manage Competitions",
            "Generate Competition Results",
        ])
    # Admin-only options - only the ones we need
    if st.session_state.is_admin:
        options.extend([
            "User Management",
            "Permission Management"
        ])
    
    procedure = st.sidebar.selectbox("Select Procedure", options)

    if procedure == "View Personal Scores":
        view_personal_scores()
    elif procedure == "Record Practice Score":
        record_practice_score()
    elif procedure == "View Round Definitions":
        view_round_definitions()
    elif procedure == "View Competition Results":
        view_competition_results()
    elif procedure == "Manage Archers" and (st.session_state.is_recorder or st.session_state.is_admin):
        manage_archers()
    elif procedure == "Approve Practice Scores" and (st.session_state.is_recorder or st.session_state.is_admin):
        approve_practice_scores()
    elif procedure == "Manage Competitions" and (st.session_state.is_recorder or st.session_state.is_admin):
        manage_competitions()
    elif procedure == "Generate Competition Results" and (st.session_state.is_recorder or st.session_state.is_admin):
        generate_competition_results()
    elif procedure == "User Management" and st.session_state.is_admin:
        manage_users()
    elif procedure == "Permission Management" and st.session_state.is_admin:
        manage_permissions()

# Main function
if __name__ == "__main__":
    st.title("Archery Club Database")
    
    if not st.session_state.connection_established:
        st.error("Unable to connect to the database. Please check your connection parameters.")
    else:
        if st.session_state.logged_in:
            main_page()
        else:
            login_page()