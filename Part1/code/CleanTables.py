#Remove all record from the specified tables (default delete from all tables)

import pyodbc
import sys

server = "tcp:lds.di.unipi.it"
database = "Group_ID_42_DB"
uid = "Group_ID_42"
password = "3RG5497A"
connectionString = "DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+";DATABASE="+database+";UID="+uid+";PWD="+password
conn = pyodbc.connect(connectionString)


if len(sys.argv) > 1:
    table_list = sys.argv[1:]  # Get table names from command-line arguments
else:
    table_list = ["Custody", "Date", "Gun", "Geography", "Participant"]  # Default table names


cursor = conn.cursor()
for table in table_list:
    delete_query = f"DELETE FROM {table}"    
    try:
        cursor.execute(delete_query)
        conn.commit()
        print(f"All records have been removed from the table {table}")
    except pyodbc.Error as ex:
        conn.rollback()
        print("An error occurred while deleting records:", ex)

conn.close()







