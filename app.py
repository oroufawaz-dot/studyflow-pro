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
if "essai_utilise" not in st.session_state: st.session_state["essai_utilise"] = False

with st.sidebar:
    st.header("🔐 Admin")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if pwd == ADMIN_PWD:
            st.session_state["is_admin"] = True
            st.session_state["paye"] = True
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
    else:
        st.info("Essai gratuit: 1 matière + 3 tâches max, 1 fois. Après, paye.")

paye = st.session_state["paye"] or st.session_state["is_admin"]

# PUB POUR GRATUIT UNIQUEMENT
def afficher_pub():
    if not paye:
        st.info("📢 PUB - Studyflow Pro à 1000F seulement! Supprime les pubs + PDF illimités. Paye sur 0147794002 / 0196012563")
        st.image("https://via.placeholder.com/728x90?text=PUB+Studyflow+Pro+1000F", use_column_width=True)

afficher_pub()

tab1, tab2, tab3 = st.tabs(["📘 Matières (Essai: 1 max)", "✅ Tâches (Essai: 3 max)", "📝 Cours & Épreuves"])

# COMPTER POUR ESSAI GRATUIT
try:
    nb_mat = len(supabase.table("matieres").select("*").execute().data)
    nb_taches = len(supabase.table("taches").select("*").execute().data)
except:
    nb_mat = 0
    nb_taches = 0

with tab1:
    st.subheader("Matières + Rappel + Date")
    if not paye:
        st.warning(f"Essai gratuit: {nb_mat}/1 matière utilisée. C'est utilisable une fois seulement.")
        afficher_pub()
    
    with st.form("mat", clear_on_submit=True):
        nom = st.text_input("Nom matière*")
        desc = st.text_area("Description")
        d = st.date_input("Date rappel", value=date.today())
        if st.form_submit_button("Ajouter matière"):
            if not paye and nb_mat >= 1:
                st.error("Essai gratuit terminé! Tu as déjà utilisé ta 1 matière gratuite. Active Compte Pro pour illimité.")
                st.session_state["essai_utilise"] = True
            elif nom and (paye or nb_mat < 1):
                supabase.table("matieres").insert({"nom": nom, "description": desc, "date_rappel": str(d)}).execute()
                st.success("Matière ajoutée" if paye else "Matière d'essai ajoutée (1/1)")
                st.rerun()
    
    try:
        for m in supabase.table("matieres").select("*").order("date_rappel").execute().data:
            st.write(f"**{m['nom']}** - Rappel: {m.get('date_rappel')} | {m.get('description','')}")
            if str(m.get('date_rappel')) == str(date.today()):
                st.warning(f"⏰ Rappel aujourd'hui: {m['nom']}")
    except Exception as e:
        st.write(e)

with tab2:
    st.subheader("Tâches + Date échéance + Heure rappel")
    if not paye:
        st.warning(f"Essai gratuit: {nb_taches}/3 tâches utilisées. Au plus 3 tâches pour une matière, utilisable une fois.")
        afficher_pub()

    with st.form("tache_form", clear_on_submit=True):
        titre = st.text_input("Tâche*")
        desc = st.text_input("Détails")
        c1, c2, c3 = st.columns(3)
        date_ech = c1.date_input("Date échéance", value=date.today())
        heure = c2.time_input("Heure rappel")
        prio = c3.selectbox("Priorité", ["Basse","Normale","Haute","Urgente"])
        statut = st.selectbox("Statut", ["A faire","En cours","Terminé"])
        if st.form_submit_button("Ajouter tâche"):
            if not paye and nb_taches >= 3:
                st.error("Essai gratuit: 3 tâches max atteint! Passe en Compte Pro pour illimité sur 0147794002")
                st.session_state["essai_utilise"] = True
            elif titre and (paye or nb_taches < 3):
                supabase.table("taches").insert({"titre": titre, "description": desc, "date_echeance": str(date_ech), "heure_rappel": str(heure), "priorite": prio, "statut": statut}).execute()
                st.success("Tâche ajoutée" if paye else f"Tâche d'essai {nb_taches+1}/3 ajoutée")
                st.rerun()

    try:
        taches = supabase.table("taches").select("*").order("date_echeance").execute().data
        for t in taches:
            st.write(f"**{t['titre']}** | 📅 {t.get('date_echeance')} ⏰ {t.get('heure_rappel')} | {t.get('priorite')} | {t.get('statut')}")
            if t.get('date_echeance') == str(date.today()) and t.get('statut') != "Terminé":
                st.warning(f"⏰ À faire aujourd'hui à {t.get('heure_rappel')}: {t['titre']}")
            st.divider()
    except Exception as e:
        st.write(e)

with tab3:
    st.subheader("Cours & Épreuves à vendre - Gratuit / Payant")
    if not paye:
        afficher_pub()
        st.warning(f"Gratuit = voir seulement. Pour ajouter PDF illimités, Paye {PRIX}F sur {CELTIS} / {MTN}")
    else:
        st.success("Dépôt reçu et merci pour le soutien - Compte Pro activé et merci pour le soutien - PDF illimités")
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
                    st.success("Compte Pro activé et merci pour le soutien - PDF ajouté! Tu peux en ajouter encore!")
                    st.rerun()
    try:
        for c in supabase.table("cours").select("*").order("created_at", desc=True).execute().data:
            st.write(f"**{c['titre']}** | {c['matiere']} | {c['type']}")
            if c.get('url'):
                if "Gratuit" in c['type'] or paye:
                    st.link_button("Ouvrir", c['url'])
                else:
                    st.write(f"🔒 Payant {PRIX}F - {CELTIS} - Essai gratuit ne peut pas ouvrir")
            st.divider()
    except:
        pass

# PUB BAS DE PAGE POUR GRATUIT
if not paye:
    st.divider()
    afficher_pub()
    st.error("Fin de l'essai gratuit? Passe Pro 1000F - 0147794002 / 0196012563 pour supprimer les pubs")
