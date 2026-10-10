import streamlit as st
import sqlite3
import random
from datetime import datetime

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

# --- SIDEBAR ---
st.sidebar.header("🔓 Débloquer Pro")
code_input = st.sidebar.text_input("Ton code Pro", placeholder="FLOW-4829").upper().strip()

if code_input:
    c.execute("SELECT used FROM codes WHERE code=?", (code_input,))
    row = c.fetchone()
    if row:
        if row[0] == 0:
            c.execute("UPDATE codes SET used=1 WHERE code=?", (code_input,))
            conn.commit()
        st.session_state.is_pro = True
        st.sidebar.success(f"✅ Pro activé: {code_input}")
        st.balloons()
    else:
        st.sidebar.error("❌ Code invalide")

is_pro = st.session_state.is_pro

st.sidebar.divider()
st.sidebar.markdown("""
**💰 Pour avoir ton code Pro - 1000F**

📱 **Celtiis:** 01 47 79 40 02
📱 **MTN MoMo:** 01 96 01 25 63

1. Envoie 1000F
2. Envoie la capture sur WhatsApp
3. Je t'envoie ton code unique

⚡ *1 code = 1 personne*
""")

# --- ADMIN ---
params = st.query_params
if params.get("admin") == "oui":
    st.title("👑 ADMIN")
    pwd = st.text_input("Mot de passe admin", type="password")
    if pwd == "parakou2026":
        st.success("Connecté")
        if st.button("🎲 Générer 10 nouveaux codes à vendre"):
            nouveaux = []
            for _ in range(10):
                new = f"FLOW-{random.randint(1000,9999)}"
                try:
                    c.execute("INSERT INTO codes (code) VALUES (?)", (new,))
                    nouveaux.append(new)
                except:
                    pass
            conn.commit()
            st.success(f"{len(nouveaux)} codes créés")
            st.code("\n".join(nouveaux))

        st.divider()
        rows = c.execute("SELECT code, used FROM codes ORDER BY used ASC").fetchall()
        st.dataframe(rows, use_container_width=True)
        st.info(f"Total: {len(rows)} | Vendus: {sum(r[1] for r in rows)} | Dispo: {len(rows)-sum(r[1] for r in rows)}")
    else:
        if pwd!= "":
            st.error("Mauvais mot de passe")
    st.stop()

# --- APP ---
st.title("📚 StudyFlow Pro")
st.caption("L'app des étudiants pour ne plus rater un devoir")

col1, col2 = st.columns([1,2])
with col1:
    st.subheader("➕ Ajouter")
    matiere = st.text_input("Matière")
    tache = st.text_input("Devoir / Tâche")
    date = st.date_input("Date limite", value=datetime.now())
    if st.button("Ajouter", use_container_width=True):
        if matiere and tache:
            c.execute("INSERT INTO tasks (matiere,tache,date,fait) VALUES (?,?,?,0)", (matiere, tache, str(date)))
            conn.commit()
            st.rerun()
with col2:
    st.subheader("📋 Mes tâches")
    tasks = c.execute("SELECT * FROM tasks ORDER BY date").fetchall()
    if not tasks:
        st.info("Aucune tâche")
    else:
        for id_, mat, tach, d, fait in tasks:
            col_a, col_b = st.columns([4,1])
            with col_a:
                chk = st.checkbox(f"**{mat}** - {tach} ({d})", value=bool(fait), key=f"id_{id_}")
                if chk!= bool(fait):
                    c.execute("UPDATE tasks SET fait=? WHERE id=?", (int(chk), id_))
                    conn.commit()
                    st.rerun()
            with col_b:
                if st.button("🗑️", key=f"del_{id_}"):
                    c.execute("DELETE FROM tasks WHERE id=?", (id_,))
                    conn.commit()
                    st.rerun()

if not is_pro:
    st.warning("👈 Version gratuite. Passe Pro à 1000F")
else:
    st.success("✅ Mode Pro actif")
