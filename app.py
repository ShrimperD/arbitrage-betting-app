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
    "regions": "us",
    "markets": "h2h",
}

placed_bets = {}

# Function to convert decimal odds to American odds
def decimal_to_american(decimal_odds):
    if decimal_odds >= 2.00:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"{int(-100 / (decimal_odds - 1))}"

# Function to calculate arbitrage percentage
def calculate_arbitrage(home_odds, away_odds):
    inv_home = 1 / home_odds
    inv_away = 1 / away_odds
    arb_percent = (inv_home + inv_away) * 100
    return round(arb_percent, 2)

# Function to calculate bet amounts
def calculate_bets(home_odds, away_odds, base_bet=50):
    bet1 = base_bet
    bet2 = (bet1 * home_odds) / away_odds
    total_bet = bet1 + bet2
    total_payout = max(bet1 * home_odds, bet2 * away_odds)
    profit = total_payout - total_bet
    return round(bet1, 2), round(bet2, 2), round(total_bet, 2), round(profit, 2)

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

            if best_home_odds > 0 and best_away_odds > 0:
                arb_percent = calculate_arbitrage(best_home_odds, best_away_odds)

                if arb_percent < min_arb_percentage:
                    continue

                bet1, bet2, total_bet, profit = calculate_bets(best_home_odds, best_away_odds, bet_amount)

                bet_key = f"{game['home_team']} vs {game['away_team']} - {event_date}"

                aof_list.append({
                    "bet_key": bet_key,
                    "match": f"{game['home_team']} vs {game['away_team']}",
                    "sport": game['sport_title'],
                    "event_date": event_date,
                    "home_odds": decimal_to_american(best_home_odds),
                    "home_bookmaker": best_home_bookmaker,
                    "away_odds": decimal_to_american(best_away_odds),
                    "away_bookmaker": best_away_bookmaker,
                    "arb_percentage": arb_percent,
                    "bet1": bet1,
                    "bet2": bet2,
                    "total_investment": total_bet,
                    "guaranteed_profit": profit,
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
