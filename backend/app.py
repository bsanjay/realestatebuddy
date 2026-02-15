from flask import Flask, jsonify, request
import mysql.connector
import redis
import os
import json
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "realestatebuddy-db")
REDIS_HOST = os.getenv("REDIS_HOST", "realestatebuddy-redis")

# Wait for MySQL to be ready
time.sleep(10)

# Redis connection
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# DB connection
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user="admin",
        password="admin123",
        database="realestate"
    )

# Create table
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

@app.route("/properties", methods=["GET"])
def get_properties():
    cached = r.get("properties")
    if cached:
        return jsonify(json.loads(cached))

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
    return jsonify(properties)

@app.route("/properties", methods=["POST"])
def add_property():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO properties (title, location, price) VALUES (%s, %s, %s)",
        (data["title"], data["location"], data["price"])
    )
    conn.commit()
    cur.close()
    conn.close()

    r.delete("properties")
    return {"message": "Property added"}, 201

app.run(host="0.0.0.0", port=5000)

