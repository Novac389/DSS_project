import googlemaps as gm
import csv
from alive_progress import alive_bar
geolocator = gm.Client(key="Insert Google Api Key")

#request the reverse geocode at google maps api for retriving the city and state
#from the location coordinates
def reverse_geocode(lat, lon):
    try:
        #request to google maps api for location info
        location = geolocator.reverse_geocode((lat, lon))
        print(location)
        city = None
        state = None
        #iterate trough the response message to find the city state information
        for loc in location:
            address = loc.get("address_components", {})
            for component in address:
                types = component.get("types", [])
                #search the city name as sublocality
                if "sublocality" in types:
                    city = component["long_name"]
                #search the city name as locality
                if "locality" in types:
                    city = component["long_name"]      
                #search the state name
                if "administrative_area_level_1" in types:
                    state = component["long_name"]
            if((city!=None) and (state!=None)):break
        return  [lat, lon, city, state]
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None


coordinates = []
#read all the coordinates form the Police.csv file
with open('Police.csv', 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        lat = row["latitude"]
        lon = row["longitude"]
        coordinates.append([lat,lon])

#take only the unique coordinates form the file
unique_data = [list(x) for x in set(tuple(x) for x in coordinates)]

#csv file writing the result of google api
header = ["latitude", "longitude", "city", "state"]
with open("city_state.csv", 'w', newline='',encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(header)
    with alive_bar(len(unique_data)) as bar: #progress bar
        for coord in unique_data:
            csv_writer.writerow(reverse_geocode(coord[0], coord[1]))
            bar()
        
        
        