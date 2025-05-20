import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date
from archery_app.database import get_connection, get_archers, get_rounds, get_equipment_types, get_competitions, get_staged_scores, get_recorders
from archery_app.validators import (
    validate_integer, validate_string, validate_date, sanitize_input,
    display_validation_errors, ValidationError
)
from archery_app.security_logging import log_security_event, SecurityEventType
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
        # Validate and sanitize inputs
        errors = []
        
        try:
            # Validate first name - letters only, 2-50 chars
            first_name = validate_string(
                first_name, 
                "First Name", 
                min_length=2, 
                max_length=50,
                pattern=r'^[A-Za-z\s\-]+$',  # Letters, spaces, hyphens
                pattern_description="First name should contain only letters, spaces, and hyphens."
            )
            
            # Apply sanitization
            first_name = sanitize_input(first_name)
            
            # Validate last name - letters only, 2-50 chars
            last_name = validate_string(
                last_name, 
                "Last Name", 
                min_length=2, 
                max_length=50,
                pattern=r'^[A-Za-z\s\-]+$',  # Letters, spaces, hyphens
                pattern_description="Last name should contain only letters, spaces, and hyphens."
            )
            
            # Apply sanitization
            last_name = sanitize_input(last_name)
            
            # Validate date_of_birth
            date_of_birth = validate_date(
                date_of_birth, 
                "Date of Birth", 
                min_date=date(1900, 1, 1), 
                max_date=date.today()
            )
            
            # Validate gender
            if gender not in ["M", "F"]:
                raise ValidationError("Gender must be either 'M' or 'F'.")
                
            # Validate equipment_id
            equipment_id = validate_integer(equipment_id, "Equipment Type", min_value=1)
            
        except ValidationError as e:
            errors.append(str(e))
        
        # Display errors if any and return
        if display_validation_errors(errors):
            return
            
        # If validation passes, proceed with archer creation
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
                # Add logging
                from archery_app.security_logging import log_security_event, SecurityEventType
                log_security_event(
                    event_type=SecurityEventType.ARCHER_CREATE,
                    description=f"New archer created: {first_name} {last_name} (ID: {archer_id})",
                    user_id=st.session_state.user_id
                )
                if archer_class:
                    st.info(f"Archer's Class: {archer_class}")
            else:
                st.warning("Archer was added but couldn't retrieve the ID.")

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")

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
        # Validate inputs
        errors = []
        
        try:
            # Validate staged_score_id
            staged_score_id = validate_integer(staged_score_id, "Score ID", min_value=1)
            
            # Validate recorder_id
            recorder_id = validate_integer(recorder_id, "Recorder ID", min_value=1)
                
        except ValidationError as e:
            errors.append(str(e))
        
        # Display errors if any and return
        if display_validation_errors(errors):
            return
            
        # If validation passes, proceed with approval
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
                # Add logging
                from archery_app.security_logging import log_security_event, SecurityEventType
                log_security_event(
                    event_type=SecurityEventType.SCORE_APPROVE,
                    description=f"Score approved: Staged Score ID {staged_score_id} → Score ID {score_id}",
                    user_id=st.session_state.user_id,
                    archer_id=recorder_id
                )
            else:
                st.error(
                    "Failed to approve score. The selected user does not have recorder privileges."
                )

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")

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
            # Validate and sanitize inputs
            errors = []
            
            try:
                # Validate competition_name
                competition_name = validate_string(
                    competition_name, 
                    "Competition Name", 
                    min_length=3, 
                    max_length=100
                )
                
                # Apply sanitization
                competition_name = sanitize_input(competition_name)
                
                # Validate competition_date
                competition_date = validate_date(
                    competition_date, 
                    "Competition Date", 
                    min_date=date(2000, 1, 1)  # Assuming no competitions before 2000
                )
                
                # Validate description
                if description:
                    description = validate_string(
                        description, 
                        "Description", 
                        max_length=255,
                        allow_none=True
                    )
                    
                    # Apply sanitization
                    description = sanitize_input(description)
                
            except ValidationError as e:
                errors.append(str(e))
            
            # Display errors if any and return
            if display_validation_errors(errors):
                return
                
            # If validation passes, proceed with competition creation
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
                    # Add logging
                    from archery_app.security_logging import log_security_event, SecurityEventType
                    log_security_event(
                        event_type=SecurityEventType.COMPETITION_CREATE,
                        description=f"New competition created: {competition_name} (ID: {competition_id})",
                        user_id=st.session_state.user_id
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
            # Validate inputs
            errors = []
            
            try:
                # Validate competition_id
                competition_id = validate_integer(competition_id, "Competition ID", min_value=1)
                
                # Validate score_id
                score_id = validate_integer(score_id, "Score ID", min_value=1)
                    
            except ValidationError as e:
                errors.append(str(e))
            
            # Display errors if any and return
            if display_validation_errors(errors):
                return
                
            # If validation passes, proceed with linking
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
                # Add logging
                from archery_app.security_logging import log_security_event, SecurityEventType
                log_security_event(
                    event_type=SecurityEventType.COMPETITION_UPDATE,
                    description=f"Score ID {score_id} linked to Competition ID {competition_id}",
                    user_id=st.session_state.user_id
                )
            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")

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
        # Validate input
        errors = []
        
        try:
            # Validate competition_id
            competition_id = validate_integer(competition_id, "Competition ID", min_value=1)
                
        except ValidationError as e:
            errors.append(str(e))
        
        # Display errors if any and return
        if display_validation_errors(errors):
            return
            
        # If validation passes, proceed with generating results
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