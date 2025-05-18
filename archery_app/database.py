import os
import streamlit as st
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

def initialize_connection():
    if "connection_established" not in st.session_state:
        st.session_state.connection_established = False
        try:
            conn = get_connection()
            if conn.is_connected():
                st.session_state.connection_established = True
                conn.close()
        except:
            pass

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