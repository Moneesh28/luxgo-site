from flask import Flask, render_template, request, redirect, flash, send_file, session, url_for
import sqlite3
import os
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'luxgo_secret_key'

# Hardcoded admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Initialize DB if not exists
def init_db():
    if not os.path.exists('luxgo.db'):
        conn = sqlite3.connect('luxgo.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                pickup_location TEXT NOT NULL,
                drop_location TEXT NOT NULL,
                pickup_date TEXT NOT NULL,
                return_date TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/export')
def export_data():
    conn = sqlite3.connect('luxgo.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(output, mimetype='text/csv', download_name='luxgo_bookings.csv', as_attachment=True)

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        pickup_location = request.form['pickup_location']
        drop_location = request.form['drop_location']
        pickup_date = request.form['pickup_date']
        return_date = request.form['return_date']

        if not name or not email or not phone:
            flash("Please fill all required fields.")
            return redirect('/form')

        conn = sqlite3.connect('luxgo.db')
        c = conn.cursor()
        c.execute("INSERT INTO bookings (name, email, phone, pickup_location, drop_location, pickup_date, return_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (name, email, phone, pickup_location, drop_location, pickup_date, return_date))
        conn.commit()
        conn.close()

        flash("Thank you for booking! We will contact you soon.")
        return redirect('/form')  # Redirecting to the form page again


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            flash("Invalid credentials. Please try again.")
            return redirect('/admin_login')

    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')

    conn = sqlite3.connect('luxgo.db')
    c = conn.cursor()
    c.execute("SELECT * FROM bookings")
    data = c.fetchall()
    conn.close()
    return render_template('admin.html', bookings=data)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_booking(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')

    conn = sqlite3.connect('luxgo.db')
    c = conn.cursor()
    c.execute("DELETE FROM bookings WHERE id = ?", (id,))
    conn.commit()

    # Reset the auto-increment ID sequence
    c.execute("DELETE FROM sqlite_sequence WHERE name='bookings'")
    conn.commit()

    conn.close()
    flash("Booking deleted successfully.")
    return redirect('/admin')  # Ensure this redirects to the admin page



@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
