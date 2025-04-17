from flask import Flask, request, render_template, redirect, url_for,flash,session
import pymysql
from datetime import date

app = Flask(__name__)

db = pymysql.connect(
    host="127.0.0.1",       
    user="root",
    password="tamilRAJAN@01",
    database="bus_booking"  
)

cursor = db.cursor()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def home():
    cursor.execute("SELECT place_name FROM places")
    places = [row[0] for row in cursor.fetchall()]
    today = date.today().isoformat()  # gives "YYYY-MM-DD"
    return render_template('home.html', places=places, today=today)

@app.route('/login', methods=['GET','POST'])
def login_user():
    if request.method == 'POST':
        user_email = request.form['user-email']
        user_password = request.form['user-password']
        sql = "SELECT * FROM users WHERE user_email = %s AND user_password = %s"
        val = (user_email, user_password)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result:
            session['user_logged_in'] = True
            session['user_name'] = result[1] 
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"
    elif request.method == 'GET':
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_logged_in', None)
    return redirect(url_for('home'))


@app.route('/signup', methods=['GET','POST'])
def signup_user():
    if request.method == 'POST':
        user_name = request.form['user-name']
        user_email = request.form['user-email']
        user_number = request.form['user-number']
        user_password = request.form['user-password']

        sql = "INSERT INTO users (user_name, user_email,user_number, user_password) VALUES (%s, %s, %s, %s)"
        val = (user_name, user_email, user_number,user_password)
        cursor.execute(sql, val)
        db.commit()
        return redirect(url_for('login_user'))
    
    elif request.method == 'GET':
        return render_template('signup.html')

@app.route('/bus-route', methods=['GET', 'POST'])
def bus_route():
    if not session.get('user_logged_in'):
        return redirect(url_for('login_user'))

    if request.method == 'GET':
        cursor.execute("SELECT place_name FROM places")
        all_places = [row[0] for row in cursor.fetchall()]
        return render_template('bookticket.html', places=all_places)

    elif request.method == 'POST':
        bus_from = request.form['from-station']
        bus_to = request.form['to-station']
        travel_date = request.form['travel-date']
        print(travel_date)
        sql = """
            SELECT b.bus_id, b.bus_name, 
                p1.place_name AS from_place, 
                p2.place_name AS to_place, 
                b.departure_time, b.arrival_time, 
                bf.fare_amount,
                b.available_seats
            FROM bus AS b
            JOIN places AS p1 ON b.from_place_id = p1.place_id
            JOIN places AS p2 ON b.to_place_id = p2.place_id
            JOIN bus_fare AS bf ON b.bus_id = bf.bus_id
            WHERE p1.place_name = %s AND p2.place_name = %s AND b.travel_date = %s;
        """

        val = (bus_from, bus_to, travel_date)
        cursor.execute(sql, val)
        buses = cursor.fetchall()

        bus_list = []
        for bus in buses:
            bus_list.append({
                'id': bus[0],
                'name': bus[1],
                'from': bus[2],
                'to': bus[3],
                'departure_time': bus[4],
                'arrival_time': bus[5],
                'price': bus[6],
                'available_seats': bus[7]
            })
        return render_template('busroute.html', buses=bus_list)


@app.route('/ticket-confirmation/<int:bus_id>', methods=['POST'])
def ticket_confirmation(bus_id): 
    ticket = [{
        "bus_id" : bus_id,
        "user_name" : request.form['user-name'],
        "user_age" : request.form['user-age'],
        "user_gender" : request.form['user-gender'],
        "adult_count" : int(request.form['adult-count']),
        "child_count" : int(request.form['child-count']),
        "infant_count" : int(request.form['infant-count']),
    }]

    sql = """
            SELECT bf.fare_amount, b.bus_name, bf.from_place, bf.to_place, b.travel_date
            FROM bus_fare bf
            join bus b
            on b.bus_id = bf.bus_id
            WHERE bf.bus_id = %s;
        """
    val = (bus_id,)
    cursor.execute(sql, val)
    row = cursor.fetchone()

    detail = {
    'fare_amount': row[0],
    'bus_name': row[1],
    'from_place': row[2],
    'to_place': row[3],
    'travel_date': row[4],
    'adult_fare': row[0] ,
    'child_fare': row[0] //2,
    }

    sql1= """
            INSERT INTO tickets (bus_id, user_name, travel_date, adult_count, child_count, infant_count, total_fare, booking_status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
    val1 = (
        bus_id, 
        ticket[0]['user_name'], 
        detail['travel_date'], 
        ticket[0]['adult_count'],
        ticket[0]['child_count'],
        ticket[0]['infant_count'],
        (ticket[0]['adult_count'] * detail['fare_amount']) + (ticket[0]['child_count'] * (detail['fare_amount'] // 2)),
        'Pending')
    cursor.execute(sql1, val1)
    db.commit()
    
    return render_template('ticketconf.html' , ticket = ticket, detail = detail)

@app.route('/book_ticket/<int:bus_id>', methods=['GET'])
def book_ticket(bus_id):
    if request.method == 'GET':
        sql = "SELECT * FROM bus WHERE bus_id = %s"
        val = (bus_id,)
        cursor.execute(sql, val)
        bus = cursor.fetchone()

        bus_dict = {
            'bus_id': bus[0],
            'bus_name': bus[1],  
            'from_place': bus[2],
            'to_place': bus[3],
            'departure_time': bus[4],
            'arrival_time': bus[5],
            'price': bus[6]
        }
        return render_template('bookticket.html', bus=bus_dict)
    
@app.route('/booking-success', methods=['POST'])
def booking_success(bus_id):
    sql = "ALTER TABLE tickets" 
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
