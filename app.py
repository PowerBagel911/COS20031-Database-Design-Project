import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Set page configuration
st.set_page_config(
    page_title="Archery Club Database",
    page_icon="🏹",
    layout="wide"
)

# API URL - change this to your PHP server address
# API_URL = "http://localhost/archery/api.php"
API_URL = "http://localhost:8000/api.php"

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# Function to make API calls
def api_call(endpoint, method="GET", params=None, data=None):
    url = f"{API_URL}?endpoint={endpoint}"
    if params:
        for key, value in params.items():
            url += f"&{key}={value}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# Login function
def login(username, password):
    response = api_call("login", method="POST", data={"username": username, "password": password})
    if response and "success" in response:
        st.session_state.logged_in = True
        st.session_state.user_data = response["user"]
        return True
    else:
        error_msg = response.get("error", "Login failed") if response else "Connection error"
        st.error(error_msg)
        return False

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.user_data = None

# Main app layout
def main():
    st.title("🏹 Archery Club Database")
    
    # Sidebar with login/logout
    with st.sidebar:
        st.header("Navigation")
        
        if not st.session_state.logged_in:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                login(username, password)
        else:
            st.success(f"Logged in as {st.session_state.user_data['name']}")
            if st.button("Logout"):
                logout()
            
            st.divider()
            
            # Navigation menu
            page = st.radio("Select Page", [
                "Dashboard", 
                "Archers", 
                "Scores", 
                "Competitions",
                "Submit Score"
            ])
        
    # Main content area
    if not st.session_state.logged_in:
        st.info("Please log in to access the system")
        
        # Display some public information
        st.header("About the Archery Club Database")
        st.write("""
        This application manages archery club data including archers, scores, competitions, and equipment.
        Login to access the full functionality of the system.
        """)
        
    else:
        # Show different pages based on selection
        if page == "Dashboard":
            show_dashboard()
        elif page == "Archers":
            show_archers()
        elif page == "Scores":
            show_scores()
        elif page == "Competitions":
            show_competitions()
        elif page == "Submit Score":
            submit_score()

# Dashboard page
def show_dashboard():
    st.header("Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Scores")
        scores = api_call("scores")
        if scores:
            # Get only the 5 most recent scores
            recent_scores = scores[:5] if len(scores) > 5 else scores
            df = pd.DataFrame(recent_scores)
            if not df.empty:
                df = df[['Date', 'ArcherName', 'RoundName', 'TotalScore']]
                st.dataframe(df, hide_index=True)
            else:
                st.info("No scores available")
        else:
            st.error("Failed to load scores")
    
    with col2:
        st.subheader("Upcoming Competitions")
        competitions = api_call("competitions")
        if competitions:
            # Filter for future competitions
            today = datetime.now().strftime('%Y-%m-%d')
            upcoming = [c for c in competitions if c['Date'] >= today]
            upcoming = upcoming[:5] if len(upcoming) > 5 else upcoming
            
            if upcoming:
                df = pd.DataFrame(upcoming)
                df = df[['CompetitionName', 'Date', 'IsChampionship']]
                df['IsChampionship'] = df['IsChampionship'].map({0: 'No', 1: 'Yes'})
                st.dataframe(df, hide_index=True)
            else:
                st.info("No upcoming competitions")
        else:
            st.error("Failed to load competitions")

# Archers page
def show_archers():
    st.header("Archers")
    
    archers = api_call("archers")
    if archers:
        df = pd.DataFrame(archers)
        
        # Add search functionality
        search = st.text_input("Search by name")
        if search:
            df = df[df['FirstName'].str.contains(search, case=False) | 
                    df['LastName'].str.contains(search, case=False)]
        
        # Display active/inactive filter
        status = st.radio("Status", ["All", "Active", "Inactive"], horizontal=True)
        if status == "Active":
            df = df[df['IsActive'] == 1]
        elif status == "Inactive":
            df = df[df['IsActive'] == 0]
        
        # Format the data for display
        if not df.empty:
            display_df = df.copy()
            display_df['Name'] = display_df['FirstName'] + ' ' + display_df['LastName']
            display_df['IsActive'] = display_df['IsActive'].map({0: 'No', 1: 'Yes'})
            display_df = display_df[['ArcherID', 'Name', 'DateOfBirth', 'Gender', 'IsActive']]
            st.dataframe(display_df, hide_index=True)
        else:
            st.info("No archers found matching your criteria")
    else:
        st.error("Failed to load archers")

# Scores page
def show_scores():
    st.header("Scores")
    
    # Get all scores
    scores = api_call("scores")
    if scores:
        df = pd.DataFrame(scores)
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("Search by archer name")
        with col2:
            approved = st.radio("Approval Status", ["All", "Approved", "Pending"], horizontal=True)
        
        # Apply filters
        if search:
            df = df[df['ArcherName'].str.contains(search, case=False)]
        
        if approved == "Approved":
            df = df[df['IsApproved'] == 1]
        elif approved == "Pending":
            df = df[df['IsApproved'] == 0]
        
        # Format the data for display
        if not df.empty:
            display_df = df.copy()
            display_df['IsApproved'] = display_df['IsApproved'].map({0: 'Pending', 1: 'Approved'})
            display_df['IsCompetition'] = display_df['IsCompetition'].map({0: 'No', 1: 'Yes'})
            display_df = display_df[['Date', 'ArcherName', 'RoundName', 'EquipmentType', 'TotalScore', 'IsApproved', 'IsCompetition']]
            st.dataframe(display_df, hide_index=True)
        else:
            st.info("No scores found matching your criteria")
    else:
        st.error("Failed to load scores")

# Competitions page
def show_competitions():
    st.header("Competitions")
    
    competitions = api_call("competitions")
    if competitions:
        df = pd.DataFrame(competitions)
        
        # Add search functionality
        search = st.text_input("Search by competition name")
        if search:
            df = df[df['CompetitionName'].str.contains(search, case=False)]
        
        # Format the data for display
        if not df.empty:
            display_df = df.copy()
            display_df['IsChampionship'] = display_df['IsChampionship'].map({0: 'No', 1: 'Yes'})
            display_df = display_df[['CompetitionID', 'CompetitionName', 'Date', 'IsChampionship', 'Description']]
            st.dataframe(display_df, hide_index=True)
        else:
            st.info("No competitions found matching your criteria")
    else:
        st.error("Failed to load competitions")

# Submit Score page
def submit_score():
    st.header("Submit New Score")
    
    # Get the necessary data for dropdowns
    archers = api_call("archers")
    rounds = api_call("rounds")
    equipment_types = api_call("equipment_types")
    
    if not all([archers, rounds, equipment_types]):
        st.error("Failed to load required data")
        return
    
    # Create dropdown options
    archer_options = {f"{a['FirstName']} {a['LastName']}": a['ArcherID'] for a in archers}
    round_options = {r['RoundName']: r['RoundID'] for r in rounds}
    equipment_options = {e['Name']: e['EquipmentTypeID'] for e in equipment_types}
    
    # Form for submitting a score
    with st.form("score_form"):
        st.subheader("Score Details")
        
        # If user is admin or recorder, they can select any archer
        if st.session_state.user_data.get('isAdmin') or st.session_state.user_data.get('isRecorder'):
            archer_name = st.selectbox("Archer", list(archer_options.keys()))
            archer_id = archer_options[archer_name]
        else:
            # Regular users can only submit their own scores
            archer_id = st.session_state.user_data['archerId']
            # Find the archer's name
            archer_name = next((f"{a['FirstName']} {a['LastName']}" for a in archers 
                               if a['ArcherID'] == archer_id), "Unknown")
            st.info(f"Submitting score for: {archer_name}")
        
        round_name = st.selectbox("Round", list(round_options.keys()))
        equipment_name = st.selectbox("Equipment Type", list(equipment_options.keys()))
        
        # Find the selected round's possible score
        selected_round = next((r for r in rounds if r['RoundID'] == round_options[round_name]), None)
        max_possible = selected_round['PossibleScore'] if selected_round else 0
        
        score = st.number_input("Total Score", min_value=0, max_value=max_possible, 
                               help=f"Maximum possible score for this round: {max_possible}")
        
        submitted = st.form_submit_button("Submit Score")
        
        if submitted:
            # Prepare data for API
            data = {
                "archerId": archer_id,
                "roundId": round_options[round_name],
                "equipmentTypeId": equipment_options[equipment_name],
                "totalScore": score
            }
            
            # Call the API to submit the score
            response = api_call("scores", method="POST", data=data)
            
            if response and "success" in response:
                st.success("Score submitted successfully!")
                st.info("Your score has been submitted for approval.")
            else:
                error_msg = response.get("error", "Submission failed") if response else "Connection error"
                st.error(f"Error: {error_msg}")

# Run the app
if __name__ == "__main__":
    main()
