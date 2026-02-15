from flask import Flask, render_template, request, redirect
import mysql.connector
import redis
import os
import json
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "realestatebuddy-db")
REDIS_HOST = os.getenv("REDIS_HOST", "realestatebuddy-redis")

time.sleep(5)

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user="sanjay",
        password="S@njay12345",
        database="realestatebuddy"
    )

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            location VARCHAR(255),
            price INT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

create_table()

@app.route("/")
def home():
    cached = r.get("properties")
    if cached:
        properties = json.loads(cached)
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM properties")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        properties = [
            {"id": row[0], "title": row[1], "location": row[2], "price": row[3]}
            for row in rows
        ]

        r.set("properties", json.dumps(properties), ex=60)

    return render_template("index.html", properties=properties)


@app.route("/add", methods=["POST"])
def add_property():
    title = request.form["title"]
    location = request.form["location"]
    price = request.form["price"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO properties (title, location, price) VALUES (%s, %s, %s)",
        (title, location, price)
    )
    conn.commit()
    cur.close()
    conn.close()

    r.delete("properties")
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

