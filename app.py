from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)

# Your API key
API_KEY = "f1e5ca6d70e837026e976e7f5a94f058"
API_URL = "https://api.the-odds-api.com/v4/sports/upcoming/odds"

# Set parameters
params = {
    "apiKey": API_KEY,
    "regions": "us",  # Odds from US sportsbooks
    "markets": "h2h",  # Moneyline odds
}

placed_bets = {}  # Track bets as "BET ON"

# Function to convert decimal odds to American odds
def decimal_to_american(decimal_odds):
    if decimal_odds >= 2.00:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"{int(-100 / (decimal_odds - 1))}"

# Function to format event date
def format_date(date_str):
    try:
        event_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return event_time.strftime("%Y-%m-%d %I:%M %p UTC")
    except:
        return "Unknown Date"

# Function to fetch AOFs
def fetch_aofs(min_arb_percentage, bet_amount=50.00):
    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        aof_list = []

        for game in data:
            best_home_odds = 0
            best_away_odds = 0
            best_home_bookmaker = ""
            best_away_bookmaker = ""
            event_date = format_date(game.get('commence_time', ''))

            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker['markets']:
                    for outcome in market['outcomes']:
                        if outcome['name'] == game['home_team'] and outcome['price'] > best_home_odds:
                            best_home_odds = outcome['price']
                            best_home_bookmaker = bookmaker['title']
                        elif outcome['name'] == game['away_team'] and outcome['price'] > best_away_odds:
                            best_away_odds = outcome['price']
                            best_away_bookmaker = bookmaker['title']

            # Create a unique key for this bet
            bet_key = f"{game['home_team']} vs {game['away_team']} - {event_date}"

            # Convert odds to American format
            american_home_odds = decimal_to_american(best_home_odds)
            american_away_odds = decimal_to_american(best_away_odds)

            # Add AOF to list
            aof_list.append({
                "bet_key": bet_key,
                "match": f"{game['home_team']} vs {game['away_team']}",
                "sport": game['sport_title'],
                "event_date": event_date,
                "home_odds": american_home_odds,
                "home_bookmaker": best_home_bookmaker,
                "away_odds": american_away_odds,
                "away_bookmaker": best_away_bookmaker,
                "bet_status": placed_bets.get(bet_key, "Not Placed")
            })

        return aof_list
    else:
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    min_arb_percentage = 5.0  # Default filter

    if request.method == "POST":
        min_arb_percentage = float(request.form.get("min_arb", 5.0))  

    aofs = fetch_aofs(min_arb_percentage)
    return render_template("index.html", aofs=aofs, min_arb=min_arb_percentage)

@app.route("/mark_bet/<bet_key>", methods=["POST"])
def mark_bet(bet_key):
    placed_bets[bet_key] = "BET ON"
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
