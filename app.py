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
    session.clear()
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
            SELECT 
            bf.fare_amount, 
            b.bus_name, 
            pf.place_name AS from_place, 
            pt.place_name AS to_place, 
            b.travel_date
        FROM bus_fare bf
        JOIN bus b ON b.bus_id = bf.bus_id
        JOIN places pf ON b.from_place_id = pf.place_id
        JOIN places pt ON b.to_place_id = pt.place_id
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

    cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (session['user_name'],))
    user=cursor.fetchone()
    sql1= """
            INSERT INTO tickets (bus_id, user_id, travel_date, adult_count, child_count, infant_count, total_fare, booking_status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
    val1 = (
        bus_id, 
        user[0], 
        detail['travel_date'], 
        ticket[0]['adult_count'],
        ticket[0]['child_count'],
        ticket[0]['infant_count'],
        (ticket[0]['adult_count'] * detail['fare_amount']) + (ticket[0]['child_count'] * (detail['fare_amount'] // 2)),
        'Pending')
    cursor.execute(sql1, val1)
    db.commit()
    
    sql2 = """
            SELECT ticket_id 
            FROM tickets 
            WHERE bus_id = %s AND user_id = %s AND travel_date = %s AND booking_status = 'pending'
            """
    val2 = (bus_id, user[0], detail['travel_date'])

    cursor.execute(sql2, val2)
    ticket_id = cursor.fetchone()
    
    return render_template('ticketconf.html' , ticket = ticket, detail = detail, ticket_id = ticket_id[0])

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
        cursor.execute('SELECT place_name from places where place_id = %s',bus[2])
        bus_dict['from_place']=cursor.fetchone()[0]
        cursor.execute('SELECT place_name from places where place_id = %s',bus[3])
        bus_dict['to_place']=cursor.fetchone()[0]
        return render_template('bookticket.html', bus=bus_dict)
    
@app.route('/booking-success', methods=['POST'])
def booking_success():
    ticket_id = request.form.get('ticket_id') or request.args.get('ticket_id')
    if not ticket_id:
        return "Ticket ID missing", 400

    # Step 1: Get ticket details including passenger count and bus_id
    sql_ticket = """
        SELECT t.ticket_id, t.bus_id, t.adult_count, t.child_count, t.infant_count
        FROM tickets t
        WHERE t.ticket_id = %s AND t.booking_status = 'pending' 
    """
    cursor.execute(sql_ticket, (ticket_id,))
    ticket_row = cursor.fetchone()

    if not ticket_row:
        return "Ticket not found or already confirmed", 404

    bus_id = ticket_row[1]
    total_passengers = ticket_row[2] + ticket_row[3] + ticket_row[4]

    # Step 2: Get available seats for the bus
    sql_bus = "SELECT available_seats FROM bus WHERE bus_id = %s"
    cursor.execute(sql_bus, (bus_id,))
    bus_row = cursor.fetchone()
    if not bus_row:
        return "Bus not found", 404

    available_seats = bus_row[0]
    # Step 3: Check seat availability
    if total_passengers >= available_seats:
        flash("Not enough seats available. Please try another bus or date.")
        return redirect(url_for('home'))  
    
    # Step 4: Update ticket to confirmed
    sql_update_ticket = """
        UPDATE tickets 
        SET booking_status = 'confirmed' 
        WHERE ticket_id = %s AND booking_status = 'pending'
    """
    cursor.execute(sql_update_ticket, (ticket_id,))

    # Step 5: Reduce available seats in the bus table
    sql_update_seats = """
        UPDATE bus 
        SET available_seats = available_seats - %s 
        WHERE bus_id = %s
    """
    cursor.execute(sql_update_seats, (total_passengers, bus_id))

    db.commit()

    # Step 6: Get final details to display in success page
    sql2 = """
        SELECT t.ticket_id, u.user_name, b.bus_name, pf.place_name, pt.place_name, t.travel_date,
               (t.adult_count * bf.fare_amount + t.child_count * (bf.fare_amount / 2)) AS total_fare
        FROM tickets t
        JOIN users u ON t.user_id = u.user_id
        JOIN bus b ON t.bus_id = b.bus_id
        JOIN bus_fare bf ON bf.bus_id = b.bus_id
        JOIN places pf ON b.from_place_id = pf.place_id
        JOIN places pt ON b.to_place_id = pt.place_id
        WHERE t.ticket_id = %s;
    """
    cursor.execute(sql2, (ticket_id,))
    row = cursor.fetchone()

    if row:
        ticket = {
            "ticket_id": row[0],
            "user_name": row[1],
            "total_fare": int(row[6])
        }
        detail = {
            "bus_name": row[2],
            "from_place": row[3],
            "to_place": row[4],
            "travel_date": row[5]
        }
        return render_template('success.html', ticket=ticket, detail=detail)
    else:
        return "Ticket not found after update", 404

@app.route('/ticket-tracking', methods=['GET'])
def ticket_tracking():
    sql = """
        SELECT 
            t.ticket_id,
            t.travel_date,
            t.booking_status,
            u.user_name,
            pf.place_name AS from_place,
            pt.place_name AS to_place
        FROM tickets t
        JOIN users u ON t.user_id = u.user_id
        JOIN bus b ON t.bus_id = b.bus_id
        JOIN places pf ON b.from_place_id = pf.place_id
        JOIN places pt ON b.to_place_id = pt.place_id
        where u.user_name=  %s
    """
    val=(session.get('user_name'),)
    cursor.execute(sql,val)
    tickets = cursor.fetchall()

    ticket_list = []
    for ticket in tickets:
        ticket_list.append({
            'ticket_id': ticket[0],
            'travel_date': ticket[1],
            'booking_status': ticket[2],
            'user_name': ticket[3],
            'from_place': ticket[4],
            'to_place': ticket[5]
        })
    return render_template('tickettrack.html', tickets=ticket_list)

if __name__ == '__main__':
    app.run(debug=True)
