import requests
from flask import Flask
import webbrowser
import threading
import time
from datetime import datetime
import pygal
from pygal.style import LightColorizedStyle
import os

def fetch_stock_data(symbol, function):
    API_KEY = "710QOQG2JW67UPY0"
    BASE_URL = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY,
        "datatype": "json"
    }
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = "60min"
    response = requests.get(BASE_URL, params=params)
    return response.json() if response.status_code == 200 else None

def get_stock_symbol():
    print("\nStock Data Visualizer\n----------------------\n")
    while True:
        symbol = input("Enter the stock symbol you are looking for: ").upper()
        data = fetch_stock_data(symbol, "GLOBAL_QUOTE")
        
        if (
            data
            and "Global Quote" in data
            and data["Global Quote"].get("01. symbol")
            and data["Global Quote"].get("05. price") not in [None, "", "0.0000"]
        ):
            return symbol

        print("Invalid stock symbol or no data available. Please try again.\n")


def get_chart_type():
    print("\nChart Types\n-----------\n1. Bar\n2. Line")
    while True:
        choice = input("Enter the chart type you want (1, 2): ")
        if choice == "1": return "Bar"
        if choice == "2": return "Line"
        print("Invalid choice. Please enter 1 for Bar or 2 for Line.\n")

def get_time_series():
    print("\nSelect the Time Series\n----------------------\n1. Intraday\n2. Daily\n3. Weekly\n4. Monthly")
    while True:
        choice = input("Enter the option (1, 2, 3, 4): ")
        if choice == "1": return "TIME_SERIES_INTRADAY"
        if choice == "2": return "TIME_SERIES_DAILY"
        if choice == "3": return "TIME_SERIES_WEEKLY"
        if choice == "4": return "TIME_SERIES_MONTHLY"
        print("Invalid choice. Please enter 1, 2, 3, or 4.\n")

def get_date(prompt):
    while True:
        date_str = input(prompt)
        try:
            entered_date = datetime.strptime(date_str, "%Y-%m-%d")
            if entered_date > datetime.now():
                print("The date cannot be in the future.")
                continue
            return entered_date
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

def get_date_range():
    while True:
        start = get_date("Enter the start date (YYYY-MM-DD): ")
        end = get_date("Enter the end date (YYYY-MM-DD): ")
        if start <= end:
            return start, end
        print("End date cannot be before start date.\n")

app = Flask(__name__)
user_data = {}

@app.route('/')
def show_results():
    stock_data = fetch_stock_data(user_data['symbol'], user_data['time_series'])

    if not stock_data:
        return "<h1>Error loading stock data.</h1>"

    if "Error Message" in stock_data:
        return f"<h1>API Error: {stock_data['Error Message']}</h1>"

    if "Note" in stock_data:
        return f"<h1>API Limit Reached: {stock_data['Note']}</h1>"

    time_series_key = next((k for k in stock_data if "Time Series" in k), None)
    if not time_series_key:
        return "<h1>Unexpected data format.</h1>"

    dates = []
    open_prices = []
    high_prices = []
    low_prices = []
    close_prices = []

    for date_str, values in sorted(stock_data[time_series_key].items()):
        try:
            date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            if user_data['start_date'] <= date <= user_data['end_date']:
                dates.append(date.strftime("%Y-%m-%d"))
                open_prices.append(float(values["1. open"]))
                high_prices.append(float(values["2. high"]))
                low_prices.append(float(values["3. low"]))
                close_prices.append(float(values["4. close"]))
        except:
            continue

    if not close_prices:
        return "<h1>No data in selected date range.</h1>"

    if user_data['chart_type'] == "Bar":
        chart = pygal.Bar(style=LightColorizedStyle, x_label_rotation=45, show_minor_x_labels=True)
    else:
        chart = pygal.Line(style=LightColorizedStyle, x_label_rotation=45, show_minor_x_labels=True)

    chart.title = f"{user_data['symbol']} Stock Data"

    num_labels = 10
    step = max(1, len(dates) // num_labels)

    chart.x_labels = dates[::step]
    chart.x_labels_major = dates[::step]
    chart.add("Open", open_prices)
    chart.add("High", high_prices)
    chart.add("Low", low_prices)
    chart.add("Close", close_prices)

    if not os.path.exists("static"):
        os.makedirs("static")

    chart.render_to_file("static/chart.svg")

    return f"""
    <h1>Stock Visualizer</h1>
    <div style="margin: 20px;">
        <p><strong>Symbol:</strong> {user_data['symbol']}</p>
        <p><strong>Date Range:</strong> {user_data['start_date'].strftime('%Y-%m-%d')} to {user_data['end_date'].strftime('%Y-%m-%d')}</p>
        <object type="image/svg+xml" data="/static/chart.svg" width="90%" height="500"></object>
    </div>
    """

def run_flask():
    app.run(host='0.0.0.0', port=5050)
    
def ask_test_another_stock():
    while True:
        another = input("\nWould you like to test another stock? (yes/no): ").lower()
        if another == "yes":
            return True
        elif another == "no":
            print("\nClosing the application...")
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

if __name__ == '__main__':
    while True:
    
        symbol = get_stock_symbol()
        chart_type = get_chart_type()
        time_series = get_time_series()
        start_date, end_date = get_date_range()

        user_data.update({
            'symbol': symbol,
            'chart_type': chart_type,
            'time_series': time_series,
            'start_date': start_date,
            'end_date': end_date
        })

        threading.Thread(target=run_flask, daemon=True).start()
        webbrowser.open_new("http://127.0.0.1:5050")

        if not ask_test_another_stock():
            break

        time.sleep(1)
        