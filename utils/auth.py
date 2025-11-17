from db.connection import create_connection

def authenticate_user(email, password):
    conn = create_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Users WHERE email=%s AND password=%s"
            cursor.execute(sql, (email, password))
            user = cursor.fetchone()
            return user
    finally:
        conn.close()


def create_user(name, email, phone, password):
    conn = create_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            # Force role to 'Client'
            sql = """
                INSERT INTO Users (name, email, phone, role, password)
                VALUES (%s, %s, %s, 'Client', %s)
            """
            cursor.execute(sql, (name, email, phone, password))
            conn.commit()
            return True
    except Exception as e:
        print("Error creating user:", e)
        return False
    finally:
        conn.close()


def reset_password(email, new_password):
    conn = create_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE Users SET password=%s WHERE email=%s"
            cursor.execute(sql, (new_password, email))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()
