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

# Function to calculate arbitrage percentage
def calculate_arbitrage(home_odds, away_odds):
    if home_odds > 0 and away_odds > 0:
        arb_percent = (1/home_odds) + (1/away_odds)
        return (1 - arb_percent) * 100  # Convert to percentage
    return -100  # No arbitrage

# Function to format event date
def format_date(date_str):
    try:
        event_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))  # Convert to datetime object
        return event_time.strftime("%Y-%m-%d %I:%M %p UTC")  # Format to readable date
    except:
        return "Unknown Date"

# Function to calculate bet amounts
def calculate_bets(home_odds, away_odds, bet1=50.00):
    bet2 = round((bet1 * home_odds) / away_odds, 2)  # Calculate second bet
    total_investment = round(bet1 + bet2, 2)
    total_payout = round((bet2 * away_odds), 2)
    guaranteed_profit = round(total_payout - total_investment, 2)
    roi = round((guaranteed_profit / total_investment) * 100, 2)

    return bet1, bet2, total_investment, total_payout, guaranteed_profit, roi

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

            # Calculate Arbitrage Percentage
            arb_percentage = calculate_arbitrage(best_home_odds, best_away_odds)

            # Filter by Arbitrage Percentage
            if arb_percentage >= min_arb_percentage:
                bet1, bet2, total_investment, total_payout, guaranteed_profit, roi = calculate_bets(best_home_odds, best_away_odds, bet_amount)

                aof_list.append({
                    "bet_key": bet_key,
                    "match": f"{game['home_team']} vs {game['away_team']}",
                    "sport": game['sport_title'],
                    "event_date": event_date,
                    "home_odds": best_home_odds,
                    "home_bookmaker": best_home_bookmaker,
                    "away_odds": best_away_odds,
                    "away_bookmaker": best_away_bookmaker,
                    "arb_percentage": round(arb_percentage, 2),
                    "bet1": bet1,
                    "bet2": bet2,
                    "total_investment": total_investment,
                    "total_payout": total_payout,
                    "guaranteed_profit": guaranteed_profit,
                    "roi": roi,
                    "bet_status": placed_bets.get(bet_key, "Not Placed")  # Get status or default "Not Placed"
                })

        return aof_list
    else:
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    min_arb_percentage = 5.0  # Default filter
    bet_amount = 50.00  # Default bet amount

    if request.method == "POST":
        min_arb_percentage = float(request.form.get("min_arb", 5.0))  # Default to 5.0 if missing
        bet_amount = float(request.form.get("bet_amount", 50.00))  # Default to 50.00 if missing

    aofs = fetch_aofs(min_arb_percentage, bet_amount)
    return render_template("index.html", aofs=aofs, min_arb=min_arb_percentage, bet_amount=bet_amount)

@app.route("/mark_bet/<bet_key>", methods=["POST"])
def mark_bet(bet_key):
    placed_bets[bet_key] = "BET ON"  # Update status to "BET ON"
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
