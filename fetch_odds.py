import requests
from datetime import datetime

# Your API key
API_KEY = "f1e5ca6d70e837026e976e7f5a94f058"
API_URL = "https://api.the-odds-api.com/v4/sports/upcoming/odds"

# Set parameters
params = {
    "apiKey": API_KEY,
    "regions": "us",  # Odds from US sportsbooks
    "markets": "h2h",  # Moneyline odds
}

# Maximum bet amount
MAX_BET = 100.00

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

# Function to calculate bet amounts based on a max bet of $100
def calculate_bets(home_odds, away_odds):
    bet1 = MAX_BET  # Set first bet to $100
    bet2 = round((bet1 * home_odds) / away_odds, 2)  # Calculate second bet
    total_investment = round(bet1 + bet2, 2)
    total_payout = round((bet2 * away_odds), 2)
    guaranteed_profit = round(total_payout - total_investment, 2)
    roi = round((guaranteed_profit / total_investment) * 100, 2)
    
    return bet1, bet2, total_investment, total_payout, guaranteed_profit, roi

# Function to fetch and display AOFs
def fetch_aofs(min_arb_percentage):
    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        print("\n✅ API Data Retrieved Successfully!\n")

        found_aof = False  # Track if any AOFs are found

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

            # Calculate Arbitrage Percentage
            arb_percentage = calculate_arbitrage(best_home_odds, best_away_odds)
            
            # Filter by Arbitrage Percentage
            if arb_percentage >= min_arb_percentage:
                found_aof = True
                bet1, bet2, total_investment, total_payout, guaranteed_profit, roi = calculate_bets(best_home_odds, best_away_odds)

                print("\n🔎 **Arbitrage Opportunity Found!**")
                print(f"🏆 **Match:** {game['home_team']} vs {game['away_team']} ({game['sport_title']})")
                print(f"📅 **Event Date:** {event_date}")
                print(f"💰 **Best Home Odds:** {best_home_odds} on {best_home_bookmaker}")
                print(f"💰 **Best Away Odds:** {best_away_odds} on {best_away_bookmaker}")
                print(f"📊 **Arbitrage Percentage:** {arb_percentage:.2f}%\n")
                
                print("📍 **Bet Breakdown:**")
                print(f"   - Bet **${bet1:.2f}** on **{game['home_team']}** at **{best_home_bookmaker}**")
                print(f"   - Bet **${bet2:.2f}** on **{game['away_team']}** at **{best_away_bookmaker}**\n")

                print(f"💵 **Guaranteed Profit:** ${guaranteed_profit:.2f}")
                print(f"📈 **ROI (Return on Investment):** {roi:.2f}%")
                print(f"🏦 **Total Investment:** ${total_investment:.2f}")
                print(f"🔄 **Total Payout:** ${total_payout:.2f}")
                print("=" * 60)

        if not found_aof:
            print("\n❌ No Arbitrage Opportunities Found for the given percentage.")

    else:
        print("❌ Error:", response.status_code, response.text)

# Main Loop - Keep refreshing until the user exits
while True:
    min_arb_percentage = float(input("\nEnter minimum Arbitrage Percentage to filter AOFs (e.g., 5 for 5%): "))
    fetch_aofs(min_arb_percentage)

    # Ask user if they want to refresh or exit
    action = input("\n🔄 Press [Enter] to refresh AOFs or type 'exit' to quit: ").strip().lower()
    if action == 'exit':
        print("\n👋 Exiting program. Have a great day!\n")
        break  # Exit the loop
