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
from archery_app.security_logging import log_security_event, SecurityEventType
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
                # Add logging
                from archery_app.security_logging import log_security_event, SecurityEventType
                log_security_event(
                    event_type=SecurityEventType.SCORE_SUBMIT,
                    description=f"Score submitted for round ID {round_id}: {total_score} points",
                    user_id=st.session_state.user_id,
                    archer_id=archer_id
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

            # Get all result sets from the stored procedure
            results = list(cursor.stored_results())
            
            if results:
                # First result set: Round definition details
                round_details = results[0].fetchall()
                if round_details:
                    st.subheader(f"🎯 Round Definition: {selected_round.split(' - ')[1]}")
                    
                    # Display basic round info from first row
                    first_row = round_details[0]
                    
                    # Create info cards for basic round information
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Arrows", first_row['TotalArrows'])
                    with col2:
                        st.metric("Possible Score", first_row['PossibleScore'])
                    with col3:
                        st.metric("Number of Ranges", len(round_details))
                    
                    # Display description if available
                    if first_row.get('Description'):
                        st.info(f"**Description:** {first_row['Description']}")
                    
                    # Display detailed range information
                    st.subheader("📏 Range Details")
                    
                    # Create a cleaner display for ranges
                    range_data = []
                    for detail in round_details:
                        range_data.append({
                            "Range": detail['RangeSequence'],
                            "Distance (m)": detail['Distance'],
                            "Number of Ends": detail['NumberOfEnds'],
                            "Arrows per End": detail['ArrowsPerEnd'],
                            "Total Arrows": detail['NumberOfEnds'] * detail['ArrowsPerEnd'],
                            "Target Face": f"{detail['TargetFaceSize']}cm",
                            "Target Description": detail['TargetFaceDescription']
                        })
                    
                    df_ranges = pd.DataFrame(range_data)
                    st.dataframe(df_ranges, use_container_width=True, hide_index=True)
                    
                    # Second result set: Equivalent rounds (if available)
                    if len(results) > 1:
                        equivalent_rounds = results[1].fetchall()
                        if equivalent_rounds:
                            st.markdown("---")  # Add a separator
                            st.subheader("🔄 Equivalent Rounds")
                            
                            # Group equivalent rounds by type
                            base_rounds = []
                            equivalent_to_rounds = []
                            
                            for equiv in equivalent_rounds:
                                if equiv['EquivalentType'] == 'This round is base for:':
                                    base_rounds.append(equiv)
                                else:
                                    equivalent_to_rounds.append(equiv)
                            
                            # Display base rounds (rounds this round is the base for)
                            if base_rounds:
                                st.write("**This round serves as the base round for:**")
                                base_data = []
                                for base in base_rounds:
                                    base_data.append({
                                        "Class": base['ClassName'],
                                        "Equipment Type": base['EquipmentType'],
                                        "Equivalent Round": base['EquivalentRoundName'],
                                        "Effective Date": base['EffectiveDate'],
                                        "Expiry Date": base['ExpiryDate'] if base['ExpiryDate'] else "No Expiry"
                                    })
                                
                                df_base = pd.DataFrame(base_data)
                                st.dataframe(df_base, use_container_width=True, hide_index=True)
                            
                            # Display equivalent rounds (rounds this round is equivalent to)
                            if equivalent_to_rounds:
                                st.write("**This round is equivalent to:**")
                                equiv_data = []
                                for equiv in equivalent_to_rounds:
                                    equiv_data.append({
                                        "Class": equiv['ClassName'],
                                        "Equipment Type": equiv['EquipmentType'],
                                        "Base Round": equiv['EquivalentRoundName'],
                                        "Effective Date": equiv['EffectiveDate'],
                                        "Expiry Date": equiv['ExpiryDate'] if equiv['ExpiryDate'] else "No Expiry"
                                    })
                                
                                df_equiv = pd.DataFrame(equiv_data)
                                st.dataframe(df_equiv, use_container_width=True, hide_index=True)
                            
                            
                        else:
                            st.info("ℹ️ No equivalent rounds defined for this round.")
                    else:
                        st.info("ℹ️ No equivalent rounds information available.")
                        
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
