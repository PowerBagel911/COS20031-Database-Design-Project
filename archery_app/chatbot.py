import streamlit as st
import mysql.connector
import pandas as pd
from .database import get_connection, verify_connection
import sqlalchemy
import re
import google.generativeai as genai

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
    
    # Role-Based Data Access Permissions:
    
    ## Normal Archer
    - Can READ their own records in the Score table
    - Can READ round information from Round, RoundRange, and TargetFace tables
    - Can READ appropriate rounds in EquivalentRound
    - Can READ competition results in Competition and CompetitionScore
    - Can INSERT into StagedScore (submit scores)
    - Can READ detailed score breakdowns in End and Arrow tables (their own scores only)
    - NO access to modify other archers' data
    
    ## Recorder (includes all Archer permissions, plus:)
    - Can CREATE/UPDATE records in Archer, Round, RoundRange, Competition, and CompetitionScore tables
    - Can UPDATE Score table (set IsApproved, ApprovedBy, IsCompetition)
    - Can process entries from StagedScore
    - Can INSERT/UPDATE detailed scoring data in End and Arrow tables
    
    ## Admin (full access)
    - Has FULL CRUD access to all tables
    - Can manage user accounts and permissions in AppUser
    - Can update classification systems in Class and AgeGroup
    - Can maintain equipment types in EquipmentType
    - Can handle rule changes through EquivalentRound
    
    # Question Type Determination:
    First, determine if the user's question requires SQL execution or is just a general database/application question:
    
    ## General Questions (NO SQL execution needed):
    - Questions about database concepts, schema, or application features
    - Questions about how data is stored or structured
    - Questions about permissions and access control
    - General information about archery club operations
    - Explanations of how certain database operations work
    
    ## SQL Execution Questions:
    - Queries to retrieve specific data (e.g., "Show me all archers who...")
    - Requests to update, insert, or delete data
    - Requests for statistical analysis of data
    - Any question requiring actual data from the database
    
    # Response Format:
    For general questions:
    1. Always answer the question in the natural language of the user, and MUST not include any permission check information or SQL determination information in the user response
    2. Provide a clear, well-formatted markdown response
    3. Do NOT include executable SQL code
    4. You can include example SQL to illustrate concepts, but clearly mark them as examples
    
    For questions that require SQL execution:
    1. Begin with a permission check: State whether the user has permission for this operation based on their role
    2. Provide a detailed SQL explanation with bullet points: Explain what the SQL query will do
    3. Include SQL code in proper markdown code blocks using triple backticks with the 'sql' language specifier: ```sql
    4. When providing SQL to execute, ALWAYS include a final code block with this heading 3 "Final code to execute:", followed by the SQL code in a code block
    5. If the user does not have permission, provide a clear explanation of why
    
    IMPORTANT:
    - ALWAYS respond using markdown formatting for better readability
    - Use headers (###), bullet points, and other markdown formatting as appropriate
    - Only use heading 3 for sections
    - For SQL execution questions, provide clear and detailed explanations for SQL queries
    - Organize your response with clear sections
    - Use proper markdown code blocks with 'sql' language specifier for all SQL code
    - For executable SQL, provide a FINAL code block with the exact format shown above
    - Do not execute operations that violate the permission rules
    - Ensure queries are restricted to appropriate data for the user's role
    - For Normal Archers, add appropriate WHERE clauses to limit queries to ONLY their data where applicable
    - For queries involving joins or multiple tables, explain the relationships briefly
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


# Extract the final executable SQL code from the response
def extract_final_sql(text):
    # Look for the standardized format first
    standard_pattern = r"###Final code to execute###\s*```(?:sql)?\s*(.*?)\s*```"
    standard_match = re.search(standard_pattern, text, re.DOTALL | re.IGNORECASE)

    if standard_match:
        return standard_match.group(1).strip()

    # Fallback to looking for any code blocks
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
        model = genai.GenerativeModel("gemini-2.0-flash")

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

        # Extract the final SQL query to execute (last code block)
        final_sql = extract_final_sql(assistant_response)

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

    if "user_prompt_text" not in st.session_state:
        st.session_state.user_prompt_text = ""

    if "should_process_message" not in st.session_state:
        st.session_state.should_process_message = False

    if "message_to_process" not in st.session_state:
        st.session_state.message_to_process = ""

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

    # Process message if needed (after rerun)
    if st.session_state.should_process_message:
        final_prompt = st.session_state.message_to_process
        st.session_state.should_process_message = False
        st.session_state.message_to_process = ""

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": final_prompt})

        # Update the chat container to display the new message
        with st.spinner("Generating Answer..."):
            # Generate SQL from prompt with chat history and query results
            result = generate_sql(
                final_prompt,
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

            # Add assistant response to message history
            st.session_state.messages.append(
                {"role": "assistant", "content": explanation}
            )

            # Store query result with this message
            query_data = {"sql": None, "df": pd.DataFrame()}

            # If permitted and SQL was extracted, execute it
            if result["permission"] and result["sql"]:
                with st.spinner("Executing query..."):
                    query_result = execute_sql_query(result["sql"])

                    # Save the executed query and result in query_data
                    query_data["sql"] = result["sql"]
                    query_data["df"] = query_result

                    # Save the executed query for context in next conversation
                    st.session_state.last_executed_query = result["sql"]

                    # Store query result for context in next conversation
                    if not query_result.empty:
                        # Convert DataFrame to a string representation
                        result_string = query_result.to_string(index=False)
                        # Save result for next query context
                        st.session_state.last_query_result = result_string
                        # Add to all query results
                        st.session_state.all_query_results.append(result_string)
                    else:
                        message = "The query returned no results."
                        st.session_state.last_query_result = message
                        st.session_state.all_query_results.append(message)

            # Add query data to query_results list
            st.session_state.query_results.append(query_data)

    # Display chat history first
    chat_container = st.container()
    with chat_container:
        if st.session_state.messages:
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    # Display the message content
                    st.markdown(message["content"])

                    # Display query results if this message has associated results
                    if (
                        message["role"] == "assistant"
                        and i // 2 < len(st.session_state.query_results)
                        and st.session_state.query_results[i // 2]
                    ):
                        query_data = st.session_state.query_results[i // 2]
                        if query_data.get("sql") and query_data.get("df") is not None:
                            with st.expander("SQL Query Results"):
                                st.code(query_data["sql"], language="sql")
                                if not query_data["df"].empty:
                                    st.dataframe(
                                        query_data["df"], use_container_width=True
                                    )
                                else:
                                    st.info("The query returned no results.")

    # Function to clear input field
    def clear_input():
        st.session_state.user_prompt_text = ""

    # Function to submit message (set flags for processing after rerun)
    def submit_message():
        if st.session_state.user_prompt_text.strip():
            # Queue message for processing after rerun
            st.session_state.message_to_process = st.session_state.user_prompt_text
            st.session_state.should_process_message = True
            # Clear the input field
            st.session_state.user_prompt_text = ""

    # Function to clear the conversation
    def clear_conversation():
        st.session_state.chat_history = None
        st.session_state.messages = []
        st.session_state.last_query_result = None
        st.session_state.all_query_results = []
        st.session_state.query_results = []
        st.session_state.last_executed_query = None
        st.session_state.last_query_dataframe = pd.DataFrame()
        st.session_state.user_prompt_text = ""
        if "last_query_message" in st.session_state:
            del st.session_state.last_query_message

    # Create a visually distinct container for the chat input and buttons
    with st.container(border=True):
        # Chat input spanning full width
        st.text_area(
            "What would you like to know about the database?",
            placeholder="e.g., Show me all archers who scored above 500 in the last month",
            height=69,
            key="user_prompt_text",
            label_visibility="collapsed",
        )

        # Create two columns for the input buttons
        col1, col2 = st.columns(2)

        with col1:
            # Send button will trigger the submit_message callback
            send_button = st.button(
                "Send →", key="send", use_container_width=True, on_click=submit_message
            )

        with col2:
            # Clear button will clear the text area
            clear_button = st.button(
                "Clear Text",
                key="clear_text",
                use_container_width=True,
                on_click=clear_input,
            )

    # Clear conversation button below the input container
    if st.session_state.messages:
        clear_conv_button = st.button(
            "Clear Conversation",
            key="clear_chat",
            use_container_width=True,
            on_click=clear_conversation,
        )
