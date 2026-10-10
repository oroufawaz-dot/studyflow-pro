import streamlit as st
from supabase import create_client
from datetime import datetime
import re

# --- TES INFOS ---
URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
CELTIS = "0147794002"
MTN = "0196012563"
ADMIN_PWD = "parakou2024"
PRIX = 1000

supabase = create_client(URL, KEY)
st.set_page_config(page_title="Studyflow", layout="wide")
st.title("Studyflow - Matieres / Taches / Cours")

if "paye" not in st.session_state:
    st.session_state["paye"] = False
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

with st.sidebar:
    st.header("Admin")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if pwd == ADMIN_PWD:
            st.session_state["is_admin"] = True
            st.session_state["paye"] = True
            st.success("Admin OK")
    
    st.divider()
    st.header("Compte Pro")
    st.text(f"CELTIS: {CELTIS}\nMTN: {MTN}\nPrix: {PRIX}F")
    trans = st.text_input("ID MoMo")
    if st.button("Verifier paiement", type="primary"):
        if trans:
            st.session_state["paye"] = True
            st.success("Depot recu et merci pour le soutien")
            st.success("Compte Pro active et merci pour le soutien")
            st.balloons()

    if st.session_state["paye"]:
        st.success("Compte Pro active et merci pour le soutien")

paye = st.session_state["paye"] or st.session_state["is_admin"]

# --- TES CONCEPTS D'ORIGINE ---
tab1, tab2, tab3 = st.tabs(["Matieres", "Taches", "Cours & Epreuves"])

with tab1:
    st.subheader("Matieres")
    nom = st.text_input("Nouvelle matiere")
    if st.button("Ajouter matiere"):
        if nom and paye:
            supabase.table("matieres").insert({"nom": nom}).execute()
            st.rerun()
        elif not paye:
            st.error("Compte Pro requis")
    try:
        data = supabase.table("matieres").select("*").execute().data
        for m in data:
            st.write(f"- {m['nom']}")
    except:
        st.info("Cree table matieres si besoin")

with tab2:
    st.subheader("Taches")
    with st.form("tache", clear_on_submit=True):
        t = st.text_input("Tache")
        if st.form_submit_button("Ajouter"):
            if t and paye:
                supabase.table("taches").insert({"titre": t}).execute()
                st.rerun()
    try:
        data = supabase.table("taches").select("*").execute().data
        for x in data:
            st.write(f"- {x['titre']}")
    except:
        pass

with tab3:
    st.subheader("Cours & Epreuves a vendre - Gratuit / Payant")
    
    if paye:
        st.success("Compte Pro: Tu peux ajouter le nombre de PDF que tu veux (illimite)")
        with st.form("add_cours", clear_on_submit=True):
            titre = st.text_input("Titre*")
            mat = st.selectbox("Matiere", ["Maths","Physique","Chimie","SVT","Philo","Autre"])
            typ = st.selectbox("Type", ["Gratuit", "Payant - A vendre"])
            pdf = st.file_uploader("PDF", type=["pdf"])
            if st.form_submit_button("Ajouter PDF"):
                if titre and pdf:
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf.name)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                    supabase.storage.from_(BUCKET).upload(fname, pdf.getvalue())
                    url = supabase.storage.from_(BUCKET).get_public_url(fname)
                    supabase.table("cours").insert({"titre": titre, "matiere": mat, "type": typ, "file_name": fname, "url": url, "prix": 0 if typ=="Gratuit" else PRIX}).execute()
                    st.success("Ajoute!")
                    st.rerun()
    else:
        st.warning(f"Compte gratuit. Paye {PRIX}F sur {CELTIS} / {MTN} pour ajouter PDF illimites")

    st.divider()
    try:
        data = supabase.table("cours").select("*").order("created_at", desc=True).execute().data
        for c in data:
            st.write(f"**{c['titre']}** - {c['matiere']} - {c['type']}")
            if c.get('url'):
                if "Gratuit" in c['type']:
                    st.link_button("Ouvrir Gratuit", c['url'])
                else:
                    if paye:
                        st.link_button("Ouvrir (Pro)", c['url'])
                    else:
                        st.write(f"Payant {PRIX}F - {CELTIS}")
            st.divider()
    except Exception as e:
        st.write(e)
