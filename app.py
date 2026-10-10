import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import PyPDF2
import time

st.set_page_config(page_title="Studyflow Parakou", page_icon="📚", layout="wide")

SUPABASE_URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
SUPABASE_KEY = "TA_CLE_ANON_ICI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASS = "parakou2024"
PRIX = 1000
NUM_MOMO = "0147794002 / 0196012563"

if "USER_ID" not in st.session_state: st.session_state.USER_ID = ""
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "paye" not in st.session_state: st.session_state.paye = False
if "pomodoro" not in st.session_state: st.session_state.pomodoro = 25*60

if not st.session_state.USER_ID:
    st.title("📚 Studyflow Parakou - La réussite commence ici")
    st.markdown("### Ton espace privé sécurisé")
    p = st.text_input("Prénom")
    n = st.text_input("Nom / Pseudo unique")
    if st.button("Entrer dans mon espace privé", type="primary", use_container_width=True):
        if p and n:
            st.session_state.USER_ID = f"{p.strip()}{n.strip()}".replace(" ","").lower()
            st.rerun()
        else: st.error("Remplis tout")
    st.stop()

USER_ID = st.session_state.USER_ID

def load(table):
    try:
        if st.session_state.is_admin:
            return supabase.table(table).select("*").order("created_at", desc=True).execute().data
        else:
            return supabase.table(table).select("*").eq("user_id", USER_ID).order("created_at", desc=True).execute().data
    except: return []

# CHECK PRO
is_pro_temp = False
try:
    rows = supabase.table("paiements").select("*").eq("telephone", USER_ID).eq("statut","confirme").execute().data
    for r in rows:
        if r.get("valide_jusqua"):
            try:
                if datetime.fromisoformat(r["valide_jusqua"].replace("Z","")) > datetime.now():
                    is_pro_temp = True
                    st.session_state.paye = True
            except: pass
except: pass
is_pro = is_pro_temp or st.session_state.is_admin

matieres = load("matieres")
taches = load("taches")
epreuves = load("epreuves")
emplois = load("emplois")

# BLOCAGE FIN MOIS
if not st.session_state.is_admin:
    actif=False
    try:
        for r in supabase.table("paiements").select("*").eq("telephone", USER_ID).eq("statut","confirme").execute().data:
            if r.get("valide_jusqua") and datetime.fromisoformat(r["valide_jusqua"].replace("Z","")) > datetime.now():
                actif=True
    except: pass
    if not actif and len(matieres)>=1:
        st.error("⛔ ACCES BLOQUE - Fin du mois expirée")
        st.warning(f"Fais un dépôt {PRIX}F sur {NUM_MOMO} et envoie l'ID dans le menu gauche. L'admin va confirmer à sa place.")
        st.stop()

with st.sidebar:
    st.header(f"👤 {USER_ID}")
    st.write("✅ PRO" if is_pro else "🆓 ESSAI - 1 mat / 3 tâches")
    if st.button("Changer fenêtre"): st.session_state.USER_ID=""; st.rerun()
    st.divider()
    if not is_pro:
        st.subheader(f"Deviens PRO {PRIX}F / mois")
        st.code(NUM_MOMO)
        idd=st.text_input("Colle ID dépôt MoMo ici")
        if st.button("Envoyer ID", type="primary", use_container_width=True):
            if idd:
                exist=supabase.table("paiements").select("*").eq("id_depot", idd).execute().data
                if exist: st.error("ID déjà utilisé")
                else:
                    supabase.table("paiements").insert({"id_depot":idd,"telephone":USER_ID,"statut":"en_attente","montant":PRIX}).execute()
                    st.success("Dépôt reçu et merci pour le soutien - Attente admin")
    else: st.success("Compte Pro activé et merci pour le soutien 🎈")
    st.divider()
    st.subheader("⏱️ Pomodoro")
    if st.button("Lancer 25min"): st.session_state.pomodoro=25*60
    st.write(f"{st.session_state.pomodoro//60} min")
    st.divider()
    if not st.session_state.is_admin:
        with st.expander("Connexion Admin"):
            pw=st.text_input("Mot de passe admin", type="password")
            if st.button("Login"): 
                if pw==ADMIN_PASS: st.session_state.is_admin=True; st.rerun()
                else: st.error("Faux")
    else:
        st.error("MODE ADMIN - Tu vois tout le monde")
        if st.button("Quitter admin"): st.session_state.is_admin=False; st.rerun()
        st.write("---"); st.write("Paiements en attente")
        for a in supabase.table("paiements").select("*").eq("statut","en_attente").execute().data:
            st.write(f"**ID:{a['id_depot']}**\nUser:{a['telephone']}")
            c1,c2=st.columns(2)
            if c1.button("✅ Confirmer", key=f"c{a['id']}"):
                fin=(datetime.now()+timedelta(days=30)).isoformat()
                supabase.table("paiements").update({"statut":"confirme","valide_jusqua":fin}).eq("id",a["id"]).execute()
                st.success(f"Relancé pour {a['telephone']}"); st.rerun()
            if c2.button("❌", key=f"r{a['id']}"): supabase.table("paiements").delete().eq("id",a["id"]).execute(); st.rerun()

lim_mat = is_pro or len(matieres)<1
lim_tache = is_pro or len(taches)<3

st.title(f"Bienvenue {USER_ID} !")
colA,colB,colC=st.columns(3)
colA.metric("Matières", len(matieres))
colB.metric("Tâches", len(taches))
colC.metric("Statut", "PRO 👑" if is_pro else "Essai")

tab1,tab2,tab3,tab4,tab5=st.tabs(["📖 Matières","✅ Tâches du jour","📝 Épreuves & Devoirs","🗓️ Emploi du temps","📊 Stats Admin"])

with tab1:
    st.subheader("Mes matières")
    if not lim_mat and not st.session_state.is_admin: st.error("Limite essai atteinte")
    c1,c2=st.columns([3,1])
    nm=c1.text_input("Ex: Mathématiques Tle D", key="nm")
    if c2.button("Ajouter", use_container_width=True):
        if nm and lim_mat:
            supabase.table("matieres").insert({"nom":nm,"user_id":USER_ID}).execute(); st.rerun()
    st.divider()
    with st.expander("📄 Importer PDF de cours"):
        pdf=st.file_uploader("PDF", type=["pdf"])
        if pdf and st.button("Extraire"):
            reader=PyPDF2.PdfReader(pdf); txt="".join([p.extract_text() or "" for p in reader.pages]); st.text_area("Contenu", txt[:2000])
    for m in matieres:
        co1,co2=st.columns([6,1])
        co1.write(f"📘 **{m['nom']}** {f' - {m.get('user_id')}' if st.session_state.is_admin else ''}")
        if co2.button("🗑️", key=f"dm{m['id']}"): supabase.table("matieres").delete().eq("id",m["id"]).execute(); st.rerun()

with tab2:
    st.subheader("Tâches du jour")
    if not lim_tache and not st.session_state.is_admin: st.error("Limite 3 tâches essai")
    nt=st.text_input("Ex: Faire exercice 5 page 20", key="nt")
    if st.button("Ajouter tâche", use_container_width=True) and nt and lim_tache:
        supabase.table("taches").insert({"nom":nt,"user_id":USER_ID,"faite":False}).execute(); st.rerun()
    for t in taches:
        c1,c2,c3=st.columns([1,6,1])
        chk=c1.checkbox("", value=t.get("faite",False), key=f"chk{t['id']}")
        if chk!=t.get("faite",False): supabase.table("taches").update({"faite":chk}).eq("id",t["id"]).execute(); st.rerun()
        c2.write(f"~~{t['nom']}~~" if chk else t['nom'])
        if c3.button("X", key=f"dt{t['id']}"): supabase.table("taches").delete().eq("id",t["id"]).execute(); st.rerun()

with tab3:
    st.subheader("Épreuves à venir")
    ne=st.text_input("Nom épreuve ex: Bac blanc"); de=st.date_input("Date", key="de")
    if st.button("Ajouter épreuve") and ne:
        supabase.table("epreuves").insert({"nom":ne,"date":str(de),"user_id":USER_ID}).execute(); st.rerun()
    for e in epreuves:
        st.info(f"📝 {e['nom']} - {e.get('date','')} {f'({e.get('user_id')})' if st.session_state.is_admin else ''}")

with tab4:
    st.subheader("Emploi du temps")
    j=st.selectbox("Jour",["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"])
    h=st.text_input("Heure ex: 08h-10h"); cou=st.text_input("Matière")
    if st.button("Ajouter créneau") and cou:
        supabase.table("emplois").insert({"jour":j,"heure":h,"cours":cou,"user_id":USER_ID}).execute(); st.rerun()
    for em in sorted(emplois, key=lambda x: x.get("jour","")):
        st.write(f"**{em.get('jour')}** {em.get('heure')} : {em.get('cours')} {f'[{em.get('user_id')}]' if st.session_state.is_admin else ''}")
        if st.button("Suppr", key=f"de{em['id']}"): supabase.table("emplois").delete().eq("id",em["id"]).execute(); st.rerun()

with tab5:
    if st.session_state.is_admin:
        st.header("Tous les utilisateurs - Toi seul vois")
        all_data = supabase.table("paiements").select("*").execute().data
        st.write(f"{len(all_data)} paiements totaux")
        users=set([x["telephone"] for x in all_data if x.get("telephone")])
        for u in users:
            cm=len(supabase.table("matieres").select("*").eq("user_id",u).execute().data)
            ct=len(supabase.table("taches").select("*").eq("user_id",u).execute().data)
            st.write(f"👤 {u} -> {cm} mat / {ct} tâches")
    else: st.info("Réservé admin - toi seul peux voir tout le monde ici")
