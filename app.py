from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)

# Your API key
API_KEY = "f1e5ca6d70e837026e976e7f5a94f058"
API_URL = "https://api.the-odds-api.com/v4/sports/upcoming/odds"

params = {
    "apiKey": API_KEY,
    "regions": "us",
    "markets": "h2h",
}

placed_bets = {}

# Convert American odds to decimal
def american_to_decimal(american_odds):
    odds = float(american_odds)
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1

# Convert decimal odds to American for display
def decimal_to_american(decimal_odds):
    if decimal_odds >= 2.00:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"{int(-100 / (decimal_odds - 1))}"

def format_date(date_str):
    try:
        event_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return event_time.strftime("%Y-%m-%d %I:%M %p UTC")
    except:
        return "Unknown Date"

# ✅ Corrected Profit Calculation using Decimal Odds
def calculate_bets_and_profit(home_odds_american, away_odds_american, base_bet=50):
    # Convert American odds to decimal for calculations
    home_odds = american_to_decimal(home_odds_american)
    away_odds = american_to_decimal(away_odds_american)

    bet1 = base_bet
    bet2 = (bet1 * home_odds) / away_odds
    total_bet = bet1 + bet2
    total_payout = min(bet1 * home_odds, bet2 * away_odds)  # Ensure correct profit
    profit = total_payout - total_bet
    profit_percentage = (profit / total_bet) * 100 if total_bet > 0 else 0

    return round(bet1, 2), round(bet2, 2), round(total_bet, 2), round(profit, 2), round(profit_percentage, 2)

def fetch_aofs(bet_amount=50.00):
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
                bet1, bet2, total_bet, profit, profit_percentage = calculate_bets_and_profit(best_home_odds, best_away_odds, bet_amount)

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
                    "arb_percentage": profit_percentage,
                    "bet1": bet1,
                    "bet2": bet2,
                    "total_investment": total_bet,
                    "guaranteed_profit": profit,
                    "bet_status": placed_bets.get(bet_key, "Not Placed")
                })

        # ✅ Sort by highest profit percentage and show top 20 AOFs
        return sorted(aof_list, key=lambda x: x["arb_percentage"], reverse=True)[:20]
    else:
        return []

@app.route("/", methods=["GET"])
def index():
    aofs = fetch_aofs()
    return render_template("index.html", aofs=aofs)

@app.route("/mark_bet/<bet_type>/<bet_key>", methods=["POST"])
def mark_bet(bet_type, bet_key):
    placed_bets[bet_key] = f"BET PLACED BY {bet_type.upper()}"
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
