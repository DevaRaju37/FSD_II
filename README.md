# CineBook — Movie Ticket Booking System

A full-stack academic mini project built with **Python Flask, MySQL, HTML, CSS and JavaScript**.

## Features
- User registration, login and logout (passwords stored as secure hashes)
- Movie catalogue and movie details
- Theatre/showtime listing
- Interactive seat selection with booked-seat indication
- Booking confirmation and booking history
- Demo payment flow (no real money or payment gateway)
- Admin dashboard to add movies, hide/show movies and add shows
- Parameterized SQL queries and basic role-based access control

## Project structure
```text
movie_ticket_booking/
├── app.py
├── requirements.txt
├── schema.sql
├── seed_admin.py
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── movie.html
│   ├── seats.html
│   ├── login.html
│   ├── register.html
│   ├── confirmation.html
│   ├── bookings.html
│   ├── admin.html
│   └── error.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Requirements
- Python 3.10+
- MySQL Server 8+
- A browser
- VS Code or another code editor

## Setup (Windows)
1. Install Python and MySQL Server. During MySQL setup, remember your root password.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment:
   ```bash
   py -m venv venv
   venv\\Scripts\\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   If `mysqlclient` fails to install on Windows, install the MySQL Connector/C build tools or use a compatible Python environment.
5. Open MySQL Workbench or MySQL command line and import `schema.sql`:
   ```bash
   mysql -u root -p < schema.sql
   ```
6. Set database environment variables in the same terminal (replace the password):
   ```powershell
   $env:MYSQL_HOST="localhost"
   $env:MYSQL_USER="root"
   $env:MYSQL_PASSWORD="YOUR_MYSQL_PASSWORD"
   $env:MYSQL_DB="movie_booking"
   $env:SECRET_KEY="replace-with-a-long-random-secret"
   ```
7. Create the sample admin account:
   ```bash
   python seed_admin.py
   ```
8. Start Flask:
   ```bash
   python app.py
   ```
9. Visit http://127.0.0.1:5000

## Demo accounts
- Admin: `admin@cinema.local` / `Admin@123` (created by `seed_admin.py`)
- User: register a new account from the website.

Change the sample admin password before using the project beyond a classroom demo.

## Linux / macOS setup
Activate the environment with `source venv/bin/activate`, install dependencies, import the SQL file using `mysql -u root -p < schema.sql`, export the environment variables, then run `python seed_admin.py` and `python app.py`.

## How booking works
1. A user opens a movie and chooses a show.
2. The seat page shows seats already included in confirmed bookings.
3. The user selects one or more available seats and submits.
4. The backend validates the selected seats and creates a booking and a successful **demo** payment record in a database transaction.
5. The confirmation page displays the ticket details.

The payment step is deliberately simulated. It does not connect to UPI, cards, wallets or a real payment provider.

## Important academic notes / limitations
- This is an intermediate mini-project starter, not a production ticketing platform.
- For a production deployment, add CSRF protection, email verification, rate limiting, secure cookie settings, real payment-provider verification, booking expiry/seat holds, cancellation/refund rules, logging, tests and deployment configuration.
- The sample poster URLs are placeholders/demo links; replace them with working image URLs or local images.
- The demo seat-locking transaction serializes booking requests by locking the show row. For production, use a more comprehensive reservation/hold model and database constraints that prevent the same seat being confirmed twice for a show.
