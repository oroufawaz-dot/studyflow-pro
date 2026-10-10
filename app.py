import streamlit as st
from supabase import create_client
from datetime import datetime, date
import re

URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
CELTIS = "0147794002"
MTN = "0196012563"
ADMIN_PWD = "parakou2024"
PRIX = 1000

supabase = create_client(URL, KEY)
st.set_page_config(page_title="Studyflow", layout="wide")
st.title("📚 Studyflow")

if "paye" not in st.session_state: st.session_state["paye"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False

with st.sidebar:
    st.header("🔐 Admin")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if pwd == ADMIN_PWD:
            st.session_state["is_admin"] = True
            st.session_state["paye"] = True
            st.success("Dépôt reçu et merci pour le soutien")
    st.divider()
    st.header("💳 Compte Pro")
    st.text(f"CELTIS: {CELTIS}\nMTN: {MTN}\n{PRIX}F")
    trans = st.text_input("ID MoMo")
    if st.button("Activer Pro", type="primary"):
        if trans:
            st.session_state["paye"] = True
            st.success("Dépôt reçu et merci pour le soutien")
            st.success("Compte Pro activé et merci pour le soutien")
            st.balloons()
    if st.session_state["paye"]:
        st.success("Compte Pro activé et merci pour le soutien")

paye = st.session_state["paye"] or st.session_state["is_admin"]

tab1, tab2, tab3 = st.tabs(["📘 Matières + Rappel", "✅ Tâches + Date", "📝 Cours & Épreuves"])

with tab1:
    st.subheader("Matières avec date de rappel")
    with st.form("mat", clear_on_submit=True):
        nom = st.text_input("Nom matière*")
        desc = st.text_area("Description")
        d = st.date_input("Date rappel", value=date.today())
        couleur = st.color_picker("Couleur", "#6366f1")
        if st.form_submit_button("Ajouter matière"):
            if nom and paye:
                supabase.table("matieres").insert({"nom": nom, "description": desc, "date_rappel": str(d), "couleur": couleur}).execute()
                st.success("Matière ajoutée")
                st.rerun()
            elif not paye:
                st.error(f"Compte Pro requis - Paye {PRIX}F sur {CELTIS}")
    
    try:
        for m in supabase.table("matieres").select("*").order("date_rappel", desc=False).execute().data:
            with st.container():
                st.write(f"**{m['nom']}** - Rappel: {m.get('date_rappel','')} | {m.get('description','')}")
                if m.get('date_rappel'):
                    if str(m['date_rappel']) == str(date.today()):
                        st.warning("⏰ Rappel aujourd'hui!")
    except Exception as e:
        st.write(e)

with tab2:
    st.subheader("Tâches avec échéance et heure de rappel")
    with st.form("tache_form", clear_on_submit=True):
        titre = st.text_input("Tâche*")
        desc = st.text_input("Détails")
        c1, c2, c3 = st.columns(3)
        date_ech = c1.date_input("Date échéance", value=date.today())
        heure = c2.time_input("Heure rappel")
        prio = c3.selectbox("Priorité", ["Basse","Normale","Haute","Urgente"])
        statut = st.selectbox("Statut", ["A faire","En cours","Terminé"])
        if st.form_submit_button("Ajouter tâche"):
            if titre and paye:
                supabase.table("taches").insert({"titre": titre, "description": desc, "date_echeance": str(date_ech), "heure_rappel": str(heure), "priorite": prio, "statut": statut}).execute()
                st.success(f"Tâche avec rappel {date_ech} {heure} ajoutée")
                st.rerun()
            elif not paye:
                st.error(f"Compte Pro requis - {CELTIS} / {MTN}")

    try:
        taches = supabase.table("taches").select("*").order("date_echeance").execute().data
        for t in taches:
            with st.container():
                col1, col2 = st.columns([4,1])
                col1.write(f"**{t['titre']}** - {t.get('priorite')} - {t.get('statut')} | 📅 {t.get('date_echeance')} ⏰ {t.get('heure_rappel')} | {t.get('description','')}")
                if col2.button("Terminé", key=f"done_{t['id']}"):
                    supabase.table("taches").update({"statut": "Terminé"}).eq("id", t["id"]).execute()
                    st.rerun()
                if t.get('date_echeance') == str(date.today()) and t.get('statut') != "Terminé":
                    st.warning(f"⏰ À faire aujourd'hui à {t.get('heure_rappel')}: {t['titre']}")
            st.divider()
    except Exception as e:
        st.write(e)

with tab3:
    st.subheader("Cours & Epreuves - Gratuit / Payant à vendre")
    if paye:
        st.success("Compte Pro: PDF illimités - Dépôt reçu et merci pour le soutien")
        with st.form("cours_f", clear_on_submit=True):
            titre = st.text_input("Titre*")
            mat = st.selectbox("Matière", ["Maths","Physique","Chimie","SVT","Philo","Autre"])
            typ = st.selectbox("Type", ["Gratuit", "Payant - A vendre"])
            pdf = st.file_uploader("PDF", type=["pdf"])
            if st.form_submit_button("Ajouter PDF illimité"):
                if titre and pdf:
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf.name)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                    supabase.storage.from_(BUCKET).upload(fname, pdf.getvalue())
                    url = supabase.storage.from_(BUCKET).get_public_url(fname)
                    supabase.table("cours").insert({"titre": titre, "matiere": mat, "type": typ, "file_name": fname, "url": url, "prix": 0 if typ=="Gratuit" else PRIX}).execute()
                    st.success("Compte Pro activé et merci pour le soutien - PDF ajouté!")
                    st.rerun()
    else:
        st.warning(f"Gratuit: Paye {PRIX}F sur {CELTIS} / {MTN} pour ajouter PDF illimités")

    try:
        for c in supabase.table("cours").select("*").order("created_at", desc=True).execute().data:
            st.write(f"**{c['titre']}** | {c['matiere']} | {c['type']} | {c.get('prix')}F")
            if c.get('url'):
                if "Gratuit" in c['type'] or paye:
                    st.link_button("Ouvrir PDF", c['url'])
                else:
                    st.write(f"🔒 Payant {PRIX}F - {CELTIS}")
            st.divider()
    except Exception as e:
        st.write(e)
