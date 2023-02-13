import json
import os
from ast import Continue
from distutils import text_file
from tkinter.ttk import Style
from turtle import clear
from unicodedata import name
from urllib import response

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

console = Console(record = True)
load_dotenv()

flight_key = os.environ.get("FLIGHT_KEY")
weather_key = os.environ.get("WEATHER_KEY")
# Load JSON file containing airport information

def loadAirportJSON():
    
    access = open('airports.json')
    airportData = json.load(access)
    
    return airportData

# Load JSON file matching country codes with country name 

def countryJSON() :
    
    access = open('countries.json')
    countryData = json.load(access)

    return countryData

# Find outgoing flights from given airport iata

def getFlightsFromIata(iata):
    
    response = requests.get(f"https://airlabs.co/api/v9/schedules?dep_iata={iata}&api_key={flight_key}")
    json = response.json()
    response.raise_for_status()
    
    return json["response"]
         
# Find possible airport matches from user's search 

def findAirportsFromName(name, airportData):
    
    airport_choices = []
    airport_choices_names = []
    
    for airport in airportData :
        airport_name = airport["name"]
        
        if airport_name is not None and name.lower() == airport_name.lower() :
            return airport
        elif airport_name is not None and name.lower() in airport_name.lower() :
            airport_choices_names.append(airport_name)
            airport_choices.append(airport)

    if len(airport_choices_names) == 0 :
        return "404 error! Airport could not be found!"   
    if len(airport_choices_names) == 1 :
        return airport_choices[0]    
    
    airport = Prompt.ask("Multiple airports found, please choose one: ", choices = airport_choices_names)         
    
    for choice in airport_choices :
        if airport == choice["name"]:
                     
            return choice

# Find airport object of flight destination

def findAirportFromIata(iata, airportData):
    
    for airport in airportData :
        if airport.get("iata") == iata :
                 
            return airport
        
# Find country code for flight destination

def findCountryFromIso(iata) :

    countryData = countryJSON()
    airportData = loadAirportJSON()
    airport = findAirportFromIata(iata, airportData)    
        
    if airport is None :
        return "N/A"

    iso = airport["iso"]
    return countryData[iso]


# Find time and date of flight's departure and arrival

def findTimeOfDepartureAndArrival(flight) :
    
    Months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    if flight.get("dep_time") is None :
        dep_str = "N/A"
    else :
        dep_time = flight["dep_time"]
        dep_str = dep_time[11:16] + " on " + dep_time[8:10] + " "+ Months[int(dep_time[5:7])-1] + " " + dep_time[0:4] 
    
    if flight.get("arr_time") is None  :
        arr_str = "N/A"
    else :
        arr_time = flight["arr_time"]  
        arr_str = arr_time[11:16] + " on " + arr_time[8:10] + " " + Months[int(arr_time[5:7])-1] + " " + arr_time[0:4]    
                
    return [dep_str, arr_str]

# Ask user for airport name    

def getSearch():
    
    return Prompt.ask("Search for an airport")

# Get latitude and longtitude for flight destination

def lat_and_lng(iata) :
    
    airport_info = loadAirportJSON()
    for airport in airport_info :
        if airport.get("iata") == iata :
            return [airport.get("lat"),airport.get("lon")]


# Get weather for flight destination

def loadWeatherForLocation(lat, lng):
   
    response = requests.get(f"http://api.weatherapi.com/v1/current.json?key={weather_key}={lat},{lng}&aqi=no")
    json = response.json()
    response.raise_for_status()

    temp = json["current"]["temp_c"]
    conditions = json["current"]["condition"]["text"]

    return [str(temp),conditions]

# Saves table to html file

def saveTableToHtml(iata) :
    console.save_html(f"{iata} Flight Information")

# Formats table 

def formatTable(airport) :

    table = Table(title = f"{airport.get('name')}\n------Flight Information------")

    table.add_column("Flight Number", justify="left", style ="cyan")
    table.add_column("Departure From", justify="left", style = "magenta")
    table.add_column("Departure Time", justify="right", style ="yellow")
    table.add_column("Arrival At", justify="left", style = "white")
    table.add_column("Arrival Time", justify="right", style = "bright_cyan")
    table.add_column("Status", justify = "left", style = "green")
    table.add_column("Weather (°C)", justify = "right", style = "blue" )
    table.add_column("Conditions", justify = "right", style = "purple")  

    return table

# Edits table for selected airport

def renderFlights(flights, table):
    
    if len(flights) == 0 :
        text = Text("No outgoing flights from this Airport")
        text.stylize("bold red")
        console.print(text)
    else : 
            
        for flight in track(flights, description = "Processing...")  : 
            
            arr_iata = flight.get("arr_iata")
            
            if flights[0] :
                dep_iata = flights[0]["dep_iata"]
                dep_country = findCountryFromIso(dep_iata)
            else :
                dep_country = "N/A"

            flight_number = flight["flight_number"]
            times = findTimeOfDepartureAndArrival(flight)
            dep_time = times[0]
            arr_country = findCountryFromIso(arr_iata)
            arr_time = times[1]
            status = flight["status"]
            latitude_longtitude = lat_and_lng(arr_iata)

            if latitude_longtitude is None : 
                arr_weather = ["N/A","N/A"]
            else :
                arr_weather = loadWeatherForLocation(latitude_longtitude[0],latitude_longtitude[1])
            
            if status == "cancelled" :
                status = Text("cancelled")
                status.stylize("red")
            elif status == "scheduled" :
                status = Text(status)
                status.stylize("white")
            elif status == "active" :
                status = Text(status)
                status.stylize("yellow")    

            table.add_row(flight_number,dep_country,dep_time,arr_country,arr_time,status,arr_weather[0],arr_weather[1])
            
        console.print(table)
        
        ask_to_save = Confirm.ask("Do you want to save to html?") 
        if ask_to_save :
            saveTableToHtml(dep_iata)       
           

# Starts the programme  

def main():
    console.print(" ")
    console.print("✈️ ✈️ ✈️ ✈️ ✈️ ✈️ ✈️ ✈️")
    console.print("Welcome to the Airports Informer Tool")
    console.print("✈️ ✈️ ✈️ ✈️ ✈️ ✈️ ✈️ ✈️")
    console.print(" ")

    airportData = loadAirportJSON()
    

    while 1:
        airportSearch = getSearch()
        airport = findAirportsFromName(airportSearch, airportData)
        flights = getFlightsFromIata(airport["iata"])
        table = formatTable(airport)
        renderFlights(flights,table)


main()