from flask import Flask, render_template, request, redirect, session
from db import get_connection  # make sure this returns a MySQL connection

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user"])

# ---------------- ROOMS ----------------
@app.route("/rooms", methods=["GET", "POST"])
def rooms():
    if "user" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        room_number = request.form["room_number"]
        room_type = request.form["room_type"]
        price = request.form["price"]

        cursor.execute(
            "INSERT INTO rooms (room_number, room_type, price, status) VALUES (%s, %s, %s, 'available')",
            (room_number, room_type, price)
        )
        conn.commit()

    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()
    conn.close()

    return render_template("rooms.html", rooms=rooms)

# ---------------- BOOKING ----------------
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "user" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch available rooms
    cursor.execute("SELECT * FROM rooms WHERE status='available'")
    rooms = cursor.fetchall()

    # Debug: check what rooms are fetched
    print("Rooms:", rooms)

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        id_proof = request.form["id_proof"]
        room_id = request.form["room_id"]
        check_in = request.form["check_in"]
        check_out = request.form["check_out"]
        total_amount = request.form["total_amount"]

        # Insert customer
        cursor.execute(
            "INSERT INTO customers (name, phone, id_proof) VALUES (%s, %s, %s)",
            (name, phone, id_proof)
        )
        customer_id = cursor.lastrowid

        # Insert booking
        cursor.execute(
            "INSERT INTO bookings (customer_id, room_id, check_in, check_out, total_amount) "
            "VALUES (%s, %s, %s, %s, %s)",
            (customer_id, room_id, check_in, check_out, total_amount)
        )

        # Update room status
        cursor.execute(
            "UPDATE rooms SET status='occupied' WHERE id=%s",
            (room_id,)
        )

        conn.commit()
        conn.close()
        return "Booking successful!"

    conn.close()
    return render_template("booking.html", rooms=rooms)

# ---------------- VIEW BOOKINGS ----------------
@app.route("/view_bookings")
def view_bookings():
    if "user" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Show only active bookings
    cursor.execute("""
        SELECT b.id AS booking_id, c.name AS customer_name, c.phone, r.room_number, r.room_type,
               b.check_in, b.check_out, b.total_amount
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN rooms r ON b.room_id = r.id
        WHERE b.status='active'
    """)
    bookings = cursor.fetchall()
    conn.close()

    return render_template("view_bookings.html", bookings=bookings)


# ---------------- CHECK-OUT ----------------
@app.route("/checkout/<int:booking_id>")
def checkout(booking_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the room associated with this booking
    cursor.execute("SELECT room_id FROM bookings WHERE id=%s", (booking_id,))
    booking = cursor.fetchone()

    if booking:
        room_id = booking['room_id']

        # Free the room
        cursor.execute("UPDATE rooms SET status='available' WHERE id=%s", (room_id,))

        # Mark booking as completed
        cursor.execute(
            "UPDATE bookings SET status='completed' WHERE id=%s", (booking_id,)
        )

        conn.commit()

    conn.close()
    return redirect("/view_bookings")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
