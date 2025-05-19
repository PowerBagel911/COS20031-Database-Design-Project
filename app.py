import streamlit as st
from datetime import datetime, date
from archery_app.security_admin import security_logs_admin
# Import modules from the archery_app package
from archery_app.database import (
    initialize_connection,
    display_connection_error,
    verify_connection,
)
from archery_app.auth import initialize_auth_state, login_page, logout
from archery_app.archer_pages import (
    view_personal_scores,
    record_practice_score,
    view_round_definitions,
    view_competition_results,
)
from archery_app.recorder_pages import (
    manage_archers,
    approve_practice_scores,
    manage_competitions,
    generate_competition_results,
)
from archery_app.admin_pages import manage_users, manage_permissions, manage_account
from archery_app.chatbot import sql_chatbot

# Set page configuration
st.set_page_config(
    page_title="Archery Club Database",
    page_icon="🏹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize connection and auth state
initialize_connection()
initialize_auth_state()


# Dashboard home page
def home_dashboard():
    st.header("Dashboard")

    # Welcome message with current date
    current_date = date.today().strftime("%B %d, %Y")
    st.subheader(f"Welcome, {st.session_state.archer_name}")
    st.write(f"Today is **{current_date}**")

    # Create a 2-column layout for quick access buttons
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("My Archery")
        if st.button("📊 View Scores", use_container_width=True):
            st.session_state.current_page = "View Personal Scores"
            st.rerun()
        if st.button("📝 Record New Score", use_container_width=True):
            st.session_state.current_page = "Record Practice Score"
            st.rerun()

    with col2:
        st.subheader("Club Information")
        if st.button("🏆 Competition Results", use_container_width=True):
            st.session_state.current_page = "View Competition Results"
            st.rerun()
        if st.button("ℹ️ Round Definitions", use_container_width=True):
            st.session_state.current_page = "View Round Definitions"
            st.rerun()
        if st.session_state.is_admin and st.button(
            "🤖 SQL Assistant", use_container_width=True
        ):
            st.session_state.current_page = "SQL Assistant"
            st.rerun()

    # For recorders and admins, show recorder section
    if st.session_state.is_recorder or st.session_state.is_admin:
        st.markdown("---")
        st.subheader("Club Management")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Approve Scores", use_container_width=True):
                st.session_state.current_page = "Approve Practice Scores"
                st.rerun()
            if st.button("👥 Manage Archers", use_container_width=True):
                st.session_state.current_page = "Manage Archers"
                st.rerun()

        with col2:
            if st.button("🏅 Manage Competitions", use_container_width=True):
                st.session_state.current_page = "Manage Competitions"
                st.rerun()
            if st.button("📋 Generate Results", use_container_width=True):
                st.session_state.current_page = "Generate Competition Results"
                st.rerun()

    # Find the admin-only section in the sidebar and add Security Logs
    # if st.session_state.is_admin:
    #     st.sidebar.subheader("Administration")

    #     admin_options = [
    #         ("👤 User Management", "User Management"),
    #         ("🔐 Permissions", "Permission Management"),
    #         ("🔒 Security Logs", "Security Logs"),  # Add this line
    #     ]

    #     for label, page in admin_options:
    #         if st.sidebar.button(
    #             label, key=f"btn_{page}", use_container_width=True
    #         ):
    #             st.session_state.current_page = page
    #             st.rerun()

    # Add to the display_selected_page part - typically it's in the main_page function
    


# Main page to choose procedure
def main_page():
    # Initialize current_page in session state if not present
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    # Display user information in sidebar
    with st.sidebar:
        st.sidebar.header(f"👤 {st.session_state.archer_name}")

        role = (
            "Administrator"
            if st.session_state.is_admin
            else "Recorder" if st.session_state.is_recorder else "Archer"
        )
        st.sidebar.write(f"**Role:** {role}")

        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()  # Refresh to show login page

        if st.sidebar.button("⚙️ Account Settings", use_container_width=True):
            st.session_state.current_page = "Manage Account"
            st.rerun()

        st.sidebar.title("Menu")

        # Home button at the top
        if st.sidebar.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()

        # Separate menus with headers
        st.sidebar.subheader("Archer Functions")

        # Always available options
        archer_options = [
            ("📊 View Scores", "View Personal Scores"),
            ("📝 Record Score", "Record Practice Score"),
            ("ℹ️ Round Info", "View Round Definitions"),
            ("🏆 Competition Results", "View Competition Results"),
        ]

        # Add SQL Assistant only for admin users
        if st.session_state.is_admin:
            archer_options.append(("🤖 SQL Assistant", "SQL Assistant"))

        for label, page in archer_options:
            if st.sidebar.button(label, key=f"btn_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        # Recorder/Admin options
        if st.session_state.is_recorder or st.session_state.is_admin:
            st.sidebar.subheader("Recorder Functions")

            recorder_options = [
                ("👥 Manage Archers", "Manage Archers"),
                ("✓ Approve Scores", "Approve Practice Scores"),
                ("🏅 Manage Competitions", "Manage Competitions"),
                ("📋 Generate Results", "Generate Competition Results"),
            ]

            for label, page in recorder_options:
                if st.sidebar.button(
                    label, key=f"btn_{page}", use_container_width=True
                ):
                    st.session_state.current_page = page
                    st.rerun()

        # Admin-only options
        if st.session_state.is_admin:
            st.sidebar.subheader("Admin Functions")

            admin_options = [
                ("👤 User Management", "User Management"),
                ("🔐 Permissions", "Permission Management"),
                ("🔒 Security Logs", "Security Logs"),
            ]

            for label, page in admin_options:
                if st.sidebar.button(
                    label, key=f"btn_{page}", use_container_width=True
                ):
                    st.session_state.current_page = page
                    st.rerun()
        
    # Main content title
    st.title("🏹 Archery Club Database")

    # Display selected page content
    if st.session_state.current_page == "Home":
        home_dashboard()
    elif st.session_state.current_page == "View Personal Scores":
        view_personal_scores()
    elif st.session_state.current_page == "Record Practice Score":
        record_practice_score()
    elif st.session_state.current_page == "View Round Definitions":
        view_round_definitions()
    elif st.session_state.current_page == "View Competition Results":
        view_competition_results()
    elif st.session_state.current_page == "SQL Assistant":
        sql_chatbot()
    elif st.session_state.current_page == "Manage Archers" and (
        st.session_state.is_recorder or st.session_state.is_admin
    ):
        manage_archers()
    elif st.session_state.current_page == "Approve Practice Scores" and (
        st.session_state.is_recorder or st.session_state.is_admin
    ):
        approve_practice_scores()
    elif st.session_state.current_page == "Manage Competitions" and (
        st.session_state.is_recorder or st.session_state.is_admin
    ):
        manage_competitions()
    elif st.session_state.current_page == "Generate Competition Results" and (
        st.session_state.is_recorder or st.session_state.is_admin
    ):
        generate_competition_results()
    elif (
        st.session_state.current_page == "User Management" and st.session_state.is_admin
    ):
        manage_users()
    elif (
        st.session_state.current_page == "Permission Management"
        and st.session_state.is_admin
    ):
        manage_permissions()
    elif st.session_state.current_page == "Security Logs" and st.session_state.is_admin:
            security_logs_admin()
    elif st.session_state.current_page == "Manage Account":
        manage_account()
    else:
        st.session_state.current_page = "Home"
        st.rerun()


# Main function
if __name__ == "__main__":
    # Check if we need to initialize the connection
    if "connection_established" not in st.session_state:
        initialize_connection()

    # Verify connection is active
    if not verify_connection():
        display_connection_error()
    else:
        if st.session_state.logged_in:
            main_page()
        else:
            login_page()
