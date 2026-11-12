import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from MySQLdb import IntegrityError

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-development-secret")

app.config.update(
    MYSQL_HOST=os.getenv("MYSQL_HOST", "localhost"),
    MYSQL_USER=os.getenv("MYSQL_USER", "root"),
    MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD", ""),
    MYSQL_DB=os.getenv("MYSQL_DB", "movie_booking"),
    MYSQL_CURSORCLASS="DictCursor"
)
mysql = MySQL(app)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    return {"current_user": session.get("name"), "is_admin": session.get("role") == "admin"}

@app.route("/")
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies WHERE is_active=1 ORDER BY id DESC")
    movies = cur.fetchall()
    cur.close()
    return render_template("index.html", movies=movies)

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies WHERE id=%s AND is_active=1", (movie_id,))
    movie = cur.fetchone()
    if not movie:
        cur.close()
        abort(404)
    cur.execute("""
        SELECT s.id, s.show_date, s.show_time, s.price, t.name AS theatre_name,
               t.location,
               (SELECT COUNT(*) FROM seats st WHERE st.theatre_id=t.id) AS total_seats,
               (SELECT COUNT(*) FROM booking_seats bs JOIN bookings b ON b.id=bs.booking_id
                WHERE b.show_id=s.id AND b.status='CONFIRMED') AS booked_seats
        FROM shows s JOIN theatres t ON t.id=s.theatre_id
        WHERE s.movie_id=%s AND s.show_date >= CURDATE()
        ORDER BY s.show_date, s.show_time
    """, (movie_id,))
    shows = cur.fetchall()
    cur.close()
    return render_template("movie.html", movie=movie, shows=shows)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must contain at least 6 characters.", "danger")
            return render_template("register.html")
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s)",
                        (name, email, generate_password_hash(password)))
            mysql.connection.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            mysql.connection.rollback()
            flash("That email is already registered.", "danger")
        finally:
            cur.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        cur = mysql.connection.cursor()
        cur.execute("SELECT id,name,email,password_hash,role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            flash("Welcome back, " + user["name"] + "!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/show/<int:show_id>/seats")
def seats(show_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT s.id,s.show_date,s.show_time,s.price,m.title,t.name AS theatre_name,t.location
        FROM shows s JOIN movies m ON m.id=s.movie_id JOIN theatres t ON t.id=s.theatre_id
        WHERE s.id=%s
    """, (show_id,))
    show = cur.fetchone()
    if not show:
        cur.close()
        abort(404)
    cur.execute("SELECT id,seat_number,seat_type FROM seats WHERE theatre_id=(SELECT theatre_id FROM shows WHERE id=%s) ORDER BY id", (show_id,))
    all_seats = cur.fetchall()
    cur.execute("""
        SELECT bs.seat_id FROM booking_seats bs JOIN bookings b ON b.id=bs.booking_id
        WHERE b.show_id=%s AND b.status='CONFIRMED'
    """, (show_id,))
    booked = {row["seat_id"] for row in cur.fetchall()}
    cur.close()
    return render_template("seats.html", show=show, seats=all_seats, booked=booked)

@app.route("/book/<int:show_id>", methods=["POST"])
@login_required
def book(show_id):
    selected = request.form.getlist("seats")
    if not selected:
        flash("Select at least one seat.", "warning")
        return redirect(url_for("seats", show_id=show_id))
    try:
        seat_ids = sorted({int(x) for x in selected})
    except ValueError:
        abort(400)
    cur = mysql.connection.cursor()
    try:
        # Lock the show row so simultaneous booking attempts are serialized.
        cur.execute("SELECT id,theatre_id,price FROM shows WHERE id=%s FOR UPDATE", (show_id,))
        show = cur.fetchone()
        if not show:
            abort(404)
        placeholders = ",".join(["%s"] * len(seat_ids))
        cur.execute(f"SELECT id FROM seats WHERE theatre_id=%s AND id IN ({placeholders}) FOR UPDATE",
                    tuple([show["theatre_id"]] + seat_ids))
        valid_ids = {r["id"] for r in cur.fetchall()}
        if valid_ids != set(seat_ids):
            raise ValueError("One or more selected seats are invalid.")
        cur.execute("""
            SELECT bs.seat_id FROM booking_seats bs JOIN bookings b ON b.id=bs.booking_id
            WHERE b.show_id=%s AND b.status='CONFIRMED' AND bs.seat_id IN (
                """ + placeholders + ") FOR UPDATE", tuple([show_id] + seat_ids))
        if cur.fetchall():
            raise ValueError("One or more seats were just booked. Please choose again.")
        total = float(show["price"]) * len(seat_ids)
        cur.execute("INSERT INTO bookings(user_id,show_id,total_amount,status) VALUES(%s,%s,%s,'PENDING')",
                    (session["user_id"], show_id, total))
        booking_id = cur.lastrowid
        for seat_id in seat_ids:
            cur.execute("INSERT INTO booking_seats(booking_id,seat_id) VALUES(%s,%s)", (booking_id, seat_id))
        cur.execute("INSERT INTO payments(booking_id,amount,payment_method,status) VALUES(%s,%s,'DEMO','SUCCESS')",
                    (booking_id, total))
        cur.execute("UPDATE bookings SET status='CONFIRMED' WHERE id=%s", (booking_id,))
        mysql.connection.commit()
        return redirect(url_for("booking_confirmation", booking_id=booking_id))
    except (ValueError, IntegrityError) as exc:
        mysql.connection.rollback()
        flash(str(exc) or "Those seats are no longer available.", "danger")
        return redirect(url_for("seats", show_id=show_id))
    except Exception:
        mysql.connection.rollback()
        raise
    finally:
        cur.close()

@app.route("/booking/<int:booking_id>")
@login_required
def booking_confirmation(booking_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.id,b.total_amount,b.status,b.created_at,m.title,s.show_date,s.show_time,
               t.name AS theatre_name,t.location,u.name AS customer_name,
               GROUP_CONCAT(st.seat_number ORDER BY st.seat_number SEPARATOR ', ') AS seat_numbers
        FROM bookings b JOIN shows s ON s.id=b.show_id
        JOIN movies m ON m.id=s.movie_id JOIN theatres t ON t.id=s.theatre_id
        JOIN users u ON u.id=b.user_id
        JOIN booking_seats bs ON bs.booking_id=b.id JOIN seats st ON st.id=bs.seat_id
        WHERE b.id=%s AND b.user_id=%s GROUP BY b.id
    """, (booking_id, session["user_id"]))
    booking = cur.fetchone()
    cur.close()
    if not booking:
        abort(404)
    return render_template("confirmation.html", booking=booking)

@app.route("/my-bookings")
@login_required
def my_bookings():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.id,b.total_amount,b.status,b.created_at,m.title,s.show_date,s.show_time,
               t.name AS theatre_name,
               GROUP_CONCAT(st.seat_number ORDER BY st.seat_number SEPARATOR ', ') AS seat_numbers
        FROM bookings b JOIN shows s ON s.id=b.show_id
        JOIN movies m ON m.id=s.movie_id JOIN theatres t ON t.id=s.theatre_id
        JOIN booking_seats bs ON bs.booking_id=b.id JOIN seats st ON st.id=bs.seat_id
        WHERE b.user_id=%s GROUP BY b.id ORDER BY b.created_at DESC
    """, (session["user_id"],))
    bookings = cur.fetchall()
    cur.close()
    return render_template("bookings.html", bookings=bookings)

@app.route("/admin")
@login_required
@admin_required
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies ORDER BY id DESC")
    movies = cur.fetchall()
    cur.execute("""
        SELECT s.id,m.title,t.name AS theatre_name,s.show_date,s.show_time,s.price
        FROM shows s JOIN movies m ON m.id=s.movie_id JOIN theatres t ON t.id=s.theatre_id
        ORDER BY s.show_date DESC,s.show_time
    """)
    shows = cur.fetchall()
    cur.close()
    return render_template("admin.html", movies=movies, shows=shows)

@app.route("/admin/movie/add", methods=["POST"])
@login_required
@admin_required
def add_movie():
    data = (request.form.get("title","").strip(), request.form.get("genre","").strip(),
            request.form.get("duration","").strip(), request.form.get("language","").strip(),
            request.form.get("rating","").strip(), request.form.get("description","").strip(),
            request.form.get("poster_url","").strip())
    if not data[0]:
        flash("Movie title is required.", "danger")
    else:
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO movies(title,genre,duration,language,rating,description,poster_url)
                       VALUES(%s,%s,%s,%s,%s,%s,%s)""", data)
        mysql.connection.commit()
        cur.close()
        flash("Movie added.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/movie/<int:movie_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_movie(movie_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE movies SET is_active=1-is_active WHERE id=%s", (movie_id,))
    mysql.connection.commit()
    cur.close()
    flash("Movie visibility updated.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/show/add", methods=["POST"])
@login_required
@admin_required
def add_show():
    try:
        movie_id = int(request.form["movie_id"])
        theatre_id = int(request.form["theatre_id"])
        show_date = request.form["show_date"]
        show_time = request.form["show_time"]
        price = float(request.form["price"])
        if price <= 0:
            raise ValueError()
    except (ValueError, KeyError):
        flash("Enter valid show details.", "danger")
        return redirect(url_for("admin"))
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO shows(movie_id,theatre_id,show_date,show_time,price) VALUES(%s,%s,%s,%s,%s)",
                (movie_id,theatre_id,show_date,show_time,price))
    mysql.connection.commit()
    cur.close()
    flash("Show added.", "success")
    return redirect(url_for("admin"))

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page or record was not found."), 404

if __name__ == "__main__":
    app.run(debug=True)
