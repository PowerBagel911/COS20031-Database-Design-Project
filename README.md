# Archery Club Database Test Script

This repository contains scripts to test the connection to the Archery Club Database and perform simple queries to verify that the database is working correctly.

## Requirements
- Python 3.6 or higher
- mysql-connector-python package
- pandas (optional, for the pandas version of the script)

## Installation

1. Install the required dependencies:

For the basic version:
```
pip install -r requirements.txt
```

For the pandas version:
```
pip install -r requirements_pandas.txt
```

## Available Scripts

### Basic Version
Run the basic test script:
```
python db_test.py
```

### Pandas Version
Run the pandas version for prettier output:
```
python db_test_with_pandas.py
```

## What the scripts do

Both scripts will:
1. Connect to the Feenix MariaDB database
2. Count the number of archers in the database
3. List all equipment types
4. Show information about rounds
5. Test the `uspGetRoundDetails` stored procedure for RoundID 1

The pandas version additionally:
- Uses pandas DataFrames to display results in a tabular format
- Includes an extra query to show archer information

If successful, you should see output showing the results of these queries.
