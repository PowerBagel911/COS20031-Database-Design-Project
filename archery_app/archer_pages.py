import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date
from archery_app.database import (
    get_connection,
    get_archers,
    get_rounds,
    get_equipment_types,
    get_competitions,
)

from archery_app.validators import (
    validate_integer, validate_date, sanitize_input, 
    display_validation_errors, ValidationError
)

def view_personal_scores():
    st.header("View Personal Scores")

    archers = get_archers()

    # Allow all users to view scores of any archer
    archer_options = {
        f"{a['ArcherID']} - {a['ArcherName']}": a["ArcherID"] for a in archers
    }

    # For normal archers, preselect their own ID but allow changing
    if not st.session_state.is_recorder and not st.session_state.is_admin:
        # Find the option key for the current archer to preselect it
        current_archer_key = next(
            (
                key
                for key in archer_options.keys()
                if str(st.session_state.archer_id) in key.split(" - ")[0]
            ),
            list(archer_options.keys())[0],  # fallback to first option if not found
        )
        st.info("You can view your scores or other archers' scores for comparison.")
        selected_archer = st.selectbox(
            "Select Archer",
            options=list(archer_options.keys()),
            index=list(archer_options.keys()).index(current_archer_key),
        )
    else:
        selected_archer = st.selectbox(
            "Select Archer", options=list(archer_options.keys())
        )

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


from archery_app.validators import (
    validate_integer, validate_date, sanitize_input, 
    display_validation_errors, ValidationError
)

def record_practice_score():
    st.header("Record Practice Score")

    archers = get_archers()

    # Only allow selecting an archer if user is recorder or admin
    if st.session_state.is_recorder or st.session_state.is_admin:
        archer_options = {
            f"{a['ArcherID']} - {a['ArcherName']}": a["ArcherID"] for a in archers
        }
        selected_archer = st.selectbox(
            "Select Archer", options=list(archer_options.keys())
        )
        archer_id = archer_options[selected_archer]
    else:
        # For normal archers, only record their own scores
        archer_id = st.session_state.archer_id
        archer_name = st.session_state.archer_name
        st.info(f"Recording score for: {archer_name}")

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
        # Validate and sanitize inputs
        errors = []
        
        try:
            # Validate archer_id
            archer_id = validate_integer(archer_id, "Archer ID", min_value=1)
            
            # Validate round_id
            round_id = validate_integer(round_id, "Round", min_value=1)
            
            # Validate equipment_id
            equipment_id = validate_integer(equipment_id, "Equipment Type", min_value=1)
            
            # Validate score_date
            score_date = validate_date(score_date, "Score Date", max_date=date.today())
            
            # Validate total_score
            total_score = validate_integer(total_score, "Total Score", min_value=0)
            
        except ValidationError as e:
            errors.append(str(e))
        
        # Display errors if any
        if display_validation_errors(errors):
            return
            
        # All inputs are valid, proceed with submission
        try:
            conn = get_connection()
            cursor = conn.cursor()

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
