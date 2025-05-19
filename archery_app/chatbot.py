import streamlit as st
import mysql.connector
import pandas as pd
from .database import get_connection, verify_connection
import sqlalchemy
import re
import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash"

# Configure Google Generative AI with Gemini 2.0 Flash
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


# Load SQL schema from create_tables.sql
def get_schema():
    try:
        with open("create_tables.sql", "r") as f:
            return f.read()
    except:
        return ""


# Define the system prompt with role-based permissions
def get_system_prompt(user_info):
    schema = get_schema()

    system_prompt = f"""You're a helpful SQL assistant for an archery club database using MySQL on MariaDB. 
    Given a user query, first determine if the query requires SQL execution or is just a general question about database concepts, schema, or the application.
    
    # Current User Information:
    User ID: {user_info.get('user_id', 'Unknown')}
    Archer ID: {user_info.get('archer_id', 'Unknown')}
    Name: {user_info.get('name', 'Unknown')}
    Role: {user_info.get('role', 'Unknown')}
    
    # Database Schema:
    {schema}
    
    # Database Context:
    We've successfully implemented all tables in the database schema:
    
    Tables with Limited Records (Based on Domain Rules):
    - AgeGroup - 8 age categories (Under 14, Under 16, etc.)
    - EquipmentType - 5 equipment types (Recurve, Compound, etc.)
    - TargetFace - 2 main target face sizes (80cm, 122cm)
    - Round - ~30 standard archery rounds (WA90/1440, Sydney, etc.)
    - Class - 16 combinations of age groups and genders
    - RoundRange - Defines distances and ends for each round
    - EquivalentRound - Maps base rounds to equivalent rounds for different classes
    
    Tables with 500 Records (Using Mockaroo):
    - Archer - 500 archers with names, birthdates, genders
    - AppUser - 500 user accounts linked to archers
    - Competition - 500 competitions with dates and descriptions
    - Score - 500 score records with total scores
    - StagedScore - 500 temporary scores awaiting approval
    - CompetitionScore - 500 links between competitions and scores
    - End - 500 ends (groups of 6 arrows) with formulas ensuring proper relationships
    - Arrow - 500 individual arrow scores within ends
    
    Security Monitoring:
    - SecurityLog - Tracks all security events including login attempts, permission changes, data modifications, and suspicious activities
    
    # Role-Based Data Access Permissions:
    
    ## Normal Archer
    - Can READ their own records in the Score table
    - Can READ round information from Round, RoundRange, and TargetFace tables
    - Can READ appropriate rounds in EquivalentRound
    - Can READ competition results in Competition and CompetitionScore
    - Can INSERT into StagedScore (submit scores)
    - Can READ detailed score breakdowns in End and Arrow tables (their own scores only)
    - NO access to modify other archers' data
    - NO access to SecurityLog
    
    ## Recorder (includes all Archer permissions, plus:)
    - Can CREATE/UPDATE records in Archer, Round, RoundRange, Competition, and CompetitionScore tables
    - Can UPDATE Score table (set IsApproved, ApprovedBy, IsCompetition)
    - Can process entries from StagedScore
    - Can INSERT/UPDATE detailed scoring data in End and Arrow tables
    - NO access to SecurityLog
    
    ## Admin (full access)
    - Has FULL CRUD access to all tables
    - Can manage user accounts and permissions in AppUser
    - Can update classification systems in Class and AgeGroup
    - Can maintain equipment types in EquipmentType
    - Can handle rule changes through EquivalentRound
    - Has READ access to SecurityLog for auditing and security monitoring
    - Can UPDATE SecurityLog.IsReviewed, SecurityLog.ReviewedBy, and SecurityLog.ReviewedAt fields
    
    # Dangerous Query Detection:
    Always evaluate if a query is potentially dangerous before providing executable code. A query is considered dangerous if it:
    - Deletes or drops tables without proper safeguards
    - Truncates tables
    - Performs mass updates without WHERE clauses
    - Alters database schema in a destructive way
    - Deletes multiple records without specific filtering
    - Modifies system tables or critical application data
    - Contains commands like DROP DATABASE, DROP TABLE, TRUNCATE TABLE without proper safeguards
    - Contains DELETE or UPDATE statements without WHERE clauses
    
    # Question Type Determination:
    First, determine if the user's question requires SQL execution or is just a general database/application question:
    
    ## General Questions (NO SQL execution needed):
    - Questions about database concepts, schema, or application features
    - Questions about how data is stored or structured
    - Questions about permissions and access control
    - General information about archery club operations
    - Explanations of how certain database operations work
    - Questions about security logging and auditing processes
    
    ## SQL Execution Questions:
    - Queries to retrieve specific data (e.g., "Show me all archers who...")
    - Requests to update, insert, or delete data
    - Requests for statistical analysis of data
    - Requests to review security logs or audit trails
    - Any question requiring actual data from the database
    
    # Response Format:
    For general questions:
    1. Always answer the question in the natural language of the user, and MUST not include any permission check information or SQL determination information in the user response
    2. Provide a clear, well-formatted markdown response
    3. Do NOT include executable SQL code
    4. You can include example SQL to illustrate concepts, but clearly mark them as examples
    
    For questions that require SQL execution:
    1. Begin with a permission check: State whether the user has permission for this operation based on their role
    2. Check if the query is potentially dangerous using the criteria above
    3. Provide a detailed SQL explanation with bullet points: Explain what the SQL query will do
    4. Include SQL code in proper markdown code blocks using triple backticks with the 'sql' language specifier: ```sql
    5. For NON-dangerous queries, include a final code block with this heading 3 "Final code to execute:", followed by the SQL code in a code block
    6. For DANGEROUS queries, include a heading "⚠️ DANGEROUS QUERY WARNING" and explain the risks. Do NOT include the "Final code to execute:" heading for these queries
    7. If the user does not have permission, provide a clear explanation of why
    
    IMPORTANT:
    - ALWAYS respond using markdown formatting for better readability
    - Use headers (###), bullet points, and other markdown formatting as appropriate
    - Only use heading 3 for sections
    - For SQL execution questions, provide clear and detailed explanations for SQL queries
    - Organize your response with clear sections
    - Use proper markdown code blocks with 'sql' language specifier for all SQL code
    - For executable SAFE SQL, provide a FINAL code block with the exact format shown above
    - For DANGEROUS SQL, provide example code but DO NOT include the "Final code to execute:" heading
    - Do not execute operations that violate the permission rules
    - Ensure queries are restricted to appropriate data for the user's role
    - For Normal Archers, add appropriate WHERE clauses to limit queries to ONLY their data where applicable
    - For queries involving joins or multiple tables, explain the relationships briefly
    - For SecurityLog queries, only provide access to Admins and ensure proper restrictions
    
    # Dangerous Query Detection:
    Always evaluate if a query is potentially dangerous before providing executable code. A query is considered dangerous if it:
    - Deletes or drops tables without proper safeguards
    - Truncates tables
    - Performs mass updates without WHERE clauses
    - Alters database schema in a destructive way
    - Deletes multiple records without specific filtering
    - Modifies system tables or critical application data
    - Contains commands like DROP DATABASE, DROP TABLE, TRUNCATE TABLE without proper safeguards
    - Contains DELETE or UPDATE statements without WHERE clauses
    """

    return system_prompt


# Create a SQLAlchemy engine for database connections
def get_sqlalchemy_engine():
    return sqlalchemy.create_engine(
        f"mysql+pymysql://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}@{st.secrets['DB_HOST']}/{st.secrets['DB_NAME']}"
    )


# Execute SQL query with proper error handling
def execute_sql_query(sql_query, archer_id=None):
    try:
        # Verify connection is established before executing
        if not verify_connection():
            return pd.DataFrame(
                [
                    {
                        "error": "Database connection not established. Please ensure you are connected to the Swinburne VPN."
                    }
                ]
            )

        engine = get_sqlalchemy_engine()
        # For SELECT queries, return a DataFrame
        if sql_query.strip().upper().startswith("SELECT"):
            return pd.read_sql(sql_query, engine)
        # For other queries, execute and return affected rows
        else:
            with engine.connect() as connection:
                result = connection.execute(sqlalchemy.text(sql_query))
                connection.commit()
                affected_rows = result.rowcount
                return pd.DataFrame([{"result": f"{affected_rows} row(s) affected"}])
    except sqlalchemy.exc.SQLAlchemyError as err:
        return pd.DataFrame([{"error": f"MySQL Error: {err}"}])
    except Exception as e:
        return pd.DataFrame([{"error": f"Error: {str(e)}"}])


# Function to detect dangerous SQL queries
def is_dangerous_query(sql_query, ai_response=""):
    """
    Checks if a SQL query is potentially dangerous.
    Returns a tuple (is_dangerous, reason) where:
    - is_dangerous: boolean indicating if the query is dangerous
    - reason: explanation of why the query is dangerous, if applicable

    Parameters:
    - sql_query: The SQL query to check
    - ai_response: The full response from the AI, which may contain warnings
    """
    if not sql_query:
        return False, ""

    sql_upper = sql_query.upper()

    # First check if the AI itself flagged the query as dangerous
    ai_danger_markers = [
        "⚠️ DANGEROUS QUERY WARNING",
        "DANGEROUS QUERY",
        "query is potentially dangerous",
        "potentially harmful",
        "could be destructive",
        "without proper safeguards",
        "without a WHERE clause",
        "⚠️",
    ]

    # Look for danger markers in the AI response
    for marker in ai_danger_markers:
        if marker.lower() in ai_response.lower():
            # Extract the context around the danger marker
            pattern = r"(?i).*?(" + re.escape(marker) + r".*?)(?:\n\n|\Z)"
            match = re.search(pattern, ai_response, re.DOTALL)
            reason = (
                match.group(1).strip()
                if match
                else f"AI identified as dangerous: {marker}"
            )
            return True, reason

    # Check for dangerous commands without proper safeguards
    danger_patterns = [
        (r"DROP\s+DATABASE", "Attempting to drop a database"),
        (r"DROP\s+TABLE", "Attempting to drop a table"),
        (r"TRUNCATE\s+TABLE", "Attempting to truncate a table"),
        (
            r"DELETE\s+FROM\s+\w+\s*(?!\s*WHERE)",
            "DELETE statement without WHERE clause",
        ),
        (
            r"UPDATE\s+\w+\s+SET\s+(?:\w+\s*=\s*[^,]+)(?:\s*,\s*\w+\s*=\s*[^,]+)*\s*(?!\s*WHERE)",
            "UPDATE statement without WHERE clause",
        ),
        (r"ALTER\s+TABLE\s+\w+\s+DROP", "Attempting to drop a column"),
        (r"DELETE\s+FROM", "DELETE operation detected"),
        (r"UPDATE\s+\w+\s+SET", "UPDATE operation detected"),
        (r"CREATE\s+USER", "Attempting to create a database user"),
        (r"GRANT\s+", "Attempting to grant permissions"),
        (r"REVOKE\s+", "Attempting to revoke permissions"),
    ]

    # Check each pattern
    for pattern, reason in danger_patterns:
        if re.search(pattern, sql_upper):
            # For DELETE and UPDATE, only flag if there's no WHERE clause
            if "DELETE" in pattern or "UPDATE" in pattern:
                if "WHERE" not in reason and "WHERE" in sql_upper:
                    continue
            return True, reason

    return False, ""


# Extract the final executable SQL code from the response
def extract_final_sql(text):
    # Check if there are any danger warnings in the text first
    danger_markers = [
        "⚠️ DANGEROUS QUERY WARNING",
        "DANGEROUS QUERY",
        "query is potentially dangerous",
        "without proper safeguards",
        "without a WHERE clause",
    ]

    for marker in danger_markers:
        if marker.lower() in text.lower():
            # If text contains danger markers, look for a code block AFTER the Final code heading
            # If not found, don't extract any SQL
            standard_match = re.search(
                r"###Final code to execute###\s*```(?:sql)?\s*(.*?)\s*```",
                text,
                re.DOTALL | re.IGNORECASE,
            )
            if not standard_match:
                return None

    # Look for the standardized format first
    standard_pattern = r"###Final code to execute###\s*```(?:sql)?\s*(.*?)\s*```"
    standard_match = re.search(standard_pattern, text, re.DOTALL | re.IGNORECASE)

    if standard_match:
        return standard_match.group(1).strip()

    # Fallback to looking for any code blocks if no danger markers were found
    code_blocks = re.findall(
        r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE
    )

    # Return the last code block if any exist
    if code_blocks:
        return code_blocks[-1].strip()

    return None


# Generate SQL from user prompt
def generate_sql(
    prompt, user_info, chat_history=None, last_query_result=None, all_query_results=None
):
    system_prompt = get_system_prompt(user_info)

    try:
        # Set up the model
        model = genai.GenerativeModel(MODEL_NAME)

        # Create the prompt with system instructions and user query
        if chat_history is None:
            # New conversation
            chat = model.start_chat(history=[])
            # Send system prompt first to ensure it's followed
            chat.send_message(system_prompt)

            # Add information about query results if available
            enhanced_prompt = f"User Question: {prompt}"

            # Include the last query result if available
            if last_query_result is not None and last_query_result != "":
                enhanced_prompt += f"\n\nThe last SQL query returned the following result:\n{last_query_result}"

            # Include all previous query results if available
            if all_query_results is not None and len(all_query_results) > 0:
                enhanced_prompt += (
                    "\n\nHere are all previous query results for context:"
                )
                for i, result in enumerate(all_query_results):
                    enhanced_prompt += f"\n\nQuery {i+1} result:\n{result}"

            response = chat.send_message(enhanced_prompt)
        else:
            # Continue existing conversation
            chat = model.start_chat(history=chat_history)

            # Add information about query results if available
            enhanced_prompt = f"User Question: {prompt}"

            # Include the last query result if available
            if last_query_result is not None and last_query_result != "":
                enhanced_prompt += f"\n\nThe last SQL query returned the following result:\n{last_query_result}"

            # Include all previous query results if available
            if all_query_results is not None and len(all_query_results) > 0:
                enhanced_prompt += (
                    "\n\nHere are all previous query results for context:"
                )
                for i, result in enumerate(all_query_results):
                    enhanced_prompt += f"\n\nQuery {i+1} result:\n{result}"

            response = chat.send_message(enhanced_prompt)

        # Extract the response
        assistant_response = response.text

        # Check if permission denied
        if (
            "not permitted" in assistant_response.lower()
            or "no permission" in assistant_response.lower()
        ):
            return {
                "permission": False,
                "sql": "",
                "explanation": assistant_response,
                "chat": chat,
            }

        # Check if the AI flagged the query as dangerous
        danger_markers = [
            "⚠️ DANGEROUS QUERY WARNING",
            "DANGEROUS QUERY",
            "query is potentially dangerous",
            "without proper safeguards",
            "without a WHERE clause",
        ]

        is_dangerous = any(
            marker.lower() in assistant_response.lower() for marker in danger_markers
        )

        # Extract the final SQL query to execute (last code block)
        final_sql = extract_final_sql(assistant_response)

        # If dangerous markers were detected but a SQL block was still found,
        # don't set permission to True - this adds an extra safety layer
        if is_dangerous and final_sql:
            return {
                "permission": False,
                "sql": final_sql,  # Still include the SQL for informational purposes
                "explanation": assistant_response,
                "chat": chat,
                "is_dangerous": True,  # Add flag to indicate it was marked dangerous
            }

        return {
            "permission": True if final_sql else False,
            "sql": final_sql,
            "explanation": assistant_response,
            "chat": chat,
        }

    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return {
            "permission": False,
            "sql": "",
            "explanation": f"Error: {str(e)}",
            "chat": None,
        }


# Main chatbot interface
def sql_chatbot():  # Initialize session state variables if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_query_result" not in st.session_state:
        st.session_state.last_query_result = None

    if "all_query_results" not in st.session_state:
        st.session_state.all_query_results = []

    if "query_results" not in st.session_state:
        st.session_state.query_results = []  # Store query results for each message

    if "last_executed_query" not in st.session_state:
        st.session_state.last_executed_query = None

    if "last_query_dataframe" not in st.session_state:
        st.session_state.last_query_dataframe = pd.DataFrame()

    # Only allow admins to access this feature
    if not st.session_state.is_admin:
        st.error(
            "You don't have permission to access the SQL Assistant. Admin access required."
        )
        return

    # Verify database connection is established
    if not verify_connection():
        st.error(
            "Cannot use SQL Assistant because database connection is not established."
        )
        st.markdown(
            """
        Please ensure you are connected to:
        - Swinburne network on campus, or
        - Swinburne VPN if off-campus
        
        [Swinburne VPN Installation Guide](https://www.swinburne.edu.au/content/dam/media/docs/Swinburne_VPN_Installation_Guide_Personal_Devices.pdf)
        """
        )
        return

    st.header("SQL Assistant (Admin Only)")
    st.write(
        "Ask questions about the database in natural language, and our Gemini-powered SQL assistant will generate and execute the appropriate SQL query."
    )

    # Collect user information for context
    user_info = {
        "user_id": getattr(st.session_state, "user_id", "Unknown"),
        "archer_id": getattr(st.session_state, "archer_id", "Unknown"),
        "name": getattr(st.session_state, "archer_name", "Unknown"),
        "role": "Admin",  # Since we already verified they're an admin
    }

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Display query results if applicable
            if (
                message["role"] == "assistant"
                and len(st.session_state.query_results) > 0
            ):
                message_index = st.session_state.messages.index(message)
                query_index = message_index // 2

                if query_index < len(st.session_state.query_results):
                    query_data = st.session_state.query_results[query_index]
                    if query_data.get("sql") and query_data.get("df") is not None:
                        with st.expander("SQL Query Results"):
                            st.code(query_data["sql"], language="sql")
                            if not query_data["df"].empty:
                                st.dataframe(query_data["df"], use_container_width=True)
                            else:
                                st.info("The query returned no results.")

    # Chat input - uses chat_input() which floats at the bottom of the page
    if prompt := st.chat_input("Ask a question about the database..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            with st.spinner("Generating Answer..."):
                # Generate SQL from prompt with chat history and query results
                result = generate_sql(
                    prompt,
                    user_info,
                    st.session_state.chat_history,
                    st.session_state.last_query_result,
                    st.session_state.all_query_results,
                )

                # Save chat history for next turn
                st.session_state.chat_history = result["chat"].history

                # Clean up the response to remove permission check information and sql determination
                explanation = result["explanation"]
                # Remove permission check and SQL determination sections if present
                explanation = re.sub(
                    r"(?i).*?permission check:.*?\n",
                    "",
                    explanation,
                    flags=re.MULTILINE,
                )
                explanation = re.sub(
                    r"(?i).*?requires SQL execution:.*?\n",
                    "",
                    explanation,
                    flags=re.MULTILINE,
                )

                # Update assistant message in session state
                st.session_state.messages.append(
                    {"role": "assistant", "content": explanation}
                )

                # Show the response in the message placeholder
                message_placeholder.markdown(explanation)

                # Store query result with this message
                query_data = {"sql": None, "df": pd.DataFrame()}

                # Handle the case when the AI detected a dangerous query
                if result.get("is_dangerous", False) and result.get("sql"):
                    # Log that we detected a dangerous query from the AI
                    query_data["sql"] = result["sql"]
                    danger_reason = "AI detected a dangerous query"
                    query_data["df"] = pd.DataFrame(
                        [
                            {
                                "warning": f"⚠️ DANGEROUS QUERY DETECTED: {danger_reason}. Query not executed for safety."
                            }
                        ]
                    )

                    # Add warning to the explanation
                    message_placeholder.markdown(
                        explanation
                        + f"\n\n⚠️ **DANGEROUS QUERY DETECTED**: {danger_reason}. Query not executed for safety."
                    )

                    # Save for next conversation context
                    warning_message = f"⚠️ DANGEROUS QUERY DETECTED: {danger_reason}. Query not executed for safety."
                    st.session_state.last_query_result = warning_message
                    st.session_state.all_query_results.append(warning_message)
                    st.session_state.last_executed_query = result["sql"]

                    # Display query results
                    with st.expander("SQL Query Results"):
                        st.code(query_data["sql"], language="sql")
                        st.warning(warning_message)

                # If permitted and SQL was extracted, check if it's dangerous and execute if safe
                # Also check the 'is_dangerous' flag that may have been set during generation
                if (
                    result.get("permission", False) and result.get("sql")
                ) and not result.get("is_dangerous", False):
                    with st.spinner("Checking and executing query..."):
                        # Double-check if the query is dangerous, also passing the AI's explanation
                        is_dangerous, danger_reason = is_dangerous_query(
                            result["sql"], result["explanation"]
                        )

                        # Save the SQL in query_data regardless of execution
                        query_data["sql"] = result["sql"]

                        if is_dangerous:
                            # Create a warning DataFrame for dangerous queries
                            query_result = pd.DataFrame(
                                [
                                    {
                                        "warning": f"⚠️ DANGEROUS QUERY DETECTED: {danger_reason}. Query not executed for safety."
                                    }
                                ]
                            )
                            # Add warning to the explanation
                            message_placeholder.markdown(
                                explanation
                                + f"\n\n⚠️ **DANGEROUS QUERY DETECTED**: {danger_reason}. Query not executed for safety."
                            )
                        else:
                            # Execute safe query
                            query_result = execute_sql_query(result["sql"])

                        # Save the result in query_data
                        query_data["df"] = query_result

                        # Save the executed query for context in next conversation
                        st.session_state.last_executed_query = result["sql"]

                        # Store query result for context in next conversation
                        if isinstance(query_result, pd.DataFrame):
                            if "warning" in query_result.columns:
                                # It's a dangerous query result
                                warning_message = query_result["warning"].iloc[0]
                                st.session_state.last_query_result = warning_message
                                st.session_state.all_query_results.append(
                                    warning_message
                                )
                            elif "error" in query_result.columns:
                                # It's an error result
                                error_message = query_result["error"].iloc[0]
                                st.session_state.last_query_result = error_message
                                st.session_state.all_query_results.append(error_message)
                            elif not query_result.empty:
                                # It's a normal result with data
                                result_string = query_result.to_string(index=False)
                                st.session_state.last_query_result = result_string
                                st.session_state.all_query_results.append(result_string)
                            else:
                                # Empty result
                                message = "The query returned no results."
                                st.session_state.last_query_result = message
                                st.session_state.all_query_results.append(message)
                        else:
                            # Handle unexpected result type
                            message = "Unexpected result format."
                            st.session_state.last_query_result = message
                            st.session_state.all_query_results.append(message)

                        # Display query results
                        with st.expander("SQL Query Results"):
                            st.code(query_data["sql"], language="sql")
                            if isinstance(query_data["df"], pd.DataFrame):
                                if "warning" in query_data["df"].columns:
                                    st.warning(query_data["df"]["warning"].iloc[0])
                                elif "error" in query_data["df"].columns:
                                    st.error(query_data["df"]["error"].iloc[0])
                                elif not query_data["df"].empty:
                                    st.dataframe(
                                        query_data["df"], use_container_width=True
                                    )
                                else:
                                    st.info("The query returned no results.")
                            else:
                                st.error("Unexpected result format.")

                # Add query data to query_results list
                st.session_state.query_results.append(query_data)

    st.markdown("<br>", unsafe_allow_html=True)
    # Clear conversation button centered below chat input
    if st.session_state.messages:
        cols = st.columns([2, 1, 2])
        with cols[1]:
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                st.session_state.chat_history = None
                st.session_state.messages = []
                st.session_state.last_query_result = None
                st.session_state.all_query_results = []
                st.session_state.query_results = []
                st.session_state.last_executed_query = None
                st.session_state.last_query_dataframe = pd.DataFrame()
                st.rerun()
