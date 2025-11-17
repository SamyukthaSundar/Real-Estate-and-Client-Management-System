import streamlit as st
import pymysql
from db.connection import create_connection
import re

def is_valid_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)


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
        conn.rollback()
    finally:
        conn.close()


# ------------------------------------------------------------
# Admin Dashboard
# ------------------------------------------------------------
def admin_dashboard(user):
    st.sidebar.title(f"👋 Welcome, {user['name']} (Admin)")
    menu = st.sidebar.radio("Navigation", [
        "🏡 Manage Properties",
        "👥 Manage Users",
        "📅 View All Appointments",
        "📑 View All Transactions",
        "💰 System Insights",
        "⚙️ Maintenance",
    ])

    # =========================================================
    # 🏡 PROPERTY MANAGEMENT
    # =========================================================
    if menu.startswith("🏡"):
        st.markdown("## 🏠 Property Management")

        props = run_query("""
            SELECT p.property_id, p.title, p.price, p.location, p.type, p.status,
                   u.name AS agent_name, u.user_id AS agent_id
            FROM Properties p
            LEFT JOIN Users u ON p.agent_id = u.user_id
            ORDER BY p.status DESC, p.property_id ASC;
        """, fetch=True)

        agents = run_query("SELECT user_id, name FROM Users WHERE role='Agent';", fetch=True)

        # --- UNASSIGNED PROPERTIES ---
        st.subheader("🏠 Unassigned Properties")
        unassigned = [p for p in props if not p["agent_id"]]
        if not unassigned:
            st.info("✅ No unassigned properties.")
        else:
            for p in unassigned:
                st.markdown(f"""
                <div style='background-color:#252525;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{p['title']}</b><br>
                    📍 {p['location']}<br>
                    💰 Price: ₹{p['price']:,}<br>
                    🏷️ Type: {p['type']}<br>
                    📊 Status: {p['status']}
                </div>
                """, unsafe_allow_html=True)

                new_agent = st.selectbox(
                    f"Assign new agent for {p['title']}",
                    [a["name"] for a in agents],
                    key=f"assign_agent_{p['property_id']}"
                )
                if st.button("Assign Agent", key=f"assign_{p['property_id']}"):
                    agent_id = next(a["user_id"] for a in agents if a["name"] == new_agent)
                    run_query("UPDATE Properties SET agent_id=%s WHERE property_id=%s", (agent_id, p["property_id"]))
                    st.success(f"✅ Property '{p['title']}' assigned to {new_agent}.")
                    st.rerun()

        st.divider()
        st.subheader("🏘️ All Properties")

        if not props:
            st.info("No properties found.")
        else:
            for p in props:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{p['title']}</b><br>
                    📍 {p['location']}<br>
                    💰 ₹{p['price']:,}<br>
                    🏷️ {p['type']}<br>
                    📊 {p['status']}<br>
                    👨‍💼 Agent: {p['agent_name'] if p['agent_name'] else 'Unassigned'}
                </div>
                """, unsafe_allow_html=True)

                new_price = st.number_input(
                    f"New price for {p['title']}",
                    min_value=0.0,
                    value=float(p["price"]),
                    step=10000.0,
                    key=f"price_{p['property_id']}"
                )

                new_status = st.selectbox(
                    f"Change status for {p['title']}",
                    ["Available", "Sold", "Rented"],
                    index=["Available", "Sold", "Rented"].index(p["status"]),
                    key=f"status_{p['property_id']}"
                )

                agent_choices = ["Unassigned"] + [a["name"] for a in agents]
                current_agent = p["agent_name"] if p["agent_name"] else "Unassigned"
                new_agent = st.selectbox(
                    f"Assign agent for {p['title']}",
                    agent_choices,
                    index=agent_choices.index(current_agent),
                    key=f"agent_{p['property_id']}"
                )

                if st.button("💾 Update Property", key=f"update_{p['property_id']}"):
                    try:
                        conn = create_connection()
                        with conn.cursor() as cursor:
                            agent_id = None if new_agent == "Unassigned" else next(
                                (a["user_id"] for a in agents if a["name"] == new_agent), None
                            )
                            cursor.execute("""
                                UPDATE Properties
                                SET price=%s, status=%s, agent_id=%s
                                WHERE property_id=%s;
                            """, (new_price, new_status, agent_id, p["property_id"]))

                            # Clean up Buys/Rents if reset to Available
                            if new_status == "Available":
                                cursor.execute("DELETE FROM Buys WHERE property_id=%s", (p["property_id"],))
                                cursor.execute("DELETE FROM Rents WHERE property_id=%s", (p["property_id"],))
                        conn.commit()
                        st.success(f"✅ '{p['title']}' updated successfully!")
                        st.rerun()
                    except pymysql.Error as e:
                        conn.rollback()
                        st.error(f"❌ Database Error: {e}")
                    finally:
                        conn.close()

    # =========================================================
    # 👥 USER MANAGEMENT
    # =========================================================
    elif menu.startswith("👥"):
        st.markdown("## 👥 User Management")
        tabs = st.tabs(["🧑‍💼 Agents", "👤 Clients", "🗂️ All Users", "➕ Create User", "🔸 Inactive Agents"])

        # --- AGENTS TAB ---
        with tabs[0]:
            agents = run_query("SELECT user_id, name, email, phone FROM Users WHERE role='Agent' ORDER BY user_id;", fetch=True)
            if agents:
                for a in agents:
                    st.markdown(f"""
                    <div style='background-color:#202020;padding:15px;border-radius:12px;margin-bottom:10px;'>
                        <b>{a['name']}</b><br>
                        ✉️ {a['email']} | ☎️ {a['phone']}
                    </div>
                    """, unsafe_allow_html=True)

                    delete_confirm = st.checkbox(f"Confirm delete {a['name']}", key=f"confirm_del_agent_{a['user_id']}")
                    if st.button("🗑️ Delete Agent", key=f"delete_agent_{a['user_id']}"):
                        if delete_confirm:
                            run_query("UPDATE Properties SET agent_id=NULL WHERE agent_id=%s", (a["user_id"],))
                            run_query("DELETE FROM Users WHERE user_id=%s", (a["user_id"],))
                            st.success(f"✅ Agent '{a['name']}' deleted and their properties unassigned.")
                            st.rerun()
                        else:
                            st.warning("⚠️ Please confirm deletion using the checkbox first.")
            else:
                st.info("No agents yet.")

        # --- CLIENTS TAB ---
        with tabs[1]:
            clients = run_query("SELECT user_id, name, email, phone FROM Users WHERE role='Client';", fetch=True)
            if clients:
                for c in clients:
                    st.markdown(f"""
                    <div style='background-color:#202020;padding:15px;border-radius:12px;margin-bottom:10px;'>
                        <b>{c['name']}</b><br>
                        ✉️ {c['email']} | ☎️ {c['phone']}
                    </div>
                    """, unsafe_allow_html=True)

                    delete_confirm = st.checkbox(f"Confirm delete {c['name']}", key=f"confirm_del_client_{c['user_id']}")
                    if st.button("🗑️ Delete Client", key=f"delete_client_{c['user_id']}"):
                        if delete_confirm:
                            run_query("DELETE FROM Users WHERE user_id=%s", (c["user_id"],))
                            st.success(f"✅ Client '{c['name']}' deleted successfully.")
                            st.rerun()
                        else:
                            st.warning("⚠️ Please confirm deletion using the checkbox first.")
            else:
                st.info("No clients found.")

        # --- ALL USERS TAB ---
        with tabs[2]:
            users = run_query("SELECT user_id, name, email, phone, role FROM Users;", fetch=True)
            if users:
                for u in users:
                    st.markdown(f"""
                    <div style='background-color:#202020;padding:15px;border-radius:12px;margin-bottom:10px;'>
                        <b>{u['name']}</b><br>
                        ✉️ {u['email']} | ☎️ {u['phone']}<br>
                        🎭 Role: {u['role']}
                    </div>
                    """, unsafe_allow_html=True)

                    new_role = st.selectbox(
                        f"Change role for {u['name']}",
                        ["Client", "Agent", "Admin"],
                        index=["Client", "Agent", "Admin"].index(u["role"]),
                        key=f"role_{u['user_id']}"
                    )

                    if new_role != u["role"]:
                        if st.button(f"Update Role for {u['name']}", key=f"update_{u['user_id']}"):
                            run_query("UPDATE Users SET role=%s WHERE user_id=%s", (new_role, u["user_id"]))
                            st.success(f"✅ Role updated for {u['name']} → {new_role}")
                            st.rerun()
            else:
                st.info("No users found.")

        # --- CREATE NEW USER TAB ---
        with tabs[3]:
            st.markdown("### ➕ Create New User (Agent/Admin)")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Agent", "Admin"])

            if st.button("Create User"):
                if not all([name, email, password]):
                    st.warning("⚠️ Please fill all required fields.")
                elif not is_valid_email(email):
                        st.error("❌ Please enter a valid email address (e.g., name@domain.ext).")
                else:
                    try:
                        run_query(
                            "INSERT INTO Users (name, email, phone, role, password) VALUES (%s, %s, %s, %s, %s)",
                            (name.strip(), email.strip().lower(), phone.strip(), role, password)
                        )
                        st.success(f"✅ {role} '{name}' created successfully!")
                    except pymysql.err.IntegrityError:
                        st.error("🚫 This email is already registered. Use a different email.")
                    except Exception as e:
                        st.error(f"❌ Error creating user: {e}")

        # --- INACTIVE AGENTS TAB ---
                # --- INACTIVE AGENTS TAB (Query 4) ---
        with tabs[4]:
            st.markdown("### 🔸 Inactive Agents (No Sales or Rentals)")
            inactive_agents = run_query("""
                SELECT user_id, name, email, phone
                FROM Users
                WHERE role = 'Agent'
                AND user_id NOT IN (
                    SELECT DISTINCT p.agent_id
                    FROM Properties p
                    LEFT JOIN Buys b ON p.property_id = b.property_id
                    LEFT JOIN Rents r ON p.property_id = r.property_id
                    WHERE b.property_id IS NOT NULL OR r.property_id IS NOT NULL
                );
            """, fetch=True)

            if inactive_agents:
                for a in inactive_agents:
                    st.markdown(f"""
                    <div style='background-color:#252525;padding:15px;border-radius:12px;margin-bottom:10px;'>
                        <b>{a['name']}</b><br>
                        ✉️ {a['email']} | ☎️ {a['phone']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ All agents have activity (sales or rentals).")

    # =========================================================
    # 📅 APPOINTMENTS
    # =========================================================
    elif menu.startswith("📅"):
        st.markdown("## 📋 All Appointments Overview")
        appts = run_query("""
            SELECT a.appointment_id, a.datetime, a.status,
                   u.name AS client, ag.name AS agent, p.title AS property
            FROM Appointments a
            JOIN Users u ON a.user_id = u.user_id
            JOIN Users ag ON a.agent_id = ag.user_id
            JOIN Properties p ON a.property_id = p.property_id
            ORDER BY a.datetime DESC;
        """, fetch=True)

        if not appts:
            st.info("No appointments found.")
        else:
            for a in appts:
                st.markdown(f"""
                <div style='background-color:#222;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{a['property']}</b><br>
                    👤 Client: {a['client']}<br>
                    🧑‍💼 Agent: {a['agent']}<br>
                    🗓️ {a['datetime']}<br>
                    📌 Status: {a['status']}
                </div>
                """, unsafe_allow_html=True)

    # =========================================================
    # 📑 TRANSACTIONS
    # =========================================================
    elif menu.startswith("📑"):
        st.markdown("## 📑 All Transactions")

        st.subheader("🏠 Sales Transactions")
        sales = run_query("""
            SELECT b.property_id, p.title, u.name AS buyer, ag.name AS agent,
                   b.amount, b.date, CalculateAgentCommission(b.amount) AS commission
            FROM Buys b
            JOIN Properties p ON b.property_id = p.property_id
            JOIN Users u ON b.buyer_id = u.user_id
            LEFT JOIN Users ag ON p.agent_id = ag.user_id
            ORDER BY b.date DESC;
        """, fetch=True)

        if sales:
            for s in sales:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{s['title']}</b><br>
                    👤 Buyer: {s['buyer']}<br>
                    🧑‍💼 Agent: {s['agent'] if s['agent'] else 'Unassigned'}<br>
                    💰 Amount: ₹{s['amount']:,}<br>
                    💸 Commission: ₹{s['commission']:,}<br>
                    📅 Date: {s['date']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sales transactions found.")

        st.subheader("🏡 Rental Transactions")
        rentals = run_query("""
            SELECT r.property_id, p.title, u.name AS tenant, ag.name AS agent,
                   r.rent_amount, r.start_date, r.end_date
            FROM Rents r
            JOIN Properties p ON r.property_id = p.property_id
            JOIN Users u ON r.tenant_id = u.user_id
            LEFT JOIN Users ag ON p.agent_id = ag.user_id
            ORDER BY r.start_date DESC;
        """, fetch=True)

        if rentals:
            for r in rentals:
                st.markdown(f"""
                <div style='background-color:#1e1e1e;padding:15px;border-radius:12px;margin-bottom:10px;'>
                    <b>{r['title']}</b><br>
                    👤 Tenant: {r['tenant']}<br>
                    🧑‍💼 Agent: {r['agent'] if r['agent'] else 'Unassigned'}<br>
                    💰 Rent: ₹{r['rent_amount']:,}<br>
                    🗓️ {r['start_date']} → {r['end_date']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No rental transactions found.")

    # =========================================================
    # 💰 SYSTEM INSIGHTS
    # =========================================================
    elif menu.startswith("💰"):
        st.markdown("## 💰 System Insights")
        avg_rating = run_query("SELECT GetAverageGlobalRating() AS avg;", fetch=True)[0]["avg"]
        st.metric("🌟 Global Average Rating", f"{avg_rating} / 5")

        totals = run_query("""
            SELECT 
                (SELECT COUNT(*) FROM Properties) AS total_properties,
                (SELECT COUNT(*) FROM Users WHERE role='Agent') AS total_agents,
                (SELECT COUNT(*) FROM Users WHERE role='Client') AS total_clients,
                (SELECT COUNT(*) FROM Buys) AS total_sales,
                (SELECT COUNT(*) FROM Rents) AS total_rentals;
        """, fetch=True)[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("🏘️ Total Properties", totals["total_properties"])
        col2.metric("🧑‍💼 Agents", totals["total_agents"])
        col3.metric("👥 Clients", totals["total_clients"])

        col4, col5 = st.columns(2)
        col4.metric("💵 Total Sales", totals["total_sales"])
        col5.metric("🏠 Total Rentals", totals["total_rentals"])

        # ------------------------------------------------------------
        # 🧠 Advanced SQL Analytics (Complex Queries)
        # ------------------------------------------------------------
        st.divider()
        st.markdown("### 🧠 Advanced Insights")

        # ----------------------------
        # Query 2: Top Performing Agents
        # ----------------------------
        st.subheader("🏆 Top 5 Performing Agents by Total Sales")
        top_agents = run_query("""
            SELECT 
                u.user_id,
                u.name AS agent_name,
                SUM(b.amount) AS total_sales,
                RANK() OVER (ORDER BY SUM(b.amount) DESC) AS rank_position
            FROM Buys b
            JOIN Properties p ON b.property_id = p.property_id
            JOIN Users u ON p.agent_id = u.user_id
            GROUP BY u.user_id, u.name
            ORDER BY total_sales DESC
            LIMIT 5;
        """, fetch=True)

        if top_agents:
            import pandas as pd
            import matplotlib.pyplot as plt

            df_top_agents = pd.DataFrame(top_agents)
            st.dataframe(df_top_agents[['rank_position', 'agent_name', 'total_sales']])

            fig, ax = plt.subplots()
            ax.bar(df_top_agents['agent_name'], df_top_agents['total_sales'])
            ax.set_xlabel("Agent")
            ax.set_ylabel("Total Sales (₹)")
            ax.set_title("Top 5 Performing Agents")
            st.pyplot(fig)
        else:
            st.info("No sales data yet.")

        # ----------------------------
        # Query 3: Property Status Summary by City
        # ----------------------------
        st.subheader("🏙️ Property Status Summary by City")
        city_summary = run_query("""
            SELECT 
                location,
                SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available_count,
                SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) AS sold_count,
                SUM(CASE WHEN status = 'Rented' THEN 1 ELSE 0 END) AS rented_count
            FROM Properties
            GROUP BY location
            ORDER BY location;
        """, fetch=True)

        if city_summary:
            import pandas as pd
            import matplotlib.pyplot as plt

            df_city = pd.DataFrame(city_summary)

            # Convert counts to numeric to avoid "no numeric data" error
            numeric_cols = ["available_count", "sold_count", "rented_count"]
            for col in numeric_cols:
                df_city[col] = pd.to_numeric(df_city[col], errors="coerce").fillna(0)

            st.dataframe(df_city)

            if not df_city.empty:
                fig, ax = plt.subplots()
                df_city.set_index('location')[numeric_cols].plot(kind='bar', ax=ax)
                ax.set_xlabel("City / Location")
                ax.set_ylabel("Number of Properties")
                ax.set_title("Property Distribution by City and Status")
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.info("No data available to plot.")
        else:
            st.info("No property data available yet.")


        # ----------------------------
        # Query 5: Monthly Revenue Report (Text-Based Stylish UI)
        # ----------------------------
        st.subheader("📊 Monthly Revenue Report (Sales + Rentals)")

        revenue_data = run_query("""
            SELECT 
                DATE_FORMAT(date, '%%Y-%%m') AS month,
                SUM(amount) AS total_revenue,
                'Sales' AS source
            FROM Buys
            GROUP BY month

            UNION ALL

            SELECT 
                DATE_FORMAT(start_date, '%%Y-%%m') AS month,
                SUM(rent_amount) AS total_revenue,
                'Rentals' AS source
            FROM Rents
            GROUP BY month
            ORDER BY month DESC;
        """, fetch=True)

        if revenue_data:
            st.markdown("""
                <div style='background-color:#1e1e1e; padding:15px; border-radius:12px;'>
                    <h4 style='color:#FFD700;'>💰 Monthly Revenue Summary</h4>
                    <p style='color:#AAAAAA;'>Here’s a quick snapshot of total income from <b>Sales</b> and <b>Rentals</b> by month:</p>
                </div>
            """, unsafe_allow_html=True)

            # Convert results to dict for monthly grouping
            monthly = {}
            for row in revenue_data:
                month = row['month']
                if month not in monthly:
                    monthly[month] = {'Sales': 0, 'Rentals': 0}
                monthly[month][row['source']] = row['total_revenue'] or 0

            for month, data in monthly.items():
                total = (data['Sales'] or 0) + (data['Rentals'] or 0)
                st.markdown(f"""
                    <div style='background-color:#252525; padding:12px; border-radius:10px; margin-top:10px;'>
                        <b style='color:#4FC3F7;'>📅 {month}</b><br>
                        🏠 <b style='color:#81C784;'>Sales:</b> ₹{data['Sales']:,}<br>
                        🏡 <b style='color:#FFB74D;'>Rentals:</b> ₹{data['Rentals']:,}<br>
                        💵 <b style='color:#FFD54F;'>Total:</b> ₹{total:,}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No revenue data available yet 💭")


        
    # =========================================================
    # ⚙️ MAINTENANCE
    # =========================================================
    elif menu.startswith("⚙️"):
        st.markdown("## ⚙️ Maintenance Tools")
        st.info("Run cleanup or maintenance procedures.")
        if st.button("🔄 Run MarkPastAppointmentsCompleted()"):
            try:
                conn = create_connection()
                with conn.cursor() as cursor:
                    cursor.execute("CALL MarkPastAppointmentsCompleted();")
                conn.commit()
                st.success("✅ Procedure executed successfully! Past appointments marked as completed.")
            except pymysql.Error as e:
                st.error(f"❌ Database Error: {e}")
            finally:
                conn.close()
