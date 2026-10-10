import streamlit as st
import sqlite3

st.set_page_config(page_title="StudyFlow Pro", page_icon="📚", layout="wide")

conn = sqlite3.connect('studyflow.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, matiere TEXT, tache TEXT, date TEXT, fait INTEGER)''')
conn.commit()

# SIDEBAR PRO
st.sidebar.header("🔓 Débloquer Pro")
code = st.sidebar.text_input("Code Pro", placeholder="PRO1000")

if code.upper() == "PRO1000":
    is_pro = True
    st.sidebar.success("✅ Pro activé !")
else:
    is_pro = False
    if code != "":
        st.sidebar.error("❌ Code invalide")

st.sidebar.divider()
st.sidebar.markdown("**💰 Avoir le code (1000F):**\nMoMo: 0147794002 ou 0196012563\nEnvoie capture WhatsApp")

# APP
st.title("📚 StudyFlow Pro")
st.caption("SaaS pour gérer les cours et tâches - Bénin")

matiere = st.text_input("Matière")
tache = st.text_input("Tâche")
date = st.date_input("Date limite")

if st.button("Ajouter tâche"):
    if matiere and tache:
        c.execute("INSERT INTO tasks (matiere,tache,date,fait) VALUES (?,?,?,0)", (matiere, tache, str(date)))
        conn.commit()
        st.success("Ajouté !")
        st.rerun()

st.divider()
st.subheader("📋 Mes tâches")
c.execute("SELECT * FROM tasks ORDER BY date")
for id_, mat, tach, d, fait in c.fetchall():
    chk = st.checkbox(f"{mat} - {tach} ({d})", value=bool(fait), key=f"id_{id_}")
    if chk != bool(fait):
        c.execute("UPDATE tasks SET fait=? WHERE id=?", (int(chk), id_))
        conn.commit()
        st.rerun()

if not is_pro:
    st.warning("👈 Entre ton code Pro à gauche")
else:
    st.success("Mode Pro activé")
