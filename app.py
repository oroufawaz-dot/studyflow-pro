import streamlit as st
import sqlite3
import datetime

st.set_page_config(page_title="StudyFlow Pro", page_icon="🎓", layout="wide")
conn = sqlite3.connect('studyflow.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS cours (matiere TEXT, date TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS taches (tache TEXT, fait INTEGER)')
conn.commit()

st.title("StudyFlow Pro 🎓")
menu = st.sidebar.selectbox("MENU", ["Accueil", "Mes Cours", "Mes Taches", "Tarifs Pro"])

if menu == "Accueil":
    st.success("Ton SaaS Pro est prêt!")
    col1, col2, col3 = st.columns(3)
    nb_c = c.execute('SELECT COUNT(*) FROM cours').fetchone()[0]
    nb_t = c.execute('SELECT COUNT(*) FROM taches').fetchone()[0]
    with col1: st.metric("Utilisateur", "1", "Toi")
    with col2: st.metric("Cours", nb_c)
    with col3: st.metric("Taches", nb_t)
    st.balloons()

if menu == "Mes Cours":
    st.header("Mes Cours")
    mat = st.text_input("Matière")
    dat = st.date_input("Date", datetime.date.today())
    if st.button("Ajouter cours"):
        if mat:
            c.execute('INSERT INTO cours VALUES (?,?)', (mat, str(dat)))
            conn.commit()
            st.success(f"Cours {mat} ajouté!")
    st.write("---")
    for row in c.execute('SELECT rowid, * FROM cours'):
        st.write(f"📚 {row[1]} - {row[2]}")
        if st.button("Supprimer", key=row[0]):
            c.execute('DELETE FROM cours WHERE rowid=?', (row[0],))
            conn.commit()
            st.rerun()

if menu == "Mes Taches":
    st.header("Mes Tâches")
    t = st.text_input("Nouvelle tâche")
    if st.button("Ajouter tâche"):
        if t:
            c.execute('INSERT INTO taches VALUES (?,0)', (t,))
            conn.commit()
            st.success("Ajouté!")
    for row in c.execute('SELECT rowid, * FROM taches'):
        ok = st.checkbox(row[1], value=bool(row[2]), key=f"t{row[0]}")
        c.execute('UPDATE taches SET fait=? WHERE rowid=?', (int(ok), row[0]))
        conn.commit()

if menu == "Tarifs Pro":
    st.header("Passer Pro - 1000 FCFA / mois")
    st.write("Débloque : Export PDF, Rappels WhatsApp, Thèmes illimités")
    st.link_button("💳 Payer avec FedaPay / Mobile Money", "https://ton-lien-fedapay-ici.com")
    st.info("Après paiement, tu reçois ton code d'activation Pro")
