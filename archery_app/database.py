import streamlit as st
import mysql.connector
import pandas as pd

# No need to load .env - Streamlit will automatically load secrets.toml


def get_connection():
    return mysql.connector.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"],
    )


def initialize_connection():
    """Initialize database connection and check if VPN connection is working."""
    if "connection_established" not in st.session_state:
        st.session_state.connection_established = False
        st.session_state.connection_error = None

        try:
            conn = get_connection()
            if conn.is_connected():
                st.session_state.connection_established = True
                conn.close()
        except mysql.connector.Error as err:
            # Store the specific error message
            st.session_state.connection_error = str(err)
        except Exception as e:
            st.session_state.connection_error = str(e)


def display_connection_error():
    """Display a formatted error message with VPN information."""
    st.error("⚠️ Database Connection Error")

    st.markdown(
        """
    ### Unable to connect to the Swinburne database
    
    This application requires connection to the Swinburne database which is only accessible when:
    
    1. You are connected to the Swinburne network on campus, or
    2. You are connected via the Swinburne VPN if off-campus
    
    #### Possible reasons for connection failure:
    - You are not connected to the Swinburne VPN
    - VPN connection has timed out
    - Database credentials may be incorrect
    - Database server may be temporarily unavailable
    
    #### To connect to Swinburne VPN:
    
    Please follow the instructions in the [Swinburne VPN Installation Guide](https://www.swinburne.edu.au/content/dam/media/docs/Swinburne_VPN_Installation_Guide_Personal_Devices.pdf)
    """
    )

    if st.session_state.connection_error:
        with st.expander("Technical error details"):
            st.code(st.session_state.connection_error)

    if st.button("Retry Connection"):
        st.session_state.pop("connection_established", None)
        st.session_state.pop("connection_error", None)
        initialize_connection()
        st.rerun()


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


def verify_connection():
    """Verify database connection is active and reconnect if needed.

    Returns:
        bool: True if connection successful, False otherwise
    """
    # If we've already established connection before
    if st.session_state.get("connection_established", False):
        try:
            # Try to quickly check connection is still active
            conn = get_connection()
            conn.ping(reconnect=True)
            conn.close()
            return True
        except Exception:
            # Connection failed, clear state and try initializing again
            st.session_state.connection_established = False
            st.session_state.connection_error = "Connection lost. Reconnecting..."
            initialize_connection()

    # Return current connection state
    return st.session_state.get("connection_established", False)


def get_archer_data_for_competition(competition_id):
    """Fetches archer data, their scores, and potentially other stats for a given competition."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # This is a starting point. We'll need to join with Score, Archer, etc.
    # and potentially calculate average scores or other metrics.
    query = """
        SELECT 
            A.ArcherID, 
            CONCAT(A.FirstName, ' ', A.LastName) AS ArcherName,
            S.TotalScore, 
            S.Date AS ScoreDate,
            R.RoundName,
            ET.Name AS EquipmentType
        FROM CompetitionScore CS
        JOIN Score S ON CS.ScoreID = S.ScoreID
        JOIN Archer A ON S.ArcherID = A.ArcherID
        JOIN Round R ON S.RoundID = R.RoundID
        JOIN EquipmentType ET ON S.EquipmentTypeID = ET.EquipmentTypeID
        WHERE CS.CompetitionID = %s
        ORDER BY S.TotalScore DESC, ArcherName ASC;
    """
    cursor.execute(query, (competition_id,))
    archer_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return archer_data


def get_archer_statistics(archer_id):
    """
    Fetches comprehensive statistics for a single archer.
    
    Returns dictionary with archer info and statistics including:
    - Basic info (name, gender, age)
    - Average score
    - Highest score
    - Total scores recorded
    - Recent scores (last 5)
    - Equipment type preference
    - Favorite round type
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get basic archer info
    query_info = """
        SELECT 
            ArcherID,
            CONCAT(FirstName, ' ', LastName) AS ArcherName,
            Gender,
            DateOfBirth,
            TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) AS Age,
            IsActive
        FROM Archer
        WHERE ArcherID = %s
    """
    cursor.execute(query_info, (archer_id,))
    archer_info = cursor.fetchone()
    
    if not archer_info:
        cursor.close()
        conn.close()
        return None
    
    # Get score statistics
    query_stats = """
        SELECT 
            COUNT(*) AS TotalScores,
            AVG(TotalScore) AS AverageScore,
            MAX(TotalScore) AS HighestScore,
            MIN(TotalScore) AS LowestScore
        FROM Score
        WHERE ArcherID = %s AND IsApproved = 1
    """
    cursor.execute(query_stats, (archer_id,))
    score_stats = cursor.fetchone()
    
    # Get recent scores (last 5)
    query_recent = """
        SELECT 
            S.TotalScore,
            S.Date,
            R.RoundName,
            R.PossibleScore,
            ET.Name AS EquipmentType
        FROM Score S
        JOIN Round R ON S.RoundID = R.RoundID
        JOIN EquipmentType ET ON S.EquipmentTypeID = ET.EquipmentTypeID
        WHERE S.ArcherID = %s AND S.IsApproved = 1
        ORDER BY S.Date DESC
        LIMIT 5
    """
    cursor.execute(query_recent, (archer_id,))
    recent_scores = cursor.fetchall()
    
    # Get preferred equipment type
    query_equipment = """
        SELECT 
            ET.Name AS EquipmentType,
            COUNT(*) AS UsageCount
        FROM Score S
        JOIN EquipmentType ET ON S.EquipmentTypeID = ET.EquipmentTypeID
        WHERE S.ArcherID = %s AND S.IsApproved = 1
        GROUP BY S.EquipmentTypeID
        ORDER BY UsageCount DESC
        LIMIT 1
    """
    cursor.execute(query_equipment, (archer_id,))
    preferred_equipment = cursor.fetchone()
    
    # Get favorite round
    query_round = """
        SELECT 
            R.RoundName,
            COUNT(*) AS UsageCount
        FROM Score S
        JOIN Round R ON S.RoundID = R.RoundID
        WHERE S.ArcherID = %s AND S.IsApproved = 1
        GROUP BY S.RoundID
        ORDER BY UsageCount DESC
        LIMIT 1
    """
    cursor.execute(query_round, (archer_id,))
    favorite_round = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # Combine all data
    stats = {
        **archer_info,
        "ScoreStats": score_stats,
        "RecentScores": recent_scores,
        "PreferredEquipment": preferred_equipment,
        "FavoriteRound": favorite_round
    }
    
    return stats
