import streamlit as st
import pymysql
from db.connection import create_connection
from datetime import datetime


# ------------------------------------------------------------
# Helper Function: Execute Queries
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Agent Dashboard
# ------------------------------------------------------------
def agent_dashboard(user):
    st.sidebar.title(f"👋 Welcome, {user['name']}")
    menu = st.sidebar.radio("Navigation", [
        "🏡 My Properties",
        "➕ Add Property",
        "📅 Appointments",
        "💰 Sales & Rentals Overview",
        "⭐ Client Reviews",
        "👤 My Account"
    ])

    # =========================================================
    # ➕ ADD PROPERTY (Only Agents can add new ones)
    # =========================================================
    if menu.startswith("➕"):
        st.markdown("## 🏗️ Add a New Property")

        with st.form("add_property_form"):
            title = st.text_input("Property Title *")
            prop_type = st.selectbox("Property Type", ["For_Sale", "For_Rent"])
            price = st.number_input("Price (₹)", min_value=0.0, step=10000.0)
            location = st.text_input("Location *")
            building_age = st.number_input("Building Age (years)", min_value=0, step=1)
            status = "Available"

            submit = st.form_submit_button("📤 Add Property")

            if submit:
                if not title or not location:
                    st.warning("⚠️ Please fill in all required fields (Title and Location).")
                else:
                    run_query("""
                        INSERT INTO Properties 
                        (agent_id, title, type, price, location, building_age, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (user["user_id"], title, prop_type, price, location, building_age, status))
                    st.success("✅ Property added successfully!")

    # =========================================================
    # 🏡 MY PROPERTIES
    # =========================================================
    elif menu.startswith("🏡"):
        st.markdown("## 🏠 Properties You Manage")

        props = run_query("""
            SELECT property_id, title, type, price, location, status
            FROM Properties
            WHERE agent_id = %s;
        """, (user["user_id"],), fetch=True)

        if not props:
            st.info("No properties added yet. Use the 'Add Property' tab to list one.")
        else:
            for p in props:
                with st.container():
                    st.markdown(f"""
                    <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                        <b>{p['title']}</b><br>
                        📍 {p['location']}<br>
                        💰 Current Price: ₹{p['price']:,}<br>
                        🏷️ Type: {p['type']}<br>
                        📊 Status: {p['status']}
                    </div>
                    """, unsafe_allow_html=True)

                    new_price = st.number_input(
                        f"Enter new price for {p['title']}",
                        min_value=0.0,
                        step=10000.0,
                        key=f"price_{p['property_id']}"
                    )
                    if st.button("💾 Update Price", key=f"update_{p['property_id']}"):
                        try:
                            conn = create_connection()
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE Properties SET price = %s WHERE property_id = %s",
                                    (new_price, p["property_id"])
                                )
                            conn.commit()
                            st.success(f"✅ Price updated for {p['title']}!")
                        except pymysql.Error as e:
                            conn.rollback()
                            if "Price reduction exceeds" in str(e):
                                st.warning("⚠️ Price update blocked: cannot reduce price by more than 10%.")
                            else:
                                st.error(f"❌ Database Error: {e}")
                        finally:
                            conn.close()

    # =========================================================
    # 📅 MANAGE APPOINTMENTS
    # =========================================================
    elif menu.startswith("📅"):
        st.markdown("## 📋 Manage Appointments")

        if st.button("🔄 Refresh Appointments (Run Procedure)"):
            try:
                conn = create_connection()
                with conn.cursor() as cursor:
                    cursor.execute("CALL MarkPastAppointmentsCompleted();")
                conn.commit()
                st.success("✅ Past appointments automatically marked as 'Completed'!")
                st.rerun()
            except pymysql.Error as e:
                st.error(f"❌ Error running procedure: {e}")
            finally:
                conn.close()

        appts = run_query("""
            SELECT a.appointment_id, a.datetime, a.status,
                   p.title AS property, u.name AS client_name, u.phone AS client_phone
            FROM Appointments a
            JOIN Properties p ON a.property_id = p.property_id
            JOIN Users u ON a.user_id = u.user_id
            WHERE a.agent_id = %s
            ORDER BY a.datetime ASC;
        """, (user["user_id"],), fetch=True)

        if not appts:
            st.info("No appointments found.")
        else:
            for a in appts:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{a['property']}</b><br>
                    👤 {a['client_name']} ({a['client_phone']})<br>
                    🗓️ {a['datetime']}<br>
                    📌 Status: <b>{a['status']}</b>
                </div>
                """, unsafe_allow_html=True)

                if a["status"] in ["Pending", "Confirmed", "Cancelled"]:
                    new_status = st.selectbox(
                        f"Update status for '{a['property']}'",
                        ["Pending", "Confirmed", "Completed", "Cancelled"],
                        index=["Pending", "Confirmed", "Completed", "Cancelled"].index(a["status"]),
                        key=f"status_{a['appointment_id']}"
                    )
                    if new_status != a["status"]:
                        if st.button("Update Status", key=f"update_{a['appointment_id']}"):
                            run_query("UPDATE Appointments SET status = %s WHERE appointment_id = %s",
                                      (new_status, a["appointment_id"]))
                            st.success(f"✅ Status updated to {new_status}")
                            st.rerun()
                else:
                    st.info("✅ This appointment is already completed and cannot be modified.")

    # =========================================================
    # 💰 SALES & RENTALS OVERVIEW
    # =========================================================
    elif menu.startswith("💰"):
        st.markdown("## 💼 Sales & Rentals Overview")

        totals = run_query("""
            WITH AgentStats AS (
                SELECT
                    p.agent_id,
                    COUNT(DISTINCT p.property_id) AS total_listings,
                    COUNT(DISTINCT b.property_id) AS total_sales
                FROM Properties p
                LEFT JOIN Buys b ON p.property_id = b.property_id
                WHERE p.agent_id = %s
                GROUP BY p.agent_id
            )
            SELECT total_listings, total_sales FROM AgentStats;
        """, (user["user_id"],), fetch=True)

        if totals:
            st.metric("🏠 Total Listings", totals[0]["total_listings"])
            st.metric("💼 Total Sales", totals[0]["total_sales"])

        avg_rating = run_query("SELECT GetAverageGlobalRating() AS avg;", fetch=True)[0]["avg"]
        st.metric("🌟 Global Average Rating", f"{avg_rating} / 5")

        st.subheader("🏘️ Sales Handled")
        sales = run_query("""
            SELECT b.property_id, p.title, u.name AS buyer_name, b.amount, b.date,
                   CalculateAgentCommission(b.amount) AS commission
            FROM Buys b
            JOIN Properties p ON b.property_id = p.property_id
            JOIN Users u ON b.buyer_id = u.user_id
            WHERE p.agent_id = %s;
        """, (user["user_id"],), fetch=True)

        if sales:
            for s in sales:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{s['title']}</b><br>
                    💵 Sold to: {s['buyer_name']}<br>
                    📅 Date: {s['date']}<br>
                    💰 Amount: ₹{s['amount']:,}<br>
                    💸 Commission: ₹{s['commission']:,}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sales yet.")

        st.subheader("🏡 Rentals Managed")
        rentals = run_query("""
            SELECT r.property_id, p.title, u.name AS tenant_name,
                   r.rent_amount, r.start_date, r.end_date
            FROM Rents r
            JOIN Properties p ON r.property_id = p.property_id
            JOIN Users u ON r.tenant_id = u.user_id
            WHERE p.agent_id = %s;
        """, (user["user_id"],), fetch=True)

        if rentals:
            for r in rentals:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{r['title']}</b><br>
                    👤 Tenant: {r['tenant_name']}<br>
                    💰 Rent: ₹{r['rent_amount']:,}<br>
                    🗓️ {r['start_date']} → {r['end_date']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No rentals yet.")

    # =========================================================
    # ⭐ CLIENT REVIEWS
    # =========================================================
    elif menu.startswith("⭐"):
        st.markdown("## ⭐ Client Reviews")
        reviews = run_query("""
            SELECT u.name AS client_name, p.title AS property, r.rating, r.comments
            FROM Reviews r
            JOIN Users u ON r.user_id = u.user_id
            JOIN Properties p ON r.property_id = p.property_id
            WHERE r.agent_id = %s;
        """, (user["user_id"],), fetch=True)

        if not reviews:
            st.info("No reviews received yet.")
        else:
            for r in reviews:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{r['property']}</b><br>
                    👤 {r['client_name']}<br>
                    ⭐ Rating: {r['rating']} / 5<br>
                    💬 "{r['comments']}"
                </div>
                """, unsafe_allow_html=True)

    # =========================================================
    # 👤 ACCOUNT SETTINGS
    # =========================================================
    elif menu.startswith("👤"):
        st.markdown("## 👤 My Account Settings")

        with st.form("update_form"):
            name = st.text_input("Name", user["name"])
            email = st.text_input("Email", user["email"])
            phone = st.text_input("Phone", user["phone"])
            password = st.text_input("Password", type="password", placeholder="Leave blank to keep unchanged")
            submit = st.form_submit_button("💾 Save Changes")

            if submit:
                query = "UPDATE Users SET name=%s, email=%s, phone=%s"
                params = [name, email, phone]
                if password:
                    query += ", password=%s"
                    params.append(password)
                query += " WHERE user_id=%s"
                params.append(user["user_id"])

                run_query(query, tuple(params))
                st.success("✅ Profile updated successfully!")
