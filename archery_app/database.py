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
