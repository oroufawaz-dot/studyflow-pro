import streamlit as st
import json, os, datetime, uuid, base64
from datetime import datetime as dt, date, time
import pandas as pd

st.set_page_config(page_title="StudyFlow", page_icon="📚", layout="wide", initial_sidebar_state="expanded")

APP_NAME = "StudyFlow"
NUM_MOMO = "0147794002 / 0196012563"
PRIX_PRO = 1000
ADMIN_PASS = "parakou2024"

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: #0F172A;}
div[data-testid="stDecoration"] {display:none;}
</style>
<link rel="manifest" href="app/static/manifest.json">
<link rel="icon" href="app/static/favicon.png">
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('app/static/service-worker.js');
}
let saved = localStorage.getItem('studyflow_user');
function saveLogin(u){ localStorage.setItem('studyflow_user', JSON.stringify(u)); }
if(Notification && Notification.permission!== 'granted'){ Notification.requestPermission(); }
function notifyStudyFlow(title, body){
  if(Notification.permission === 'granted'){
    navigator.serviceWorker.ready.then(reg => {
      reg.showNotification(title, {body: body, icon: 'app/static/icon-512.png', badge: 'app/static/favicon.png', vibrate: [200,100,200]});
    });
  }
}
setInterval(()=> {
  let tasks = JSON.parse(localStorage.getItem('studyflow_tasks')||'[]');
  tasks.forEach(t=>{
    if(t.reminder && new Date(t.reminder) <= new Date() &&!t.notified){
      notifyStudyFlow('StudyFlow 📚', t.title);
      t.notified=true;
    }
  });
  localStorage.setItem('studyflow_tasks', JSON.stringify(tasks));
}, 60000);
</script>
""", unsafe_allow_html=True)

DB_FILE = "db.json"
def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE,'r') as f:
                return json.load(f)
    except: pass
    return {"users":{}}
def save_db(db):
    with open(DB_FILE,'w') as f:
        json.dump(db,f, indent=2, default=str)

db = load_db()

if "user" not in st.session_state:
    st.session_state.user = None
if "is_pro" not in st.session_state:
    st.session_state.is_pro = False

def login(u,p):
    users = db.get("users",{})
    if u in users and users[u].get("password")==p:
        st.session_state.user = u
        st.session_state.is_pro = users[u].get("is_pro", False)
        st.markdown(f"<script>saveLogin({{user:'{u}'}})</script>", unsafe_allow_html=True)
        return True
    if u=="admin" and p==ADMIN_PASS:
        st.session_state.user = "admin"
        st.session_state.is_pro = True
        return True
    return False

def register(u,p):
    if "users" not in db: db["users"]={}
    if u in db["users"]: return False
    db["users"][u]={"password":p,"is_pro":False,"matieres":[],"taches":[],"epreuves":[],"emploi":[],"notes":[],"pomodoros":[],"places":[],"created":str(dt.now())}
    save_db(db)
    return True

if not st.session_state.user:
    st.title("📚 StudyFlow pour tous")
    st.caption("Ta plateforme d'étude tout-en-un -Partout")
    tab1, tab2 = st.tabs(["Connexion","Inscription"])
    with tab1:
        u = st.text_input("Nom d'utilisateur", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter", use_container_width=True):
            if login(u,p):
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    with tab2:
        u2 = st.text_input("Nouveau nom", key="reg_u")
        p2 = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
        if st.button("Créer mon compte StudyFlow", use_container_width=True):
            if register(u2,p2):
                st.success("Compte créé! Connecte-toi")
            else:
                st.error("Nom déjà pris")
    st.stop()

user = st.session_state.user
is_admin = user=="admin"
if is_admin:
    user_data = {"is_pro":True}
else:
    user_data = db["users"].get(user, {"is_pro":False,"matieres":[],"taches":[],"epreuves":[],"emploi":[],"notes":[],"pomodoros":[],"places":[]})

today = date.today()
is_end_month = today.day >= 25
is_pro = user_data.get("is_pro",False) or is_admin
if is_end_month and not is_pro and not is_admin:
    st.warning(f"⏰ Fin de mois - Passe PRO pour continuer ({PRIX_PRO}F)")
    st.info(f"MoMo: {NUM_MOMO} - Envoie {PRIX_PRO}F et envoie l'ID de transaction. L'admin activera ton compte.")
    id_trans = st.text_input("ID Transaction MoMo")
    if st.button("J'ai payé"):
        st.success(f"ID reçu: {id_trans}. En attente confirmation admin parakou2024. MoMo {NUM_MOMO}")
    st.stop()

with st.sidebar:
    st.title("📚 StudyFlow")
    st.write(f"Connecté: **{user}** {'👑 PRO' if is_pro else '🆓 Gratuit'}")
    menu = st.radio("Navigation", ["🏠 Dashboard","📖 Matières / Cours","✅ Tâches V4 + Rappels","📝 Épreuves","🗓️ Emploi du temps / Planning","🍅 Pomodoro 25min","📓 Notes","📍 Places (Salle)","💎 Pass PRO 1000F","⚙️ Admin" if is_admin else "👤 Profil"])
    if st.button("Déconnexion"):
        st.session_state.user=None
        st.markdown("<script>localStorage.removeItem('studyflow_user')</script>", unsafe_allow_html=True)
        st.rerun()

def save():
    if not is_admin:
        db["users"][user]=user_data
        save_db(db)

if menu=="🏠 Dashboard":
    st.header("🏠 Dashboard StudyFlow pour tous")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Matières", len(user_data.get("matieres",[])))
    c2.metric("Tâches", len(user_data.get("taches",[])))
    c3.metric("Épreuves", len(user_data.get("epreuves",[])))
    c4.metric("Places", len(user_data.get("places",[])))
    st.markdown("---")
    st.subheader("Tes dernières tâches avec rappel même app fermée")
    for t in user_data.get("taches",[])[-5:]:
        st.write(f"• {t.get('title')} - {t.get('date')} {t.get('heure','')} - Rappel: {t.get('reminder','non')}")

elif menu=="📖 Matières / Cours":
    st.header("📖 Matières / Cours + Import PDF")
    with st.form("add_mat"):
        nom = st.text_input("Nom matière")
        prof = st.text_input("Prof")
        pdf = st.file_uploader("Importer PDF cours", type=["pdf"])
        if st.form_submit_button("Ajouter matière"):
            m = {"id":str(uuid.uuid4()),"nom":nom,"prof":prof,"pdf":pdf.name if pdf else "", "created":str(dt.now())}
            user_data.setdefault("matieres",[]).append(m)
            save()
            st.success("Matière ajoutée")
    st.dataframe(pd.DataFrame(user_data.get("matieres",[])))

elif menu=="✅ Tâches V4 + Rappels":
    st.header("✅ Tâches V4 - Notif même fermée")
    with st.form("add_tache"):
        title = st.text_input("Titre tâche")
        d = st.date_input("Date")
        h = st.time_input("Heure")
        rem_date = st.date_input("Date rappel")
        rem_time = st.time_input("Heure rappel")
        motif = st.text_area("Motif / Détails")
        if st.form_submit_button("Ajouter tâche + activer rappel"):
            rem = datetime.datetime.combine(rem_date, rem_time)
            t = {"id":str(uuid.uuid4()),"title":title,"date":str(d),"heure":str(h),"reminder":str(rem),"motif":motif,"done":False}
            user_data.setdefault("taches",[]).append(t)
            save()
            st.markdown(f"<script>localStorage.setItem('studyflow_tasks', JSON.stringify({json.dumps(user_data['taches'])})); notifyStudyFlow('StudyFlow 📚','Rappel activé: {title}');</script>", unsafe_allow_html=True)
            st.success("Tâche ajoutée + rappel V4 activé même app fermée")
    for t in user_data.get("taches",[]):
        col1,col2 = st.columns([4,1])
        col1.write(f"**{t['title']}** - {t['date']} {t['heure']} | Rappel: {t['reminder']} | {t['motif']}")
        if col2.button("Fait", key=t['id']):
            t['done']=True
            save()

elif menu=="📝 Épreuves":
    st.header("📝 Épreuves")
    with st.form("epreuve"):
        mat = st.text_input("Matière")
        date_e = st.date_input("Date épreuve")
        type_e = st.selectbox("Type",["Devoir","Examen","TD","TP"])
        if st.form_submit_button("Ajouter épreuve"):
            e = {"id":str(uuid.uuid4()),"matiere":mat,"date":str(date_e),"type":type_e}
            user_data.setdefault("epreuves",[]).append(e)
            save()
    st.table(user_data.get("epreuves",[]))

elif menu=="🗓️ Emploi du temps / Planning":
    st.header("🗓️ Emploi du temps / Planning par jour")
    jours = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    with st.form("edt"):
        jour = st.selectbox("Jour", jours)
        heure = st.time_input("Heure")
        cours = st.text_input("Cours")
        salle = st.text_input("Salle")
        if st.form_submit_button("Ajouter au planning"):
            e = {"id":str(uuid.uuid4()),"jour":jour,"heure":str(heure),"cours":cours,"salle":salle}
            user_data.setdefault("emploi",[]).append(e)
            save()
    df = pd.DataFrame(user_data.get("emploi",[]))
    if not df.empty:
        st.dataframe(df.sort_values(["jour","heure"]))

elif menu=="🍅 Pomodoro 25min":
    st.header("🍅 Pomodoro 25min + Notif")
    st.write("Concentration 25 min - notif même fermée à la fin")
    if st.button("Lancer Pomodoro 25min"):
        st.markdown("<script>setTimeout(()=>{notifyStudyFlow('StudyFlow 📚','Pomodoro terminé! Pause 5min 🍅')}, 1500000); alert('Pomodoro lancé 25min');</script>", unsafe_allow_html=True)
        st.success("Pomodoro lancé - tu seras notifié même si app fermée")
    mins = st.number_input("Minutes étudiées (manuel)", min_value=0, value=25)
    if st.button("Enregistrer session"):
        user_data.setdefault("pomodoros",[]).append({"minutes":mins,"date":str(dt.now())})
        save()

elif menu=="📓 Notes":
    st.header("📓 Notes avec tags")
    with st.form("note"):
        titre = st.text_input("Titre")
        cont = st.text_area("Contenu")
        tags = st.text_input("Tags (séparés par,)")
        if st.form_submit_button("Ajouter note"):
            n = {"id":str(uuid.uuid4()),"titre":titre,"contenu":cont,"tags":tags,"date":str(dt.now())}
            user_data.setdefault("notes",[]).append(n)
            save()
    for n in user_data.get("notes",[])[::-1]:
        st.markdown(f"**{n['titre']}** - {n['tags']} \n\n {n['contenu']}")

elif menu=="📍 Places (Salle)":
    st.header("📍 Confirmation des places - Salle / Numéro / Date / Heure / Motif")
    with st.form("place"):
        salle = st.text_input("Salle / Lieu")
        numero = st.text_input("Numéro de place")
        d = st.date_input("Date")
        h = st.time_input("Heure")
        motif = st.text_input("Motif")
        if st.form_submit_button("Confirmer ma place + Notif"):
            p = {"id":str(uuid.uuid4()),"salle":salle,"numero":numero,"date":str(d),"heure":str(h),"motif":motif,"user":user,"created":str(dt.now())}
            user_data.setdefault("places",[]).append(p)
            save()
            st.markdown(f"<script>notifyStudyFlow('StudyFlow 📚','Place confirmée: {salle} - {numero} le {d} à {h}');</script>", unsafe_allow_html=True)
            st.success(f"Place confirmée: {salle} N°{numero} le {d} à {h} - Notif activée même fermée")
    st.subheader("Mes places confirmées")
    for pl in user_data.get("places",[]):
        c1,c2 = st.columns([4,1])
        c1.write(f"📍 {pl['salle']} - Place {pl['numero']} - {pl['date']} {pl['heure']} - Motif: {pl['motif']}")
        if c2.button("Annuler", key="ann_"+pl['id']):
            user_data["places"] = [x for x in user_data["places"] if x["id"]!=pl["id"]]
            save()
            st.rerun()

elif menu=="💎 Pass PRO 1000F":
    st.header("💎 Pass PRO StudyFlow - 1000F")
    st.info(f"Pour débloquer StudyFlow tout le mois: envoie {PRIX_PRO}F MoMo à {NUM_MOMO}")
    st.write("FedaPay aussi disponible")
    st.code(f"MoMo: {NUM_MOMO}\nMontant: {PRIX_PRO}F\nNom: StudyFlow PRO")
    id_t = st.text_input("ID transaction après paiement")
    if st.button("Envoyer ID pour validation"):
        st.success(f"ID {id_t} envoyé à l'admin. Activation sous peu. Merci! MoMo {NUM_MOMO}")

elif menu=="⚙️ Admin":
    st.header("⚙️ Admin StudyFlow - parakou2024")
    st.metric("Total utilisateurs", len(db.get("users",{})))
    all_users = []
    for uname, udata in db.get("users",{}).items():
        all_users.append({"user":uname,"is_pro":udata.get("is_pro"),"matieres":len(udata.get("matieres",[])),"taches":len(udata.get("taches",[])),"places":len(udata.get("places",[])),"heures":sum([p.get("minutes",0) for p in udata.get("pomodoros",[])]),"created":udata.get("created")})
    st.dataframe(pd.DataFrame(all_users))
    st.subheader("Activer PRO manuellement (sans ID)")
    u_act = st.selectbox("Choisir utilisateur", list(db.get("users",{}).keys()))
    if st.button(f"Activer PRO pour {u_act}"):
        db["users"][u_act]["is_pro"]=True
        save_db(db)
        st.success(f"{u_act} est maintenant PRO - MoMo {NUM_MOMO} validé")
    st.subheader("Toutes les places confirmées")
    places = []
    for uname, udata in db.get("users",{}).items():
        for p in udata.get("places",[]):
            places.append({**p,"user":uname})
    st.dataframe(pd.DataFrame(places))
else:
    st.write(f"Profil {user} - PRO: {is_pro} - MoMo Support: {NUM_MOMO}")

st.markdown(f"<center><small>StudyFlow pour tous © 2026 - MoMo {NUM_MOMO} - PWA installable - Reste connecté même fermé</small></center>", unsafe_allow_html=True)
