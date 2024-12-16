import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# Define hourly rates for each client
HOURLY_RATES = {
    'Amanda': 20,
    'Heidi': 24
}

# Define working days for each client
WORK_SCHEDULE = {
    'Amanda': ['Monday', 'Tuesday', 'Wednesday', 'Friday'],
    'Heidi': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
}

# Load work hours from the Excel file
def load_work_hours(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Day", "Hours Worked", "Client", "Earnings"])

# Log new work hours into the Excel file and calculate earnings
def log_hours(file_path, date, hours, client):
    if client not in HOURLY_RATES or client not in WORK_SCHEDULE:
        raise ValueError(f"Client '{client}' not found in rates or schedule.")

    date_obj = datetime.strptime(date, '%Y-%m-%d')
    day_of_week = date_obj.strftime('%A')

    if day_of_week not in WORK_SCHEDULE[client]:
        raise ValueError(f"{client} does not work on {day_of_week}. Please choose a valid day.")

    earnings = hours * HOURLY_RATES[client]
    new_entry = pd.DataFrame({
        "Date": [date],
        "Day": [day_of_week],
        "Hours Worked": [hours],
        "Client": [client],
        "Earnings": [earnings]
    })

    df = load_work_hours(file_path)
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_excel(file_path, index=False)

# Delete a work hour entry by index
def delete_hours(file_path, index):
    df = load_work_hours(file_path)
    if index < len(df):
        df = df.drop(index)
        df.reset_index(drop=True, inplace=True)
        df.to_excel(file_path, index=False)

@app.route('/')
def home():
    work_hours = load_work_hours('work_hours.xlsx')
    if work_hours.empty:
        return render_template('index.html', tables=None, work_hours=None)

    table_html = work_hours.to_html(classes='data', header="true", index=True, escape=False)
    return render_template('index.html', tables=table_html, work_hours=work_hours)

# Route to handle logging hours from a form
@app.route('/log', methods=['POST'])
def log():
    date = request.form['date']
    hours = float(request.form['hours'])
    client = request.form['client']
    
    try:
        log_hours('work_hours.xlsx', date, hours, client)
    except ValueError as e:
        return str(e), 400
    
    return redirect(url_for('home'))

# Route to delete an entry
@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    delete_hours('work_hours.xlsx', index)
    return redirect(url_for('home'))

# Route to display the weekly summary
@app.route('/weekly_summary')
def weekly_summary():
    work_hours = load_work_hours('work_hours.xlsx')

    if work_hours.empty:
        return "No data available for weekly summary."

    work_hours['Date'] = pd.to_datetime(work_hours['Date'])
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())

    weekly_data = work_hours[work_hours['Date'] >= start_of_week]
    print("Filtered weekly data:", weekly_data)  # Debug print

    if weekly_data.empty:
        return "No data found for the current week."

    summary = weekly_data.groupby('Client').agg({
        'Hours Worked': 'sum',
        'Earnings': 'sum'
    }).reset_index()
    summary.columns = ['Client', 'Total Hours', 'Total Earnings']
    print("Summary Data:", summary)  # Debug print

    return render_template('summary.html', total_hours=summary)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
