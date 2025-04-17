from flask import Flask, request, render_template, redirect, url_for,flash
import pymysql

app = Flask(__name__)

db = pymysql.connect(
    host="127.0.0.1",       
    user="root",
    password="root",
    database="bus_booking"  
)

cursor = db.cursor()

@app.route('/')
def home():
    return render_template('home.html') 

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
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"
    elif request.method == 'GET':
        return render_template('login.html')

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

@app.route('/bus-route', methods=['GET','POST'])
def bus_route():
    if request.method == 'GET':
        return render_template('bookticket.html')
    elif request.method == 'POST':
        bus_from = request.form['from-station']
        bus_to = request.form['to-station']
        travel_date = request.form['travel-date']


        sql = """
                SELECT b.bus_id, b.bus_name, b.from_place, b.to_place, b.departure_time, b.arrival_time, bf.fare_amount,b.available_seats
                FROM bus b
                join bus_fare bf on b.bus_id = bf.bus_id
                WHERE b.from_place = %s AND b.to_place = %s AND b.travel_date = %s;
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
                'available_seats': bus[7] if bus[7] > 0 else 'No seats available'
            })
        return render_template('busroute.html', buses=bus_list)

@app.route('/ticket-confirmation/<int:bus_id>', methods=['POST'])
def ticket_confirmation(bus_id): 
    sql = "SELECT * FROM bus WHERE bus_id = %s"
    val = (bus_id,)
    cursor.execute(sql, val)
    bus = cursor.fetchone()

    bus_detail = {
        'bus_id': bus[0],
        'bus_name': bus[1],  
        'from_place': bus[2],
        'to_place': bus[3],
        'departure_time': bus[4],
        'arrival_time': bus[5],
        'price': bus[6]
    }

    ticket = [{
        "bus_id" : bus_id,
        "user_name" : request.form['user-name'],
        "user_age" : request.form['user-age'],
        "user_gender" : request.form['user-gender'],
        "adult_count" : int(request.form['adult-count']),
        "child_count" : int(request.form['child-count']),
        "infant_count" : int(request.form['infant-count']),

    }]
    total_seat = ticket[0]['adult_count'] + ticket[0]['child_count'] + ticket[0]['infant_count']
    sql = """
            SELECT bf.fare_amount, b.bus_name, bf.from_place, bf.to_place, b.travel_date
            FROM bus_fare bf
            join bus b
            on b.bus_id = bf.bus_id
            WHERE bf.from_place = %s and bf.to_place = %s;
        """
    val = (bus_detail['from_place'], bus_detail['to_place'])
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
            INSERT INTO tickets (bus_id, user_name, travel_date,from_place, to_place,  adult_count, child_count, infant_count, total_seat, total_fare, booking_status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
    val1 = (
        bus_id, 
        ticket[0]['user_name'], 
        detail['travel_date'], 
        detail['from_place'],
        detail['to_place'],
        ticket[0]['adult_count'],
        ticket[0]['child_count'],
        ticket[0]['infant_count'],
        total_seat,
        (ticket[0]['adult_count'] * detail['fare_amount']) + (ticket[0]['child_count'] * (detail['fare_amount'] // 2)),
        'Pending'
        )
    cursor.execute(sql1, val1)
    db.commit()

    sql2 = "SELECT ticket_id FROM tickets WHERE bus_id = %s AND user_name = %s AND travel_date = %s AND booking_status = 'Pending'"
    val2 = (bus_id, ticket[0]['user_name'], detail['travel_date']) 
    cursor.execute(sql2, val2)
    ticket_id = cursor.fetchone()
   
    return render_template('ticketconf.html' , ticket = ticket, detail = detail, ticket_id = ticket_id[0],bus_detail = bus_detail)

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
    
@app.route('/booking-success/<int:ticket_id>', methods=['POST'])
def booking_success(ticket_id):
    sql = "UPDATE tickets SET booking_status = 'Confirmed' WHERE ticket_id = %s and booking_status = 'Pending'" 
    val = (ticket_id,)
    cursor.execute(sql, val)
    db.commit()

    sql0 = """
            UPDATE bus
            SET available_seats = available_seats - (
                SELECT total_seat 
                FROM tickets 
                WHERE ticket_id = %s
            )
            WHERE bus_id = (
                SELECT bus_id 
                FROM tickets 
                WHERE ticket_id = %s 
            );

            """
    val0 = (ticket_id, ticket_id)
    cursor.execute(sql0, val0)
    db.commit()

    sql1 = """
            SELECT b.bus_name, b.from_place, b.to_place, b.travel_date, bf.fare_amount
            FROM tickets t
            JOIN bus b ON t.bus_id = b.bus_id
            JOIN bus_fare bf ON b.bus_id = bf.bus_id
            WHERE t.ticket_id = %s;
            """
    val1 = (ticket_id,)
    cursor.execute(sql1, val1)
    row = cursor.fetchone()

    detail = {
        'bus_name': row[0],
        'from_place': row[1],
        'to_place': row[2],
        'travel_date': row[3],
        'fare_amount': row[4]
    }

    sql2 = """
            SELECT * FROM tickets WHERE ticket_id = %s;
            """
    val2 = (ticket_id,)
    cursor.execute(sql2, val2)
    tickets = cursor.fetchall()
    ticket_list = []
    for ticket in tickets:
        ticket_list.append({
            'ticket_id': ticket[0],
            'bus_id': ticket[1],
            'user_name': ticket[2],
            'travel_date': ticket[3],
            'adult_count': ticket[4],
            'child_count': ticket[5],
            'infant_count': ticket[6],
            'total_fare': ticket[9],
            'booking_status': ticket[8]
        })
    return render_template('success.html', ticket=ticket_list[0], detail=detail)

@app.route('/ticket-tracking', methods=['GET'])
def ticket_tracking():
    if request.method == 'GET':
        sql = "SELECT * FROM tickets"
        cursor.execute(sql)
        tickets = cursor.fetchall()
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'ticket_id': ticket[0],
                'bus_id': ticket[1],
                'user_name': ticket[2],
                'travel_date': ticket[3],
                'from_place': ticket[4],
                'to_place': ticket[5],
                'adult_count': ticket[6],
                'child_count': ticket[7],
                'infant_count': ticket[8],
                'total_fare': ticket[10],
                'booking_status': ticket[9]
            })

        return render_template('tickettrack.html', tickets=ticket_list)
if __name__ == '__main__':
    app.run(debug=True)
