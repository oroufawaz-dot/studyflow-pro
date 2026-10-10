import streamlit as st
import sqlite3
import random
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="StudyFlow Pro", page_icon="📚", layout="wide")

conn = sqlite3.connect('studyflow.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, matiere TEXT, tache TEXT, date TEXT, fait INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, used INTEGER DEFAULT 0)''')
conn.commit()

c.execute("SELECT COUNT(*) FROM codes")
if c.fetchone()[0] == 0:
    for _ in range(5):
        code = f"FLOW-{random.randint(1000,9999)}"
        c.execute("INSERT INTO codes (code) VALUES (?)", (code,))
    conn.commit()

if "is_pro" not in st.session_state:
    st.session_state.is_pro = False

MASTER_CODE = "OROU-BOSS"

st.sidebar.header("🔓 Débloquer Pro")
code_input = st.sidebar.text_input("Ton code Pro", placeholder="FLOW-4829").upper().strip()

if code_input:
    if code_input == MASTER_CODE:
        st.session_state.is_pro = True
        st.sidebar.success(f"👑 Boss activé")
        st.balloons()
    else:
        c.execute("SELECT used FROM codes WHERE code=?", (code_input,))
        row = c.fetchone()
        if row:
            if row[0] == 0:
                c.execute("UPDATE codes SET used=1 WHERE code=?", (code_input,))
                conn.commit()
            st.session_state.is_pro = True
            st.sidebar.success(f"✅ Pro activé")
            st.balloons()
        else:
            st.sidebar.error("❌ Code invalide")

is_pro = st.session_state.is_pro

st.sidebar.divider()
if not is_pro:
    st.sidebar.warning("Version Gratuite - 3 tâches max")
else:
    st.sidebar.success("✅ Version Pro - Illimitée")

st.sidebar.markdown("""
**💰 Code Pro - 1000F**

📱 **Celtiis:** 01 47 79 40 02
📱 **MTN MoMo:** 01 96 01 25 63

1. Envoie 1000F
2. Capture WhatsApp
3. Reçois ton code unique
""")

# --- ADMIN ---
params = st.query_params
if params.get("admin") == "oui":
    st.title("👑 ADMIN")
    pwd = st.text_input("Mot de passe admin", type="password")
    if pwd == "parakou2026":
        st.success(f"Boss code: {MASTER_CODE}")
        if st.button("🎲 Générer 10 nouveaux codes", use_container_width=True):
            nouveaux = []
            for _ in range(10):
                new = f"FLOW-{random.randint(1000,9999)}"
                try:
                    c.execute("INSERT INTO codes (code) VALUES (?)", (new,))
                    nouveaux.append(new)
                except: pass
            conn.commit()
            st.code("\n".join(nouveaux))
        st.divider()
        rows = c.execute("SELECT code, used FROM codes").fetchall()
        st.dataframe(rows, use_container_width=True)
    st.stop()

# --- APP ---
st.title("📚 StudyFlow Pro")
tasks = c.execute("SELECT * FROM tasks ORDER BY date").fetchall()
total = len(tasks)
faits = len([t for t in tasks if t[4]==1])

# STATS PRO
if is_pro:
    col1, col2, col3 = st.columns(3)
    col1.metric("Tâches", total)
    col2.metric("Faites", faits)
    col3.metric("Restantes", total-faits)

st.divider()
col1, col2 = st.columns([1,2])

with col1:
    st.subheader("➕ Ajouter")
    if not is_pro and total >= 3:
        st.error("⛔ Limite gratuite atteinte (3 tâches max)")
        st.info("👉 Passe Pro à 1000F pour illimité!")
        st.sidebar.error("Bloqué - Passe Pro")
    else:
        matiere = st.text_input("Matière")
        tache = st.text_input("Devoir")
        date = st.date_input("Date limite", value=datetime.now())
        if st.button("Ajouter", use_container_width=True, type="primary"):
            if matiere and tache:
                c.execute("INSERT INTO tasks (matiere,tache,date,fait) VALUES (?,?,?,0)", (matiere, tache, str(date)))
                conn.commit()
                st.rerun()

with col2:
    st.subheader("📋 Mes tâches")
    if not tasks:
        st.info("Aucune tâche")
    else:
        for id_, mat, tach, d, fait in tasks:
            col_a, col_b = st.columns([4,1])
            with col_a:
                color = "🟢" if fait else "🔴"
                if is_pro:
                    st.checkbox(f"{color} **{mat}** - {tach} ({d})", value=bool(fait), key=f"id_{id_}")
                else:
                    st.checkbox(f"{color} {mat} - {tach} ({d})", value=bool(fait), key=f"id_{id_}")
            with col_b:
                if st.button("🗑️", key=f"del_{id_}"):
                    c.execute("DELETE FROM tasks WHERE id=?", (id_,))
                    conn.commit()
                    st.rerun()

        if is_pro:
            st.divider()
            df = pd.DataFrame(tasks, columns=["id","Matiere","Tache","Date","Fait"])
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter mes devoirs (Pro)", csv, "devoirs.csv", "text/csv", use_container_width=True)

if not is_pro:
    st.warning("🔓 Version Gratuite : 3 tâches max. Passe Pro à 1000F pour illimité + stats + export!")
else:
    st.success("👑 Pro Actif - Merci pour ton soutien!")
