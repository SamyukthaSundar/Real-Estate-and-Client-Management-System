import streamlit as st
import pymysql
from PIL import Image
import pandas as pd
from datetime import datetime, date
from db.connection import create_connection
import re


# ============================================================
# Helper: Execute Queries
# ============================================================
def run_query(query, params=(), fetch=False):
    conn = create_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()
    except pymysql.Error as e:
        st.error(f"❌ Database Error: {e}")
    finally:
        conn.close()

# ============================================================
# Fetch Data
# ============================================================
def fetch_properties(prop_type, location, budget):
    return run_query("""
        SELECT p.property_id, p.title, p.price, p.location, p.type, p.status,
               u.name AS agent_name, u.phone AS agent_phone, u.email AS agent_email, u.user_id AS agent_id
        FROM Properties p
        JOIN Users u ON p.agent_id = u.user_id
        WHERE p.type=%s AND p.price<=%s AND p.location LIKE %s AND p.status='Available';
    """, (prop_type, budget, f"%{location}%"), fetch=True)

def fetch_all_properties():
    return run_query("""
        SELECT p.property_id, p.title, p.price, p.location, p.type, p.status,
               u.name AS agent_name, u.phone AS agent_phone, u.email AS agent_email, u.user_id AS agent_id
        FROM Properties p
        JOIN Users u ON p.agent_id = u.user_id
        WHERE p.status='Available';
    """, fetch=True)

def fetch_all_agents():
    return run_query("SELECT user_id, name, phone, email FROM Users WHERE role='Agent';", fetch=True)

def fetch_appointments(client_id):
    appts = run_query("""
        SELECT a.appointment_id, a.datetime, a.status, p.title AS property,
               u.name AS agent_name, u.phone AS agent_phone, u.email AS agent_email
        FROM Appointments a
        JOIN Properties p ON a.property_id = p.property_id
        JOIN Users u ON a.agent_id = u.user_id
        WHERE a.user_id=%s
        ORDER BY a.datetime DESC;
    """, (client_id,), fetch=True)

    if not appts:
        return pd.DataFrame()
    df = pd.DataFrame(appts)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.rename(columns={
        "datetime": "Date/Time",
        "property": "Property",
        "agent_name": "Agent",
        "agent_phone": "Agent Phone",
        "agent_email": "Agent Email",
        "status": "Status",
        "appointment_id": "Appointment ID"
    })
    return df

def fetch_purchases_rentals(client_id):
    conn = create_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 'Buy' AS type, p.property_id, p.title, p.location, b.amount AS price, b.date,
                       u.name AS agent_name, u.phone AS agent_phone
                FROM Buys b
                JOIN Properties p ON b.property_id = p.property_id
                JOIN Users u ON p.agent_id = u.user_id
                WHERE b.buyer_id = %s
                ORDER BY b.date DESC;
            """, (client_id,))
            buys = cursor.fetchall()

            cursor.execute("""
                SELECT 'Rent' AS type, p.property_id, p.title, p.location, r.rent_amount AS price,
                       r.start_date AS start_date, r.end_date AS end_date,
                       u.name AS agent_name, u.phone AS agent_phone
                FROM Rents r
                JOIN Properties p ON r.property_id = p.property_id
                JOIN Users u ON p.agent_id = u.user_id
                WHERE r.tenant_id = %s
                ORDER BY r.start_date DESC;
            """, (client_id,))
            rents = cursor.fetchall()
            return buys + rents
    finally:
        conn.close()

# ============================================================
# Core Operations
# ============================================================
def book_appointment(user_id, property_id, agent_id, appt_datetime):
    run_query("""
        INSERT INTO Appointments (user_id, property_id, agent_id, datetime, status)
        VALUES (%s, %s, %s, %s, 'Pending');
    """, (user_id, property_id, agent_id, appt_datetime))
    st.success("✅ Appointment booked successfully!")

def cancel_appointment(appt_id):
    run_query("UPDATE Appointments SET status='Cancelled' WHERE appointment_id=%s;", (appt_id,))
    st.success("❌ Appointment cancelled.")

def buy_property(user_id, property_id, amount):
    run_query("""
        INSERT INTO Buys (buyer_id, property_id, amount, date)
        VALUES (%s, %s, %s, NOW());
    """, (user_id, property_id, amount))
    run_query("UPDATE Properties SET status='Sold' WHERE property_id=%s;", (property_id,))
    st.success("🏡 Property purchased successfully!")

def rent_property(user_id, property_id, rent_amount, start_date, end_date):
    if start_date < date.today():
        st.error("❌ Start date cannot be in the past.")
        return
    if end_date <= start_date:
        st.error("❌ End date must be after start date.")
        return

    run_query("""
        INSERT INTO Rents (tenant_id, property_id, rent_amount, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s);
    """, (user_id, property_id, rent_amount, start_date, end_date))
    run_query("UPDATE Properties SET status='Rented' WHERE property_id=%s;", (property_id,))
    st.success("🏠 Property rented successfully!")

def add_review(user_id, property_id, agent_id, rating, comments):
    try:
        run_query("""
            INSERT INTO Reviews (user_id, property_id, agent_id, rating, comments)
            VALUES (%s, %s, %s, %s, %s);
        """, (user_id, property_id, agent_id, rating, comments))
        st.success("⭐ Review submitted successfully!")
    except pymysql.Error as e:
        if "Duplicate entry" in str(e):
            st.warning("⚠️ You've already reviewed this property.")
        else:
            st.error(f"❌ Error adding review: {e}")

def fetch_my_reviews(user_id):
    return run_query("""
        SELECT r.rating, r.comments, p.title, u.name AS agent_name
        FROM Reviews r
        JOIN Properties p ON r.property_id = p.property_id
        JOIN Users u ON r.agent_id = u.user_id
        WHERE r.user_id=%s;
    """, (user_id,), fetch=True)

def update_user_details(user_id, name, email, phone):
    run_query("UPDATE Users SET name=%s, email=%s, phone=%s WHERE user_id=%s;", (name, email, phone, user_id))
    st.success("✅ Profile updated successfully!")

def delete_account(user_id):
    run_query("DELETE FROM Users WHERE user_id=%s;", (user_id,))
    st.success("🗑️ Your account has been deleted. Transaction and review records are retained.")
    
    # Clear session and show message
    st.session_state.clear()
    st.info("🔄 Please refresh the page or return to the login screen to continue.")


# ============================================================
# Display Helpers
# ============================================================
def display_properties(props, user):
    for p in props:
        col_img, col_info = st.columns([1, 3])
        with col_img:
            try:
                st.image("house.jpg", width=120)
            except:
                st.write("🏠")
        with col_info:
            st.markdown(f"""
            **{p['title']}**
            - 📍 Location: {p['location']}
            - 🏷️ Type: {p['type']}
            - 💰 Price: ₹{p['price']:,}
            - 📊 Status: {p['status']}
            - 👨‍💼 Agent: {p['agent_name']}
            - ☎️ Contact: {p['agent_phone']}
            - ✉️ Email: {p['agent_email']}
            """)
            if p["type"] == "For_Sale" and p["status"] == "Available":
                if st.button(f"💵 Buy {p['title']}", key=f"buy_{p['property_id']}"):
                    buy_property(user["user_id"], p["property_id"], p["price"])
            elif p["type"] == "For_Rent" and p["status"] == "Available":
                with st.expander(f"🏠 Rent {p['title']}"):
                    start_date = st.date_input("Start Date", min_value=date.today(), key=f"start_{p['property_id']}")
                    end_date = st.date_input("End Date", min_value=start_date, key=f"end_{p['property_id']}")
                    if st.button(f"📅 Confirm Rent for {p['title']}", key=f"rent_{p['property_id']}"):
                        rent_property(user["user_id"], p["property_id"], p["price"], start_date, end_date)
        st.divider()

# ============================================================
# Main Client Dashboard
# ============================================================
def client_dashboard(user):
    st.sidebar.title(f"🏠 Welcome, {user['name']}")
    menu = st.sidebar.radio("Navigation", [
        "🏡 Search Properties",
        "🏘️ View All Properties",
        "📅 Book Appointment",
        "📋 My Appointments",
        "💼 My Purchases & Rentals",
        "⭐ Write a Review",
        "💬 My Reviews",
        "👤 My Account"
    ])

    if menu.startswith("🏡"):
        st.markdown("## 🔍 Search for Properties")
        with st.form("search_form"):
            col1, col2, col3 = st.columns(3)
            with col1: type_sel = st.selectbox("Type", ["For_Sale", "For_Rent"])
            with col2: location_sel = st.text_input("Location", placeholder="Enter city or area")
            with col3: budget_sel = st.number_input("Max Budget", min_value=0, value=1000000, step=10000)
            search_btn = st.form_submit_button("Search")
        if search_btn:
            props = fetch_properties(type_sel, location_sel, budget_sel)
            st.markdown("### 🏡 Search Results" if props else "No matching properties found.")
            if props: display_properties(props, user)

    elif menu.startswith("🏘️"):
        st.markdown("## 🏘️ All Available Properties")
        props = fetch_all_properties()
        display_properties(props, user) if props else st.info("No properties currently available.")

    elif menu.startswith("📅"):
        st.markdown("## 📅 Book an Appointment")
        props = fetch_all_properties()
        if not props: st.warning("No properties available."); return
        selected = st.selectbox("Select Property", [f"{p['property_id']} - {p['title']}" for p in props])
        selected_prop = next(p for p in props if f"{p['property_id']} - {p['title']}" == selected)
        agents = fetch_all_agents()
        agent_sel = st.selectbox("Select Agent", [f"{a['user_id']} - {a['name']} ({a['phone']})" for a in agents])
        agent_id = int(agent_sel.split(" - ")[0])
        appt_date = st.date_input("Date", min_value=date.today())
        appt_time = st.time_input("Time", datetime.now().time())
        appt_datetime = datetime.combine(appt_date, appt_time)
        if st.button("Confirm Appointment"):
            book_appointment(user["user_id"], selected_prop["property_id"], agent_id, appt_datetime)

    elif menu.startswith("📋"):
        st.markdown("## 🗓️ My Appointments (Past & Upcoming)")
        # ✅ Auto-update past appointments before fetching
        run_query("CALL MarkPastAppointmentsCompleted();")
        df = fetch_appointments(user["user_id"])
        if df.empty:
            st.info("No appointments found.")
        else:
            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"**Property:** {row['Property']}  \n**Agent:** {row['Agent']}  \n📅 {row['Date/Time']}  \n📌 Status: {row['Status']}")
                    if row["Status"] not in ["Cancelled", "Completed"]:
                        if st.button("Cancel", key=f"cancel_{row['Appointment ID']}"):
                            cancel_appointment(row["Appointment ID"])
                st.divider()

    elif menu.startswith("💼"):
        st.markdown("## 💼 My Purchases & Rentals")
        history = fetch_purchases_rentals(user["user_id"])
        if not history:
            st.info("No transactions found.")
        else:
            for h in history:
                st.markdown(f"""
                **Property:** {h['title']}  
                **Location:** {h['location']}  
                **Transaction:** {h['type']}  
                **Amount:** ₹{h['price']:,}  
                **Agent:** {h['agent_name']}  
                **Contact:** {h['agent_phone']}
                """)
                if h["type"] == "Rent":
                    st.write(f"🗓️ {h['start_date']} → {h['end_date']}")
                st.divider()

    elif menu.startswith("⭐"):
        st.markdown("## ⭐ Write a Review")
        trans = fetch_purchases_rentals(user["user_id"])
        if not trans:
            st.info("You can only review properties you've bought or rented.")
            return
        property_map = {f"{t['property_id']} - {t['title']}": t for t in trans}
        selected = st.selectbox("Select Property", list(property_map.keys()))
        selected_item = property_map[selected]
        rating = st.slider("Rating (1-5)", 1, 5, 5)
        comments = st.text_area("Comments")
        if st.button("Submit Review"):
            agent_id = run_query("SELECT agent_id FROM Properties WHERE property_id=%s;", (selected_item["property_id"],), fetch=True)[0]["agent_id"]
            add_review(user["user_id"], selected_item["property_id"], agent_id, rating, comments)

    elif menu.startswith("💬"):
        st.markdown("## 💬 My Reviews")
        reviews = fetch_my_reviews(user["user_id"])
        if not reviews:
            st.info("No reviews yet.")
        else:
            for r in reviews:
                stars = "⭐" * r["rating"]
                st.markdown(f"**{r['title']}** ({stars})  \n👨‍💼 Agent: {r['agent_name']}  \n💬 {r['comments']}")
                st.divider()

    elif menu.startswith("👤"):
        st.markdown("## 👤 My Account")

        def is_valid_email(email):
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return re.match(pattern, email)

    
        with st.form("update_form"):
            name = st.text_input("Full Name", value=user["name"])
            email = st.text_input("Email", value=user["email"])
            phone = st.text_input("Phone", value=user["phone"])
            update_btn = st.form_submit_button("Update Profile")
            if update_btn:
                # ✅ Email validation
                if not is_valid_email(email):
                    st.error("❌ Please enter a valid email address (e.g., name@domain.ext).")
                else:
                    try:
                        run_query("UPDATE Users SET name=%s, email=%s, phone=%s WHERE user_id=%s",
                                (name.strip(), email.strip().lower(), phone.strip(), user["user_id"]))
                        st.success("✅ Profile updated successfully!")
                    except pymysql.err.IntegrityError:
                        st.error("🚫 That email is already in use. Choose another one.")
                    except Exception as e:
                        st.error(f"❌ Error updating profile: {e}")
        st.divider()
        st.markdown("### ⚠️ Account Deletion")

        # Initialize state variable
        if "show_confirm_delete" not in st.session_state:
            st.session_state.show_confirm_delete = False

        # When delete button is pressed
        if st.button("🗑️ Delete Account"):
            st.session_state.show_confirm_delete = True

        # Show confirmation prompt if flag is set
        if st.session_state.show_confirm_delete:
            st.markdown(
                "<div style='background-color:#3c1d1d;padding:12px;border-radius:10px;'>"
                "🚨 <b>Are you absolutely sure?</b> This action <b>cannot be undone</b>."
                "</div>",
                unsafe_allow_html=True
            )
            st.write("")
            st.markdown(
                "<div style='color:#00b4d8;font-weight:bold;'>Click below to confirm or cancel:</div>",
                unsafe_allow_html=True
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirm Delete"):
                    delete_account(user["user_id"])
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_confirm_delete = False
                    st.success("Account deletion cancelled.")

