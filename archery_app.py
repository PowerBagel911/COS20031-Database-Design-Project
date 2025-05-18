import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date


# Database connection
def get_connection():
    return mysql.connector.connect(
        host="feenix-mariadb.swin.edu.au",
        user="s104844794",
        password="260804",
        database="s104844794_db",
    )


# Initialize session state
if "connection_established" not in st.session_state:
    st.session_state.connection_established = False
    try:
        conn = get_connection()
        if conn.is_connected():
            st.session_state.connection_established = True
            conn.close()
    except:
        pass

# Page title
st.title("Archery Club Database")


# Main page to choose procedure
def main_page():
    st.sidebar.title("Menu")
    procedure = st.sidebar.selectbox(
        "Select Procedure",
        [
            "View Personal Scores",
            "Record Practice Score",
            "View Round Definitions",
            "View Competition Results",
            "Manage Archers",
            "Approve Practice Scores",
            "Manage Competitions",
            "Generate Competition Results",
        ],
    )

    if procedure == "View Personal Scores":
        view_personal_scores()
    elif procedure == "Record Practice Score":
        record_practice_score()
    elif procedure == "View Round Definitions":
        view_round_definitions()
    elif procedure == "View Competition Results":
        view_competition_results()
    elif procedure == "Manage Archers":
        manage_archers()
    elif procedure == "Approve Practice Scores":
        approve_practice_scores()
    elif procedure == "Manage Competitions":
        manage_competitions()
    elif procedure == "Generate Competition Results":
        generate_competition_results()


# Helper functions to get data for dropdowns
def get_archers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT ArcherID, CONCAT(FirstName, ' ', LastName) as ArcherName FROM Archer ORDER BY ArcherID"
    )
    archers = cursor.fetchall()
    cursor.close()
    conn.close()
    return archers


def get_rounds():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT RoundID, RoundName FROM Round ORDER BY RoundID")
    rounds = cursor.fetchall()
    cursor.close()
    conn.close()
    return rounds


def get_equipment_types():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT EquipmentTypeID, Name FROM EquipmentType ORDER BY EquipmentTypeID"
    )
    equipment_types = cursor.fetchall()
    cursor.close()
    conn.close()
    return equipment_types


def get_competitions():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT CompetitionID, CompetitionName FROM Competition ORDER BY CompetitionID"
    )
    competitions = cursor.fetchall()
    cursor.close()
    conn.close()
    return competitions


def get_staged_scores():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT ss.StagedScoreID, 
               CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName, 
               r.RoundName, 
               et.Name AS EquipmentType, 
               ss.Date, 
               ss.TotalScore 
        FROM StagedScore ss
        JOIN Archer a ON ss.ArcherID = a.ArcherID
        JOIN Round r ON ss.RoundID = r.RoundID
        JOIN EquipmentType et ON ss.EquipmentTypeID = et.EquipmentTypeID
        ORDER BY ss.StagedScoreID
    """
    )
    staged_scores = cursor.fetchall()
    cursor.close()
    conn.close()
    return staged_scores


# New function to get recorders only
def get_recorders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.ArcherID, CONCAT(a.FirstName, ' ', a.LastName) as ArcherName 
        FROM Archer a
        JOIN AppUser u ON a.ArcherID = u.ArcherID
        WHERE u.IsRecorder = 1
        ORDER BY a.ArcherID
        """
    )
    recorders = cursor.fetchall()
    cursor.close()
    conn.close()
    return recorders


# 1. View Personal Scores
def view_personal_scores():
    st.header("View Personal Scores")

    archers = get_archers()
    archer_options = {
        f"{a['ArcherID']} - {a['ArcherName']}": a["ArcherID"] for a in archers
    }

    selected_archer = st.selectbox("Select Archer", options=list(archer_options.keys()))
    archer_id = archer_options[selected_archer]

    rounds = get_rounds()
    round_options = {"All Rounds": None}
    round_options.update(
        {f"{r['RoundID']} - {r['RoundName']}": r["RoundID"] for r in rounds}
    )

    selected_round = st.selectbox(
        "Filter by Round (Optional)", options=list(round_options.keys())
    )
    round_id = round_options[selected_round]

    start_date = st.date_input("Start Date (Optional)", value=None)
    end_date = st.date_input("End Date (Optional)", value=None)

    if st.button("View Scores"):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Call the stored procedure
            cursor.callproc(
                "uspGetArcherScores", [archer_id, start_date, end_date, round_id]
            )

            # Fixed: Use proper syntax to iterate through results
            results = list(cursor.stored_results())
            if results:
                scores = results[0].fetchall()
                if scores:
                    st.subheader(f"Scores for {selected_archer.split(' - ')[1]}")
                    df = pd.DataFrame(scores)
                    st.dataframe(df)
                else:
                    st.info("No scores found for the selected criteria.")
            else:
                st.info("No results returned from the procedure.")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# 2. Record Practice Score
def record_practice_score():
    st.header("Record Practice Score")

    archers = get_archers()
    archer_options = {
        f"{a['ArcherID']} - {a['ArcherName']}": a["ArcherID"] for a in archers
    }

    selected_archer = st.selectbox("Select Archer", options=list(archer_options.keys()))
    archer_id = archer_options[selected_archer]

    rounds = get_rounds()
    round_options = {f"{r['RoundID']} - {r['RoundName']}": r["RoundID"] for r in rounds}

    selected_round = st.selectbox("Select Round", options=list(round_options.keys()))
    round_id = round_options[selected_round]

    equipment_types = get_equipment_types()
    equipment_options = {
        f"{e['EquipmentTypeID']} - {e['Name']}": e["EquipmentTypeID"]
        for e in equipment_types
    }

    selected_equipment = st.selectbox(
        "Select Equipment Type", options=list(equipment_options.keys())
    )
    equipment_id = equipment_options[selected_equipment]

    score_date = st.date_input("Score Date", value=date.today())
    total_score = st.number_input("Total Score", min_value=0, step=1)

    if st.button("Submit Score"):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Initialize the output parameter
            output_params = cursor._connection.cursor()

            # Call the stored procedure
            cursor.callproc(
                "uspAddStagedScore",
                [archer_id, round_id, equipment_id, score_date, total_score, 0],
            )

            # Execute the stored procedure
            conn.commit()

            # Direct query to get the last inserted ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            staged_score_id = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            if staged_score_id:
                st.success(
                    f"Score submitted successfully! Staged Score ID: {staged_score_id}"
                )
            else:
                st.warning("Score was submitted but couldn't retrieve the ID.")

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# 3. View Round Definitions
def view_round_definitions():
    st.header("View Round Definitions")

    rounds = get_rounds()
    round_options = {f"{r['RoundID']} - {r['RoundName']}": r["RoundID"] for r in rounds}

    selected_round = st.selectbox("Select Round", options=list(round_options.keys()))
    round_id = round_options[selected_round]

    if st.button("View Round Details"):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Call the stored procedure
            cursor.callproc("uspGetRoundDetails", [round_id])

            # Fixed: Use proper syntax to iterate through results
            results = list(cursor.stored_results())
            if results:
                details = results[0].fetchall()
                if details:
                    st.subheader(f"Details for {selected_round.split(' - ')[1]}")
                    df = pd.DataFrame(details)
                    st.dataframe(df)
                else:
                    st.info("No details found for the selected round.")
            else:
                st.info("No results returned from the procedure.")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# 4. View Competition Results
def view_competition_results():
    st.header("View Competition Results")

    competitions = get_competitions()
    competition_options = {
        f"{c['CompetitionID']} - {c['CompetitionName']}": c["CompetitionID"]
        for c in competitions
    }

    if not competition_options:
        st.info("No competitions found in the database.")
        return

    selected_competition = st.selectbox(
        "Select Competition", options=list(competition_options.keys())
    )
    competition_id = competition_options[selected_competition]

    if st.button("View Results"):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Call the stored procedure
            cursor.callproc("uspGetCompetitionResults", [competition_id])

            # Fixed: Use proper syntax to iterate through results
            results = list(cursor.stored_results())
            if results:
                competition_results = results[0].fetchall()
                if competition_results:
                    st.subheader(f"Results for {selected_competition.split(' - ')[1]}")
                    df = pd.DataFrame(competition_results)
                    st.dataframe(df)
                else:
                    st.info("No results found for the selected competition.")
            else:
                st.info("No results returned from the procedure.")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# 5. Manage Archers (Add Archer)
def manage_archers():
    st.header("Add New Archer")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    date_of_birth = st.date_input(
        "Date of Birth", min_value=date(1900, 1, 1), max_value=date.today()
    )
    gender = st.selectbox("Gender", ["M", "F"])

    equipment_types = get_equipment_types()
    equipment_options = {
        f"{e['EquipmentTypeID']} - {e['Name']}": e["EquipmentTypeID"]
        for e in equipment_types
    }

    selected_equipment = st.selectbox(
        "Default Equipment Type", options=list(equipment_options.keys())
    )
    equipment_id = equipment_options[selected_equipment]

    if st.button("Add Archer"):
        if not first_name or not last_name:
            st.warning("Please fill in all required fields.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Call the stored procedure
            cursor.callproc(
                "uspAddArcher",
                [first_name, last_name, date_of_birth, gender, equipment_id, 0],
            )

            # Execute the stored procedure
            conn.commit()

            # Direct query to get the last inserted ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            archer_id = cursor.fetchone()[0]

            # Get archer class info separately
            archer_class = None
            results = list(cursor.stored_results())
            if results:
                archer_class = results[0].fetchone()

            cursor.close()
            conn.close()

            if archer_id:
                st.success(f"Archer added successfully! Archer ID: {archer_id}")
                if archer_class:
                    st.info(f"Archer's Class: {archer_class}")
            else:
                st.warning("Archer was added but couldn't retrieve the ID.")

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# 6. Approve Practice Scores
def approve_practice_scores():
    st.header("Approve Practice Scores")

    staged_scores = get_staged_scores()
    if not staged_scores:
        st.info("No staged scores waiting for approval.")
        return

    score_options = {
        f"{s['StagedScoreID']} - {s['ArcherName']} - {s['RoundName']} - {s['Date']} - Score: {s['TotalScore']}": s[
            "StagedScoreID"
        ]
        for s in staged_scores
    }

    selected_score = st.selectbox(
        "Select Score to Approve", options=list(score_options.keys())
    )
    staged_score_id = score_options[selected_score]

    # Changed from get_archers() to get_recorders() to only show valid recorders
    recorders = get_recorders()

    if not recorders:
        st.warning(
            "No recorders found in the database. Only users with recorder permissions can approve scores."
        )
        return

    recorder_options = {
        f"{r['ArcherID']} - {r['ArcherName']}": r["ArcherID"] for r in recorders
    }

    selected_recorder = st.selectbox(
        "Approving Recorder", options=list(recorder_options.keys())
    )
    recorder_id = recorder_options[selected_recorder]

    if st.button("Approve Score"):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Using an output parameter for the procedure
            args = [staged_score_id, recorder_id, 0]
            result_args = cursor.callproc("uspApproveScore", args)

            # Execute the stored procedure
            conn.commit()

            # Get the output parameter (ScoreID)
            score_id = result_args[2]  # This is the OUT parameter from the procedure

            cursor.close()
            conn.close()

            if score_id > 0:
                st.success(f"Score approved successfully! Score ID: {score_id}")
            else:
                st.error(
                    "Failed to approve score. The selected user does not have recorder privileges."
                )

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# 7. Manage Competitions
def manage_competitions():
    st.header("Manage Competitions")

    tab1, tab2 = st.tabs(["Create Competition", "Link Score to Competition"])

    with tab1:
        st.subheader("Create New Competition")
        competition_name = st.text_input("Competition Name")
        competition_date = st.date_input("Competition Date", value=date.today())
        is_championship = st.checkbox("Is Championship")
        description = st.text_area("Description")

        if st.button("Create Competition"):
            if not competition_name:
                st.warning("Please enter a competition name.")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Call the stored procedure
                cursor.callproc(
                    "uspCreateCompetition",
                    [
                        competition_name,
                        competition_date,
                        is_championship,
                        description,
                        0,
                    ],
                )

                # Execute the stored procedure
                conn.commit()

                # Direct query to get the last inserted ID
                cursor.execute("SELECT LAST_INSERT_ID()")
                competition_id = cursor.fetchone()[0]

                cursor.close()
                conn.close()

                if competition_id:
                    st.success(
                        f"Competition created successfully! Competition ID: {competition_id}"
                    )
                else:
                    st.warning("Competition was created but couldn't retrieve the ID.")

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")

    with tab2:
        st.subheader("Link Score to Competition")

        competitions = get_competitions()
        competition_options = {
            f"{c['CompetitionID']} - {c['CompetitionName']}": c["CompetitionID"]
            for c in competitions
        }

        if not competition_options:
            st.info("No competitions found in the database.")
            return

        selected_competition = st.selectbox(
            "Select Competition",
            options=list(competition_options.keys()),
            key="link_comp",
        )
        competition_id = competition_options[selected_competition]

        # Get approved scores that are not yet competition scores
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT s.ScoreID, 
                   CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName, 
                   r.RoundName, 
                   et.Name AS EquipmentType, 
                   s.Date, 
                   s.TotalScore 
            FROM Score s
            JOIN Archer a ON s.ArcherID = a.ArcherID
            JOIN Round r ON s.RoundID = r.RoundID
            JOIN EquipmentType et ON s.EquipmentTypeID = et.EquipmentTypeID
            WHERE s.IsApproved = 1 AND s.IsCompetition = 0
            ORDER BY s.ScoreID
        """
        )
        scores = cursor.fetchall()
        cursor.close()
        conn.close()

        if not scores:
            st.info("No approved non-competition scores available.")
            return

        score_options = {
            f"{s['ScoreID']} - {s['ArcherName']} - {s['RoundName']} - {s['Date']} - Score: {s['TotalScore']}": s[
                "ScoreID"
            ]
            for s in scores
        }

        selected_score = st.selectbox(
            "Select Score to Link", options=list(score_options.keys())
        )
        score_id = score_options[selected_score]

        if st.button("Link Score"):
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Call the stored procedure
                cursor.callproc("uspLinkScoreToCompetition", [competition_id, score_id])

                # Execute the stored procedure
                conn.commit()

                cursor.close()
                conn.close()

                st.success(f"Score linked to competition successfully!")

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")


# 8. Generate Competition Results
def generate_competition_results():
    st.header("Generate Competition Results")

    competitions = get_competitions()
    competition_options = {
        f"{c['CompetitionID']} - {c['CompetitionName']}": c["CompetitionID"]
        for c in competitions
    }

    if not competition_options:
        st.info("No competitions found in the database.")
        return

    selected_competition = st.selectbox(
        "Select Competition", options=list(competition_options.keys())
    )
    competition_id = competition_options[selected_competition]

    if st.button("Generate Results"):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Call the stored procedure
            cursor.callproc("uspGenerateCompetitionResults", [competition_id])

            # Fixed: Use proper syntax to iterate through results
            results = list(cursor.stored_results())
            if results:
                competition_results = results[0].fetchall()
                if competition_results:
                    st.subheader(f"Results for {selected_competition.split(' - ')[1]}")

                    # Group by category
                    categories = {}
                    for row in competition_results:
                        category = row["Category"]
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(row)

                    # Display results by category
                    for category, rows in categories.items():
                        st.subheader(f"Category: {category}")
                        df = pd.DataFrame(rows)
                        st.dataframe(df)
                else:
                    st.info("No results found for the selected competition.")
            else:
                st.info("No results returned from the procedure.")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")


# Main function
if __name__ == "__main__":
    if st.session_state.connection_established:
        main_page()
    else:
        st.error(
            "Unable to connect to the database. Please check your connection parameters."
        )
