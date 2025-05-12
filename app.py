from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sqlite3
import os

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

    # Sorting logic
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
            df = pd.read_csv(file)
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

if __name__ == '__main__':
    if not os.path.exists('db'):
        os.makedirs('db')
    app.run(debug=True)
