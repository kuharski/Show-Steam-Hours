import mysql.connector

import numpy as np
import matplotlib.pyplot as plt

import requests
from requests.exceptions import HTTPError
import json

# replace with your personal key and id
STEAM_WEB_API_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
STEAM_ID = "XXXXXXXXXXXXXXXX"

# connect to database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="root",
    database="myGames"
)

# returns json response
def get_games_data(api_key, user_id): 
    try:    
        url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={user_id}&include_appinfo=true&format=json'
        response = requests.get(url)
        return response.json()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return
    except Exception as err:
        print(f'Other error occurred: {err}')
        return

# returns number of games owned
def get_game_count(data): 
    if 'response' in data and 'game_count' in data['response']:
        return data['response']['game_count']
    else:
        print("Failed to retrieve game count")
        return -1

# returns a list containing tuples of each game's information (appId, name, hoursPlayed)
def get_library(data):
    if 'response' in data and 'games' in data['response']:
        all_games = data['response']['games']
        rows = []
        for game in all_games:
            appId = game['appid']
            name = game['name']
            hoursPlayed = round(game['playtime_forever'] / 60, 1)
            
            gameInfo = (appId, name, hoursPlayed)
            rows.append(gameInfo)
        return rows
    else:
        print("Failed to retrieve the game library")
        rows = []
        return rows

# get the data
data = get_games_data(STEAM_WEB_API_KEY, STEAM_ID)
d = get_library(data)
cursor = db.cursor()

# create local database and required table
cursor.execute("CREATE DATABASE myGames")
cursor.execute("CREATE TABLE gameInfo (appId int NOT NULL, name varchar(255), hoursPlayed float(225, 1), PRIMARY KEY (appId))")

# insert game information into the table
for game in d:
    cursor.execute("INSERT INTO gameInfo (appId, name, hoursPlayed) VALUES (%s, %s, %s)", (game[0], game[1], game[2]))
    db.commit()

# get total hours played on steam
cursor.execute("SELECT SUM(hoursPlayed) AS totalHours FROM gameInfo")
totalHours = cursor.fetchall()[0][0]
cursor.close()

# order data by hours played
cursor = db.cursor()
cursor.execute("SELECT * FROM gameInfo ORDER BY hoursPlayed")
allInfo = cursor.fetchall
names = []
hours = []

# print out summary to the terminal
print("You own " + str(get_game_count(data)) + " games on Steam!")
print("You also have " + str(totalHours) + " total hours playing Steam games.")
print("Here is a summary of games you've played for more than 2 hours.")
print("\n")

for row in cursor:
# only include games played more than 2 hours (more than one sitting)
    if row[2] > 2:
        print(row[1] + ": " + str(row[2]) + " hours")
        names.append(row[1])
        hours.append(row[2])

# visualize the data using Matplotlib
plt.figure(figsize=(18,12))
plt.barh(names, hours, color="#2A475E")
plt.xticks(fontsize=12)
plt.ylabel(None)
plt.xlabel("Hours Played", fontsize=16, labelpad=20)
plt.title("Hours Played Across Steam Games", fontsize=24, pad=20)
plt.show()
db.close()
