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

from pytz import timezone, utc

def format_event_date(date_str):
    try:
        event_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        event_time = event_time.astimezone(timezone("America/Chicago"))  # Convert to Central Time
        return event_time.strftime("%Y-%m-%d %I:%M %p CT")  # Show as Central Time
    except:
        return "Unknown Date"


# ✅ Last Working Version of Total Profit Calculation
def calculate_bets_and_profit(home_odds, away_odds, base_bet=50):
    bet1 = base_bet
    bet2 = (bet1 * home_odds) / away_odds
    total_bet = bet1 + bet2
    total_payout = min(bet1 * home_odds, bet2 * away_odds)  # ✅ Using minimum payout for profit calculation
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
            event_date = format_event_date(game.get('commence_time', ''))

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
                    "home_odds": round(best_home_odds, 2),
                    "home_bookmaker": best_home_bookmaker,
                    "away_odds": round(best_away_odds, 2),
                    "away_bookmaker": best_away_bookmaker,
                    "arb_percentage": profit_percentage,
                    "bet1": bet1,
                    "bet2": bet2,
                    "total_investment": total_bet,
                    "guaranteed_profit": profit,
                    "bet_status": placed_bets.get(bet_key, "Not Placed")
                })

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
