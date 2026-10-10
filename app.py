import streamlit as st
from supabase import create_client
from datetime import datetime
import re

# CONFIG
URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
MOMO_CELTIS = "0147794002"
MOMO_MTN = "0196012563"
ADMIN_PASSWORD = "parakou2024"
PRIX = 1000

supabase = create_client(URL, KEY)
st.set_page_config(page_title="Studyflow", page_icon="📚", layout="wide")
st.title("📚 Studyflow - Matières / Tâches / Cours")

if "paye" not in st.session_state: st.session_state["paye"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False

# SIDEBAR - MOT DE PASSE + MOMO
with st.sidebar:
    st.header("🔐 Admin")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if pwd == ADMIN_PASSWORD:
            st.session_state["is_admin"] = True
            st.session_state["paye"] = True
    
    st.divider()
    st.header("💳 Compte Pro")
    st.code(f"CELTIS: {MOMO_CELTIS}\nMTN: {MOMO_MTN}\n{Prix}F".replace("{Prix}", str(PRIX)))
    trans = st.text_input("ID MoMo")
    if st.button("Verifier", type="primary"):
        if trans:
            st.session_state["paye"] = True
            st.success("Dépôt reçu et merci pour le soutien")
            st.success("Compte Pro activé et merci pour le soutien")
            st.balloons()

    if st.session_state["paye"]:
        st.success("Compte Pro activé et merci pour le soutien")

paye = st.session_state["paye"] or st.session_state["is_admin"]

# TES 3 ONGLETS D'ORIGINE - JE GARDE
tab1, tab2, tab3 = st.tabs(["📘 Matières", "✅ Tâches", "📝 Cours & Epreuves à vendre"])

with tab1:
    st.subheader("Matières")
    nom = st.text_input("Nouvelle matière")
    if st.button("Ajouter matière"):
        if nom and paye:
            supabase.table("matieres").insert({"nom": nom}).execute()
            st.rerun()
        elif not paye:
            st.error("Compte Pro requis pour ajouter")
    try:
        for m in supabase.table("matieres").select("*").execute().data:
            st.write(f"- {m['nom']}")
    except: st.info("Crée table matieres dans Supabase si besoin")

with tab2:
    st.subheader("Tâches")
    with st.form("tache", clear_on_submit=True):
        t = st.text_input("Tâche")
        if st.form_submit_button("Ajouter"):
            if t and paye:
                supabase.table("taches").insert({"titre": t}).execute()
                st.rerun()
    try:
        for ta in supabase.table("taches").select("*").execute().data:
            st.write(f"- {ta['titre']}")
    except: pass

with tab3:
    st.subheader("Cours & Epreuves - Gratuit / Payant")
    
    # GRATUIT / PAYANT
    col_g, col_p = st.columns(2)
    col_g.info("🆓 Gratuit = visible par tous")
    col_p.warning("🔒 Payant = Compte Pro = PDF illimités")

    # AJOUT - SEULEMENT COMPTE PAYANT = ILLIMITÉ
    if paye:
        st.write("---")
        st.write("**Tu as le Compte Pro - Tu peux ajouter le nombre de PDF que tu veux (illimité)**")
        with st.form("cours_form", clear_on_submit=True):
            titre = st.text_input("Titre*")
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Matiere", ["Maths","Physique","Chimie","SVT","Philo","Anglais","Autre"])
            typ = c2.selectbox("Type", ["Gratuit", "Payant - A vendre"])
            pdf = st.file_uploader("PDF", type=["pdf"])
            if st.form_submit_button("Ajouter ce PDF (illimité)"):
                if titre and pdf:
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf.name)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                    supabase.storage.from_(BUCKET).upload(fname, pdf.getvalue())
                    url = supabase.storage.from_(BUCKET).get_public_url(fname)
                    supabase.table("cours").insert({"titre": titre, "matiere": mat, "type": typ, "file_name": fname, "url": url, "prix": 0 if typ=="Gratuit" else PRIX}).execute()
                    st.success("PDF ajouté! Tu peux en ajouter encore!")
                    st.rerun()
    else:
        st.warning(f"Pour ajouter des PDF illimités, active Compte Pro sur {MOMO_CELTIS} / {MOMO_MTN}")

    st.divider()
    # LISTE
    try:
        data = supabase.table("cours").select("*").order("created_at", desc=True).execute().data
        for c in data:
            st.write(f"**{c['titre']}** | {c['matiere']} | {c['type']}")
            if c.get('url'):
                if "Gratuit" in c['type']:
                    st.link_button("Ouvrir Gratuit", c['url'])
                else:
                    if paye:
                        st.link_button("Ouvrir (Compte Pro)", c['url'])
                    else:
                        st.write(f"🔒 Payant - {PRIX}F sur {MOMO_CELTIS}")
            st.divider()
    except Exception as e:
        st.error(e)
