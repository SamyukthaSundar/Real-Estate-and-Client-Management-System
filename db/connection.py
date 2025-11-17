import pymysql

def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',           # Change if different
            password='',     # Your DB password
            db='real_estate_mgmt',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Error while connecting: {e}")
        return None
