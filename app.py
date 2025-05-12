from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import sqlite3
from io import BytesIO
import os
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'db/database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def dashboard():
    month = request.args.get('month')
    sort = request.args.get('sort')

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    if month:
        df = df[df['date'].dt.strftime('%Y-%m') == month]

    summary = df.groupby('category')['amount'].sum().reset_index()

    if sort == 'category_asc':
        summary = summary.sort_values(by='category')
    elif sort == 'amount_asc':
        summary = summary.sort_values(by='amount')
    elif sort == 'amount_desc':
        summary = summary.sort_values(by='amount', ascending=False)
    else:
        summary = summary.sort_values(by='amount', ascending=False)

    total_spent = df['amount'].sum()
    summary_list = summary.values.tolist()

    all_months = df['date'].dt.strftime('%Y-%m').dropna().unique().tolist()
    all_months.sort(reverse=True)

    return render_template(
        'dashboard.html',
        summary=summary_list,
        total=total_spent,
        all_months=all_months,
        selected_month=month,
        sort=sort
    )

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            df = pd.read_(file)
            conn = get_db_connection()
            df.to_sql('transactions', conn, if_exists='append', index=False)
            conn.close()
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

@app.route('/clear', methods=['POST'])
def clear_data():
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/report')
def monthly_report():
    month = request.args.get('month')
    if not month:
        return "Month parameter is required, e.g., /report?month=2025-04"

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[df['date'].dt.strftime('%Y-%m') == month]

    if df.empty:
        return f"No transactions found for {month}"

    # Prepare report table
    report_df = df.groupby('category')['amount'].sum().reset_index()
    report_df.columns = ['Category', 'Total Spent']
    report_df['Total Spent'] = report_df['Total Spent'].round(2)
    report_df['% of Total'] = (report_df['Total Spent'] / report_df['Total Spent'].sum() * 100).round(2)

    # Custom header
    friendly_month = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    header_line = f"SpendScope Monthly Report - {friendly_month}"

    # Convert to CSV with header
    csv_bytes = BytesIO()
    csv_bytes.write((header_line + "\n\n").encode('utf-8'))
    report_df.to_csv(csv_bytes, index=False)
    csv_bytes.seek(0)

    filename = f"SpendScope_{month}_Report.csv"
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    if not os.path.exists('db'):
        os.makedirs('db')
    app.run(debug=True)
