import os
import streamlit as st
import openai
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
from .database import get_connection
import sqlalchemy
import re

# Load environment variables
load_dotenv()

# Configure OpenAI with Deepseek R1 API
openai.api_key = os.getenv("DEEPSEEK_API_KEY")
openai.base_url = "https://api.deepseek.com"  # Adjust if necessary for Deepseek


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
    Given a user query, generate appropriate SQL code and determine if the user has permission to execute it.
    
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
    
    # Response Format:
    1. Write your response in well-formatted markdown
    2. Begin with a permission check: State whether the user has permission for this operation based on their role
    3. Provide a SQL explanation: Explain what the SQL query will do (when applicable)
    4. Include SQL code in proper markdown code blocks using triple backticks with the 'sql' language specifier: ```sql
    5. When providing SQL to execute, ALWAYS include a final code block with this exact format:
    
    ###Final code to execute###
    ```sql
    <YOUR SQL QUERY HERE>
    ```
    
    IMPORTANT:
    - ALWAYS respond using markdown formatting for better readability
    - Use headers (##, ###), bullet points, and other markdown formatting as appropriate
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
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )


# Execute SQL query with proper error handling
def execute_sql_query(sql_query, archer_id=None):
    try:
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
def generate_sql(prompt, user_info):
    system_prompt = get_system_prompt(user_info)

    try:
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )

        # Extract the response
        assistant_response = response.choices[0].message.content

        # Check if permission denied
        if (
            "not permitted" in assistant_response.lower()
            or "no permission" in assistant_response.lower()
        ):
            return {"permission": False, "sql": "", "explanation": assistant_response}

        # Extract the final SQL query to execute (last code block)
        final_sql = extract_final_sql(assistant_response)

        return {
            "permission": True,
            "sql": final_sql,
            "explanation": assistant_response,
        }

    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return {"permission": False, "sql": "", "explanation": f"Error: {str(e)}"}


# Main chatbot interface
def sql_chatbot():
    # Only allow admins to access this feature
    if not st.session_state.is_admin:
        st.error(
            "You don't have permission to access the SQL Assistant. Admin access required."
        )
        return

    st.header("SQL Assistant (Admin Only)")
    st.write(
        "Ask questions about the database in natural language, and our SQL assistant will generate and execute the appropriate SQL query."
    )

    # Collect user information for context
    user_info = {
        "user_id": getattr(st.session_state, "user_id", "Unknown"),
        "archer_id": getattr(st.session_state, "archer_id", "Unknown"),
        "name": getattr(st.session_state, "archer_name", "Unknown"),
        "role": "Admin",  # Since we already verified they're an admin
    }

    # User input
    user_prompt = st.text_area(
        "What would you like to know about the database?",
        placeholder="e.g., Show me all archers who scored above 500 in the last month",
        height=100,
    )

    if st.button("Generate SQL"):
        if user_prompt.strip():
            with st.spinner("Generating SQL..."):
                # Generate SQL from prompt
                result = generate_sql(user_prompt, user_info)

                # Display explanation (the full response) using markdown
                st.header("AI Response")
                st.markdown(result["explanation"])

                # If permitted and SQL was extracted, execute it
                if result["permission"] and result["sql"]:
                    st.subheader("Query Results")
                    with st.spinner("Executing query..."):
                        query_result = execute_sql_query(result["sql"])
                        st.dataframe(query_result)
        else:
            st.warning("Please enter a question about the database.")
