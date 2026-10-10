import streamlit as st
from supabase import create_client
from datetime import datetime
import re

URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
MOMO_CELTIS = "0147794002"
MOMO_MTN = "0196012563"

supabase = create_client(URL, KEY)
st.set_page_config(page_title="Studyflow", layout="wide")
st.title("📚 Studyflow")

if "paye" not in st.session_state:
    st.session_state["paye"] = False

with st.sidebar:
    st.header("💰 Activer Compte Pro")
    st.code(f"CELTIS: {MOMO_CELTIS}\nMTN: {MOMO_MTN}\n1000F")
    trans = st.text_input("ID Transaction MoMo")
    if st.button("Verifier paiement", type="primary"):
        if trans:
            st.session_state["paye"] = True
            # MESSAGE QUE TU VOULAIS - N'OUBLIE PAS
            st.success("✅ Dépôt reçu et merci pour le soutien")
            st.success("✅ Compte Pro activé et merci pour le soutien")
            st.balloons()

paye = st.session_state["paye"]

# Si payé, message en grand
if paye:
    st.success("✅ Dépôt reçu et merci pour le soutien")
    st.success("✅ Compte Pro activé et merci pour le soutien - Tu peux ajouter PDF illimités")

# ZONE AJOUT - SEULEMENT SI PAYE = ILLIMITÉ
if paye:
    st.subheader("➕ Ajouter PDF (Illimité)")
    with st.form("add", clear_on_submit=True):
        titre = st.text_input("Titre*")
        matiere = st.selectbox("Matiere", ["Maths","Physique","Chimie","SVT","Philo","Autre"])
        pdf = st.file_uploader("PDF*", type=["pdf"])
        if st.form_submit_button("Ajouter ce PDF"):
            if titre and pdf:
                safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf.name)
                fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                supabase.storage.from_(BUCKET).upload(fname, pdf.getvalue())
                url = supabase.storage.from_(BUCKET).get_public_url(fname)
                supabase.table("cours").insert({"titre": titre, "matiere": matiere, "file_name": fname, "url": url}).execute()
                st.success(f"✅ {titre} ajouté! Tu peux encore en ajouter!")
                st.rerun()
else:
    st.warning(f"Compte gratuit - Paye 1000F sur {MOMO_CELTIS} / {MOMO_MTN}")

# LISTE
st.divider()
try:
    data = supabase.table("cours").select("*").order("created_at", desc=True).execute().data
    for c in data:
        st.write(f"**{c['titre']}** - {c['matiere']}")
        if c.get('url'):
            st.link_button("Ouvrir", c['url'])
        st.divider()
except:
    pass
