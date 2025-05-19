import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date, datetime
import hashlib
from archery_app.database import get_connection
from archery_app.auth import generate_salt, hash_password

def get_all_users():
    """Retrieve all users from the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("uspGetAllUsers")

        results = list(cursor.stored_results())
        users = results[0].fetchall() if results else []

        cursor.close()
        conn.close()
        return users
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return []


def get_archers_without_accounts():
    """Get archers that don't have user accounts yet"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("uspGetArchersWithoutAccounts")

        results = list(cursor.stored_results())
        archers = results[0].fetchall() if results else []

        cursor.close()
        conn.close()
        return archers
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return []


# 1. User Account Management
def manage_users():
    st.header("User Account Management")

    tab1, tab2, tab3 = st.tabs(["View Users", "Create User", "Manage Account"])

    with tab1:
        # View all user accounts
        st.subheader("All User Accounts")

        users = get_all_users()
        if users:
            # Convert boolean values to Yes/No for better display
            for user in users:
                # Convert boolean values to Yes/No strings, but preserve original values
                if isinstance(user["IsRecorder"], bool):
                    user["Is Recorder"] = "Yes" if user["IsRecorder"] else "No"
                else:
                    user["Is Recorder"] = user["IsRecorder"]

                if isinstance(user["IsAdmin"], bool):
                    user["Is Admin"] = "Yes" if user["IsAdmin"] else "No"
                else:
                    user["Is Admin"] = user["IsAdmin"]

            # Create a dataframe with the updated column names
            display_data = [
                {
                    "User ID": u["UserID"],
                    "Username": u["Username"],
                    "Archer ID": u["ArcherID"],
                    "Archer Name": u["ArcherName"],
                    "Is Recorder": u["Is Recorder"],
                    "Is Admin": u["Is Admin"],
                }
                for u in users
            ]

            df = pd.DataFrame(display_data)
            st.dataframe(df)
        else:
            st.info("No user accounts found.")

    with tab2:
        # Create new user accounts
        st.subheader("Create New User Account")

        archers = get_archers_without_accounts()
        if not archers:
            st.info("All archers already have accounts.")
            return

        archer_options = {
            f"{a['ArcherID']} - {a['FirstName']} {a['LastName']}": a["ArcherID"]
            for a in archers
        }

        selected_archer = st.selectbox(
            "Select Archer", options=list(archer_options.keys())
        )
        archer_id = archer_options[selected_archer]

        username = st.text_input("Username", value=str(archer_id))

        # Default password follows the pattern: aAa{archer_id}$%
        default_password = f"aAa{archer_id}$%"
        st.info(f"Default password will be: {default_password}")

        is_recorder = st.checkbox("Grant Recorder Privileges")

        # In the "Create Account" section, replace the current password hashing with:
        if st.button("Create Account"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Generate a new salt and hash the password
                salt = generate_salt()
                password_hash = hash_password(default_password, salt)

                # Call the stored procedure with updated parameters
                result_args = cursor.callproc(
                    "uspManageUserAccount",
                    [
                        "CREATE",
                        0,
                        archer_id,
                        username,
                        password_hash,
                        is_recorder,
                        0,
                        "",
                    ],
                )

                # Update the salt and hash type
                cursor.execute(
                    "UPDATE AppUser SET Salt = %s, HashType = 'salted_sha256' WHERE UserID = LAST_INSERT_ID()",
                    (salt,)
                )
                
                conn.commit()

                # Get output parameters
                result_id = result_args[6]
                message = result_args[7]

                cursor.close()
                conn.close()

                if result_id > 0:
                    st.success(f"{message} (User ID: {result_id})")
                else:
                    st.error(message)

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")

    with tab3:
        # Change password or delete account
        st.subheader("Change Password or Delete Account")

        users = get_all_users()
        if not users:
            st.info("No user accounts found.")
            return

        user_options = {
            f"{u['UserID']} - {u['ArcherName']} ({u['Username']})": u["UserID"]
            for u in users
        }

        selected_user = st.selectbox(
            "Select User", options=list(user_options.keys()), key="manage_user"
        )
        user_id = user_options[selected_user]

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Change Password")

            password_option = st.radio(
                "Password Option", ["Set Custom Password", "Reset to Default"]
            )

            if password_option == "Set Custom Password":
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                if st.button("Change Password"):
                    if not new_password:
                        st.error("Password cannot be empty.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()

                            # Generate a new salt and hash the password
                            salt = generate_salt()
                            password_hash = hash_password(new_password, salt)

                            # Call the stored procedure
                            result_args = cursor.callproc(
                                "uspManageUserAccount",
                                ["RESET", user_id, 0, "", password_hash, False, 0, ""],
                            )
                            
                            # Update the salt and hash type
                            cursor.execute(
                                "UPDATE AppUser SET Salt = %s, HashType = 'salted_sha256' WHERE UserID = %s",
                                (salt, user_id)
                            )

                            conn.commit()

                            # Output parameters
                            result_id = result_args[6]
                            message = result_args[7]

                            cursor.close()
                            conn.close()

                            if result_id > 0:
                                st.success(f"{message}")
                            else:
                                st.error(message)

                        except mysql.connector.Error as err:
                            st.error(f"Database error: {err}")
            else:  # Reset to Default
                # For reset to default password
                # For reset to default password
                if st.button("Reset to Default Password"):
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()

                        # Get archer ID for the selected user
                        # Find the user info for the selected user_id
                        selected_user_info = [u for u in users if u["UserID"] == user_id][0]
                        archer_id = selected_user_info["ArcherID"]  # This will be 183 for the selected user

                        # Default password and salt/hash
                        default_password = f"aAa{archer_id}$%"
                        salt = generate_salt()
                        password_hash = hash_password(default_password, salt)

                        # Call the stored procedure
                        result_args = cursor.callproc(
                            "uspManageUserAccount",
                            ["RESET", user_id, 0, "", password_hash, False, 0, ""],
                        )
                        
                        # Update the salt and hash type
                        cursor.execute(
                            "UPDATE AppUser SET Salt = %s, HashType = 'salted_sha256' WHERE UserID = %s",
                            (salt, user_id)
                        )

                        conn.commit()

                        # Output parameters
                        result_id = result_args[6]
                        message = result_args[7]

                        cursor.close()
                        conn.close()

                        if result_id > 0:
                            st.success(f"{message}")
                            st.info(f"New password is: {default_password}")
                        else:
                            st.error(message)

                    except mysql.connector.Error as err:
                        st.error(f"Database error: {err}")
        with col2:
            st.write("### Delete Account")
            st.warning("This action cannot be undone!")
            confirm_delete = st.checkbox("I understand the consequences")

            if st.button("Delete User Account", disabled=not confirm_delete):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    # Call the stored procedure
                    result_args = cursor.callproc(
                        "uspManageUserAccount",
                        ["DELETE", user_id, 0, "", "", False, 0, ""],
                    )

                    conn.commit()

                    # Get output parameters
                    result_id = result_args[6]
                    message = result_args[7]

                    cursor.close()
                    conn.close()

                    if result_id > 0:
                        st.success(f"{message}")
                    else:
                        st.error(message)

                except mysql.connector.Error as err:
                    st.error(f"Database error: {err}")


# 2. Permission Management
def manage_permissions():
    st.header("User Permissions")

    tab1, tab2 = st.tabs(["Update Permissions", "View Permission Levels"])

    with tab1:
        # Grant/revoke recorder privileges
        st.subheader("Update User Permissions")

        users = get_all_users()
        if not users:
            st.info("No user accounts found.")
            return

        # Process user data to ensure consistent boolean values
        for user in users:
            # Make sure IsRecorder is a proper boolean
            if isinstance(user["IsRecorder"], str):
                user["IsRecorder"] = user["IsRecorder"] == "Yes"

            # Make sure IsAdmin is a proper boolean
            if isinstance(user["IsAdmin"], str):
                user["IsAdmin"] = user["IsAdmin"] == "Yes"

        user_options = {
            f"{u['UserID']} - {u['ArcherName']} ({u['Username']})": u["UserID"]
            for u in users
        }

        selected_user = st.selectbox("Select User", options=list(user_options.keys()))
        user_id = user_options[selected_user]

        # Get current permission status
        selected_user_info = [u for u in users if u["UserID"] == user_id][0]
        current_recorder_status = selected_user_info["IsRecorder"]

        new_recorder_status = st.checkbox(
            "Recorder Privileges", value=current_recorder_status
        )

        if st.button("Update Permissions"):
            if new_recorder_status == current_recorder_status:
                st.info("No changes to apply.")
            else:
                action_text = "grant" if new_recorder_status else "revoke"
                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    # Call the stored procedure
                    result_args = cursor.callproc(
                        "uspUpdateRecorderPrivilege",
                        [user_id, new_recorder_status, False, ""],
                    )

                    conn.commit()

                    # Get output parameters
                    success = result_args[2]
                    message = result_args[3]

                    cursor.close()
                    conn.close()

                    if success:
                        st.success(
                            f"Successfully {action_text}ed recorder privileges for {selected_user_info['ArcherName']}"
                        )
                    else:
                        st.error(message)

                except mysql.connector.Error as err:
                    st.error(f"Database error: {err}")

    with tab2:
        # View current permissions
        st.subheader("Current Permission Levels")

        users = get_all_users()
        if users:
            # Process user data to ensure consistent boolean values before display
            for user in users:
                # Ensure we have string values for display
                if isinstance(user["IsRecorder"], bool):
                    user["Is Recorder"] = "Yes" if user["IsRecorder"] else "No"
                else:
                    user["Is Recorder"] = user["IsRecorder"]  # Already a string

                if isinstance(user["IsAdmin"], bool):
                    user["Is Admin"] = "Yes" if user["IsAdmin"] else "No"
                else:
                    user["Is Admin"] = user["IsAdmin"]  # Already a string

            # Create a simplified dataframe with just the permission information
            permission_data = [
                {
                    "User ID": u["UserID"],
                    "Username": u["Username"],
                    "Archer Name": u["ArcherName"],
                    "Is Recorder": u["Is Recorder"],
                    "Is Admin": u["Is Admin"],
                }
                for u in users
            ]

            df = pd.DataFrame(permission_data)
            st.dataframe(df)
        else:
            st.info("No user accounts found.")


# 3. Account Self-Management
def manage_account():
    st.header("Account Settings")
    st.subheader("Change Password")

    # Get current user ID from session state
    current_user_id = st.session_state.user_id

    # Password change options
    password_option = st.radio(
        "Password Option", ["Set Custom Password", "Reset to Default"]
    )

    if password_option == "Set Custom Password":
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        # For custom password reset
        if st.button("Change Password"):
            if not new_password:
                st.error("Password cannot be empty.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    # Generate a new salt and hash the password
                    salt = generate_salt()
                    password_hash = hash_password(new_password, salt)

                    # Call the stored procedure
                    result_args = cursor.callproc(
                        "uspManageUserAccount",
                        ["RESET", current_user_id, 0, "", password_hash, False, 0, ""],
                    )
                    
                    # Update the salt and hash type
                    cursor.execute(
                        "UPDATE AppUser SET Salt = %s, HashType = 'salted_sha256' WHERE UserID = %s",
                        (salt, current_user_id)
                    )

                    conn.commit()

                    # Get output parameters
                    result_id = result_args[6]
                    message = result_args[7]

                    cursor.close()
                    conn.close()

                    if result_id > 0:
                        st.success(f"{message}")
                    else:
                        st.error(message)

                except mysql.connector.Error as err:
                    st.error(f"Database error: {err}")
    else:  # Reset to Default
        # For reset to default password
        if st.button("Reset to Default Password"):
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Get archer ID from user ID for password pattern
                archer_id = st.session_state.archer_id

                # Default password and hash
                default_password = f"aAa{archer_id}$%"
                
                # Generate a new salt and hash the password
                salt = generate_salt()
                password_hash = hash_password(default_password, salt)

                # Call the stored procedure
                result_args = cursor.callproc(
                    "uspManageUserAccount",
                    ["RESET", current_user_id, 0, "", password_hash, False, 0, ""],
                )
                
                # Update the salt and hash type
                cursor.execute(
                    "UPDATE AppUser SET Salt = %s, HashType = 'salted_sha256' WHERE UserID = %s",
                    (salt, current_user_id)
                )

                conn.commit()

                # Get output parameters
                result_id = result_args[6]
                message = result_args[7]

                cursor.close()
                conn.close()

                if result_id > 0:
                    st.success(f"{message}")
                    st.info(f"New password is: {default_password}")
                else:
                    st.error(message)

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")

    # Display current user information
    st.markdown("---")
    st.subheader("Account Information")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get current user details
        cursor.execute(
            """
            SELECT u.UserID, u.Username, u.ArcherID, 
                   CONCAT(a.FirstName, ' ', a.LastName) as ArcherName,
                   IF(u.IsRecorder, 'Yes', 'No') as IsRecorder,
                   IF(u.IsAdmin, 'Yes', 'No') as IsAdmin
            FROM AppUser u
            JOIN Archer a ON u.ArcherID = a.ArcherID
            WHERE u.UserID = %s
            """,
            (current_user_id,),
        )

        user_info = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_info:
            st.write(f"**Username:** {user_info['Username']}")
            st.write(f"**Name:** {user_info['ArcherName']}")
            st.write(f"**Archer ID:** {user_info['ArcherID']}")
            st.write(f"**Recorder Privileges:** {user_info['IsRecorder']}")
            st.write(f"**Admin Privileges:** {user_info['IsAdmin']}")
        else:
            st.error("Unable to retrieve account information.")

    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
