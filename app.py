import streamlit as st
from supabase import create_client
from datetime import datetime
import re

# --- CONFIG ---
SUPABASE_URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
SUPABASE_KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
MOMO_CELTIS = "0147794002"
MOMO_MTN = "0196012563"
PRIX = 1000
ADMIN_PWD = "parakou2024"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
st.set_page_config(page_title="Studyflow", page_icon="📚", layout="wide")
st.title("📚 Studyflow - Compte Payant = PDF Illimités")

if "paye" not in st.session_state: st.session_state["paye"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔐 Compte")
    # Admin pour toi
    pwd = st.text_input("Mot de passe Admin (toi)", type="password")
    if st.button("Connexion Admin"):
        if pwd == ADMIN_PWD:
            st.session_state["is_admin"] = True
            st.session_state["paye"] = True
    
    st.divider()
    st.header("💰 Compte Payant")
    st.write(f"**Paye {PRIX}F pour ajouter des PDF illimités**")
    st.code(f"CELTIS: {MOMO_CELTIS}\nMTN: {MOMO_MTN}", language="text")
    trans = st.text_input("ID Transaction MoMo après paiement")
    if st.button("✅ Activer mon compte payant", type="primary", use_container_width=True):
        if trans:
            st.session_state["paye"] = True
            st.success("Compte payant activé! Tu peux ajouter illimité!")
            st.balloons()
    
    if st.session_state["paye"]:
        st.success("✅ COMPTE PAYANT ACTIF\nTu peux ajouter autant de PDF que tu veux")
    else:
        st.warning("🆓 Compte Gratuit: Tu peux seulement voir")

paye = st.session_state["paye"] or st.session_state["is_admin"]

# --- PARTIE 1: AJOUTER (SEULEMENT SI PAYANT) ---
if paye:
    with st.container(bordered=True):
        st.subheader("➕ Ajouter un PDF (Compte Payant - Illimité)")
        st.caption("Tu as payé, tu peux ajouter 1, 10, 100 PDF, pas de limite")
        with st.form("add_pdf", clear_on_submit=True):
            col1, col2 = st.columns(2)
            titre = col1.text_input("Titre du PDF*")
            matiere = col2.selectbox("Matière", ["Maths","Physique","Chimie","SVT","Philo","Anglais","Français","Histoire-Géo","Autre"])
            pdf = st.file_uploader("Fichier PDF*", type=["pdf"])
            if st.form_submit_button(f"🚀 Ajouter ce PDF (encore { 'illimité' })", use_container_width=True):
                if titre and pdf:
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf.name)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                    with st.spinner("Sauvegarde permanente..."):
                        supabase.storage.from_(BUCKET).upload(fname, pdf.getvalue())
                        url = supabase.storage.from_(BUCKET).get_public_url(fname)
                        supabase.table("cours").insert({
                            "titre": titre, "matiere": matiere, "type": "Payant",
                            "file_name": fname, "url": url, "prix": PRIX
                        }).execute()
                    st.success(f"✅ {titre} ajouté! Tu peux en ajouter encore!")
                    st.rerun()
else:
    with st.container(bordered=True):
        st.warning(f"🔒 Tu es en compte gratuit. Paye {PRIX}F sur {MOMO_CELTIS} / {MOMO_MTN} pour pouvoir ajouter des PDF illimités")
        st.button("🔒 Ajouter PDF - Bloqué (Paye d'abord)", disabled=True)

# --- PARTIE 2: VOIR TOUS LES PDF ---
st.divider()
st.subheader("📂 Tous les PDF")

try:
    cours = supabase.table("cours").select("*").order("created_at", desc=True).execute().data
    if not cours:
        st.info("Aucun PDF. Sois le premier à payer et ajouter!")
    for c in cours:
        with st.container(bordered=True):
            c1, c2, c3 = st.columns([4,2,1])
            c1.write(f"**{c['titre']}** - {c['matiere']} - {c['created_at'][:10]}")
            # Tout le monde peut voir / ouvrir si on veut, ou seulement payant
            if c.get('url'):
                c2.link_button("📥 Ouvrir PDF", c['url'])
            if st.session_state["is_admin"]:
                if c3.button("🗑️", key=c['id']):
                    supabase.storage.from_(BUCKET).remove([c['file_name']])
                    supabase.table("cours").delete().eq("id", c['id']).execute()
                    st.rerun()
except Exception as e:
    st.error(f"Exécute le SQL de création table cours. Erreur: {e}")
