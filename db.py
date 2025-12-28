import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",          # change if different
        password="navi31",
        database="hotel_db"
    )
    return connection
