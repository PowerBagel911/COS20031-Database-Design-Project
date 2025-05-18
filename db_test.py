import mysql.connector
import sys


def test_db_connection():
    # Database connection parameters
    config = {
        "host": "feenix-mariadb.swin.edu.au",
        "user": "s104844794",
        "password": "260804",
        "database": "s104844794_db",
    }

    try:
        # Establish connection
        print("Attempting to connect to database...")
        conn = mysql.connector.connect(**config)

        if conn.is_connected():
            print("Connection successful!")
            cursor = conn.cursor()

            # Test query 1: Count archers
            cursor.execute("SELECT COUNT(*) FROM Archer")
            result = cursor.fetchone()
            print(f"Total archers in database: {result[0]}")

            # Test query 2: List equipment types
            print("\nEquipment Types:")
            cursor.execute("SELECT * FROM EquipmentType")
            equipment_types = cursor.fetchall()
            for eq_type in equipment_types:
                print(
                    f"ID: {eq_type[0]}, Name: {eq_type[1]}, Description: {eq_type[2]}"
                )

            # Test query 3: Get some round information
            print("\nRound Information:")
            cursor.execute(
                "SELECT RoundID, RoundName, TotalArrows, PossibleScore FROM Round LIMIT 5"
            )
            rounds = cursor.fetchall()
            for round_info in rounds:
                print(
                    f"ID: {round_info[0]}, Name: {round_info[1]}, Arrows: {round_info[2]}, Max Score: {round_info[3]}"
                )

            # Test a stored procedure
            print("\nTesting stored procedure uspGetRoundDetails for RoundID 1:")
            cursor.callproc("uspGetRoundDetails", [1])

            # Process stored procedure results
            for result in cursor.stored_results():
                for row in result.fetchall():
                    print(row)

            # Close cursor and connection
            cursor.close()
            conn.close()
            print("\nConnection closed.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

    return True


if __name__ == "__main__":
    success = test_db_connection()
    sys.exit(0 if success else 1)
