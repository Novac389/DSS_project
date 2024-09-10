import pyodbc
import json
import csv
import xml.etree.ElementTree as ET
from alive_progress import alive_it
from datetime import datetime, date


#Dictionary Values
dict_age = json.load(open('dict_partecipant_age.json'))
dict_type = json.load(open('dict_partecipant_type.json'))
dict_status = json.load(open('dict_partecipant_status.json'))

#Connection to Group_ID_42_DB
server = "tcp:lds.di.unipi.it"
database = "Group_ID_42_DB"
uid = "Group_ID_42"
password = "3RG5497A"
connectionString = "DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+";DATABASE="+database+";UID="+uid+";PWD="+password
conn = pyodbc.connect(connectionString)

#True: allow error prints during execution
print_option = False



#########################   UTILS   ######################### 

#Input: date string in the format "yyyy-mm-dd hh:mm:ss"
#Return: a list with [year, month, day, quarter, day of the week]
def compute_date(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

    quarter = (date.month - 1) // 3 + 1   #compute the quarter {1, 2, 3, 4}
    quarter_string = f"Q{quarter}"  #{Q1, Q2, Q3, Q4}
    day_of_the_week = date.strftime('%A')  #return the name of the day

    return [date.year, date.month, date.day, quarter_string, day_of_the_week]


#Compute the crime gravity (based on dict values)
def compute_crime_gravity(age, type_, status):
    return dict_age[age]*dict_type[type_]*dict_status[status]


#Compute the partecipant_id
# {M or F}  +  age_group  +  status  +  type(Suspect|Victim)
def compute_participant_id(age_group, gender, status, type_):
    participant_id = gender[0]+str(dict_age[age_group])+str(dict_status[status]) + str(dict_type[type_])
    return participant_id

#Compute the gun id
def compute_gun_id(gun_stolen, gun_type):
    gun_id = gun_type+"_"+gun_stolen
    return gun_id

#Compute the geography id
# "latitude number"+"longitude number" (without '.' and '-')
def compute_geo_id(latitude, longitude):
    geo_id = (str(latitude) +str(longitude))
    geo_id = geo_id.replace('.', '').replace('-', '')
    return geo_id

#Input: name of the table, list of the column names, list of values to insert
#Return: the INSERT query string
def build_query(table_name, columns, values):
    columns_string = ', '.join(columns)
    values = [val if val!="" else 'NULL' for val in values]  #convert empty string into NULL
    #Formatting values appropriately for the query
    formatted_values = []
    for val in values:
        if isinstance(val, str) & (val!='NULL'):
            formatted_values.append(f"'{val}'")  #enclosing string value in single quotes
        else:
            formatted_values.append(str(val))  #convert non-string value into string
    values_string = ', '.join(formatted_values)
    
    query = f"INSERT INTO {table_name} ({columns_string}) VALUES ({values_string})"
    return query

def perform_query(query):
    try:    # Attempts to execute the provided query
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except pyodbc.Error as ex:  #handle of exceptions
        if "Violation of PRIMARY KEY constraint" in str(ex):     
            if print_option: print("Duplicate PRIMARY KEY")
        elif "Violation of FOREIGN KEY constraint" in str(ex):
            conn.rollback()
            if print_option: print("FOREIGN KEY constrait violation in the query: "+query)
        else:   #other errors
            conn.rollback()
            print("An error occurred during the insert operation. Query failed: "+query)
            print(ex)
        
############################################################# 

#Read from Police.csv, city_state.csv, dates.xml
with open('Police.csv', 'r') as police_file, open('city_state_id.csv', 'r', encoding='utf-8') as geo_file, open('dates.xml', 'r') as date_file:
    #File readers
    tree = ET.parse(date_file)
    root = tree.getroot()
    
    # Read all lines except the first one (header)
    police_data = police_file.readlines()[1:]
    geo_data = geo_file.readlines()[1:]

    print("Loading Date Data")
    for row in alive_it(root.findall('row')):  #Insert in 'Date'
        #retrieve data
        date_string = row.find('date').text
        date_pk = (int) (row.find('date_pk').text)
        date = (str) (datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S').date()) #Sql format
        
        #build query
        columns = ["date_id", "date", "year", "month", "day", "quarter", "day_of_the_week"]
        values = [date_pk, date] + compute_date(date_string)
        query = build_query("Date", columns, values)
        
        #insert the record
        perform_query(query)
        #END FOR


    print("Loading Geo Data")
    for row in alive_it(geo_data):  #Insert in 'Geography'
        #retrieve data
        row = row.strip().split(',') 
        geo_id, latitude, longitude, city, state = row[0], row[1], row[2], row[3], row[4]
        city = city.replace("'", "_")    #needed to avoid error in INSERT operation caused by ' character
        
        #build query
        columns = ["geo_id", "latitude", "longitude", "city", "state"]
        values = [geo_id, latitude, longitude, city, state]
        query = build_query("Geography", columns, values)
        #insert the record
        perform_query(query)
    #END FOR
    
    
    print("Loading Police Data")
    for row in alive_it(police_data):  #Insert in 'Custody', 'Gun', 'Participant'
        #Retrieve data from police.csv
        row = row.strip().split(',')
        
        age_group, gender, status, type_ = row[1],row[2],row[3],row[4]
        latitude, longitude, gun_stolen, gun_type = row[5],row[6],row[7],row[8]
        custody_id = row[0]
        incident_id = row[9]
        date_id = row[10]
        
        #generating the missing ids
        gun_id = compute_gun_id(gun_stolen, gun_type)
        participant_id = compute_participant_id(age_group, gender, status, type_)
        geo_id = compute_geo_id(latitude, longitude)
        
        crime_gravity = compute_crime_gravity(age_group, type_, status)
        
        
        #build query for custody, gun, incident, participant
        custody_data = [custody_id, participant_id, gun_id, geo_id, date_id, incident_id, crime_gravity]
        gun_data = [gun_id, gun_stolen, gun_type]
        participant_data = [participant_id, age_group, gender, status, type_]
        
        #column names lists
        custody_columns = ["custody_id", "participant_id", "gun_id", "geo_id", "date_id", "incident_id", "crime_gravity"]
        gun_columns = ["gun_id", "is_stolen", "gun_type"]
        participant_columns = ["participant_id", "age_group", "gender", "status", "type"]
        
        #retrieve query string for each table
        custody_query = build_query("Custody", custody_columns, custody_data)
        gun_query = build_query("Gun", gun_columns, gun_data)
        participant_query = build_query("Participant", participant_columns, participant_data)
        
        #insert the record
        perform_query(gun_query)
        perform_query(participant_query)
        perform_query(custody_query)
    #END FOR
    
    conn.close()