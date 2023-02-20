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


def loadAirportJSON() -> list:
    """Load in airport data from json file

    Returns:
        list: data on all the airports
    """
    access = open('airports.json')
    airportData = json.load(access)

    return airportData


def countryJSON() -> dict:
    """Loads a dictionary of country/country code key-value pairs

    Returns:
        dict: country/country code key-value pairs
    """
    
    access = open('countries.json')
    countryData = json.load(access)
   
    return countryData


def getFlightsFromIata(iata: str) -> list:
    """Loads all flight information from the relevant airport

    Args:
        iata (str): airport's unique id

    Returns:
        list: contains a dictionary of flight details
    """

    response = requests.get(f"https://airlabs.co/api/v9/schedules?dep_iata={iata}&api_key={flight_key}")
    json = response.json()
    response.raise_for_status()

    return json["response"]


def findAirportsFromName(name: str, airportData: list) -> dict:
    """Gets airport data for the selected airport name

    Args:
        name (str): name of the selected airport
        airportData (list): contains dictionaries with data for every airport

    Returns:
        dict: the data for the relevant airport
    """

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


def findAirportFromIata(iata: str, airportData: list) -> dict:
    """Get airport data for airport with the matching iata(id)

    Args:
        iata (str): id for the desired airport
        airportData (list): details of every airport

    Returns:
        dict: data for the desired airport
    """
    
    for airport in airportData :
        if airport.get("iata") == iata :
                 
            return airport
        

def findCountryFromIso(iata: str) -> str:
    """Find the country name from the country code

    Args:
        iata (str): country code

    Returns:
        str: country name
    """
    countryData = countryJSON()
    airportData = loadAirportJSON()
    airport = findAirportFromIata(iata, airportData)    
        
    if airport is None :
        return "N/A"

    iso = airport["iso"]
 
    return countryData[iso]


def findTimeOfDepartureAndArrival(flight: dict) -> list:
    """Find the departure & arrival times for a flight

    Args:
        flight (dict): flight details

    Returns:
        list: the formatted departure & arrival times
    """
    
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
 

def getSearch() -> str:
    """Get the user's airport choice

    Returns:
        str: airport name
    """
    return Prompt.ask("Search for an airport")


def lat_and_lng(iata: str) -> list:
    """Get the latitude and longtitude of the relevant airport

    Args:
        iata (str): airport code

    Returns:
        list: latitude and longtitude of the airport
    """
    
    airport_info = loadAirportJSON()
    for airport in airport_info :
        if airport.get("iata") == iata :
            return [airport.get("lat"),airport.get("lon")]


def loadWeatherForLocation(lat: str, lng: str) -> list:
    """Gets the weather at the given latitude and longtitude

    Args:
        lat (str): latitude of an airport
        lng (str): longtitude of an airport

    Returns:
        list: the temperature and weather conditions
    """
   
    response = requests.get(f"http://api.weatherapi.com/v1/current.json?key={weather_key}={lat},{lng}&aqi=no")
    json = response.json()
    response.raise_for_status()
    temp = json["current"]["temp_c"]
    conditions = json["current"]["condition"]["text"]

    return [str(temp),conditions]


def saveTableToHtml(iata: str):
    """Saves a html file containing the flights table to the directory

    Args:
        iata (str): airport code
    """
    console.save_html(f"{iata} Flight Information")


def formatTable(airport: dict) -> Table:
    """Creates the empty flight details table with all the relevant columns

    Args:
        airport (dict): _description_

    Returns:
        Table: _description_
    """
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


def renderFlights(flights: list, table: Table):
    """Inputs all the flight information into the rows of the table

    Args:
        flights (list): list of all flights at the airport
        table (Table): the empty flight details table
    """
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
        

def main():
    "Starts the programme"

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


if __name__ == "__main__":
    main()