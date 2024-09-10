import csv
#read all the coordinates form the Police.csv file and create geo id
#geo_id = lat + lon
geo_ids=[]
with open('city_state.csv', 'r',encoding="utf-8") as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        lat = row["latitude"]
        lon = row["longitude"]
        geo_id = lat+lon
        geo_ids.append(geo_id.replace(".", "").replace("-", ""))

# Specify the input and output file names
input_file = 'city_state.csv'
output_file = 'city_state_id.csv'

header=[]
data = []

with open(input_file, 'r', newline='',encoding="utf-8") as infile:
    reader = csv.reader(infile)
    header = next(reader)  # Read and store the header
    for row in reader:
        data.append(row)
        
# Add the new column data to the header
header = ["geo_id"] + header
# Add the new column data to each row in the list
for i, row in enumerate(data):
    data[i] = [geo_ids[i]] + row
    

# Write the modified data back to a new CSV file
with open(output_file, 'w', newline='',encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerow(header)
    writer.writerows(data)


