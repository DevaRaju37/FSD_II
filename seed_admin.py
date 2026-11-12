"""Run once after importing schema.sql: python seed_admin.py"""
import os
from werkzeug.security import generate_password_hash
import MySQLdb

db = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST","localhost"),
    user=os.getenv("MYSQL_USER","root"),
    passwd=os.getenv("MYSQL_PASSWORD",""),
    db=os.getenv("MYSQL_DB","movie_booking")
)
cur = db.cursor()
cur.execute(
    "INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'admin') "
    "ON DUPLICATE KEY UPDATE role='admin'",
    ("Cinema Admin","admin@cinema.local",generate_password_hash("Admin@123"))
)
db.commit()
cur.close()
db.close()
print("Admin account ready: admin@cinema.local / Admin@123")
print("Change this password after first login.")
