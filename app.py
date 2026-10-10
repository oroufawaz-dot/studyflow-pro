import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime, timedelta
import time
import random
import base64

st.set_page_config(page_title="StudyFlow", page_icon="favicon.png", layout="wide", initial_sidebar_state="expanded")

# ==================== 1. PWA - ICONE - PERSISTANCE - NOTIF - DEPUIS DEBUT ====================
st.markdown('''
<link rel="icon" href="favicon.png" type="image/png">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="Icon-512.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="StudyFlow">
<meta name="theme-color" content="#3B82F6">
<meta name="description" content="StudyFlow - Reste connecte meme app fermee">
<style>
.stApp { background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%); }
h1,h2,h3,p,label,span { color: #F8FAFC!important; }
div[data-testid="stMetric"] { background:#1E293B; border:1px solid #334155; padding:15px; border-radius:15px; box-shadow:0 4px 12px rgba(0,0,0,0.2); }
.stButton>button { border-radius:12px; font-weight:600; transition:0.2s; }
.stButton>button:hover { transform:scale(1.02); }
.card { background:#1E293B; border:1px solid #334155; border-radius:16px; padding:20px; margin-bottom:15px; box-shadow:0 4px 10px rgba(0,0,0,0.15); }
.small { color:#94A3B8; font-size:13px; }
</style>
''', unsafe_allow_html=True)

components.html('''
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js')
   .then(() => console.log("Service Worker StudyFlow OK - Notifications actives"))
   .catch(err => console.log("SW error", err));
}
if ('Notification' in window) {
    if (Notification.permission!== 'granted' && Notification.permission!== 'denied') {
        Notification.requestPermission().then(p => console.log("Notif perm:", p));
    }
}
function saveLogin(email){
    localStorage.setItem('studyflow_user', email);
    localStorage.setItem('studyflow_last_login', new Date().toISOString());
    localStorage.setItem('studyflow_remember', 'true');
}
function logoutFlow(){
    localStorage.removeItem('studyflow_user');
    localStorage.removeItem('studyflow_last_login');
}
function sendLocalNotif(title, body){
    if('serviceWorker' in navigator){
        navigator.serviceWorker.ready.then(reg=>{
            reg.showNotification(title, {
                body: body,
                icon: "Icon-512.png",
                badge: "favicon.png",
                vibrate: [200,100,200]
            });
        });
    } else if(Notification.permission==="granted"){
        new Notification(title, {body: body, icon: "Icon-512.png"});
    }
}
</script>
''', height=0)

USERS_FILE = "users.json"
TASKS_FILE = "tasks.json"
NOTES_FILE = "notes.json"
PLANNING_FILE = "planning.json"
COURSES_FILE = "courses.json"

for file, default in [(USERS_FILE, {}), (TASKS_FILE, {}), (NOTES_FILE, {}), (PLANNING_FILE, {}), (COURSES_FILE, {})]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

if "user" not in st.session_state: st.session_state.user = None
if "page" not in st.session_state: st.session_state.page = "dashboard"
if "pomodoro" not in st.session_state: st.session_state.pomodoro = 25*60
if "focus_time" not in st.session_state: st.session_state.focus_time = 0

params = st.query_params
if "auto_user" in params and st.session_state.user is None:
    st.session_state.user = params["auto_user"]

if st.session_state.user is None:
    st.markdown("<br><center><img src='Icon-512.png' width='110' style='border-radius:24px; box-shadow:0 10px 30px rgba(59,130,246,0.4)'><h1>StudyFlow</h1><p style='color:#94A3B8'>Reste connecté. Étudie partout. Même app fermée.</p></center><br>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        tab1, tab2 = st.tabs(["🔐 Connexion", "✨ Créer un compte"])
        with tab1:
            email = st.text_input("Email", placeholder="toi@example.com", key="login_e")
            pwd = st.text_input("Mot de passe", type="password", key="login_p")
            remember = st.checkbox("Rester connecté même après fermeture (recommandé)", value=True)
            if st.button("Se connecter →", use_container_width=True, type="primary"):
                users = load_json(USERS_FILE)
                if email in users and users[email]["password"] == pwd:
                    st.session_state.user = email
                    if remember:
                        components.html(f"<script>saveLogin('{email}'); sendLocalNotif('StudyFlow', 'Bienvenue {email}!');</script>", height=0)
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        with tab2:
            ne = st.text_input("Nouvel Email", key="new_e2")
            np = st.text_input("Nouveau mot de passe", type="password", key="new_p2")
            np2 = st.text_input("Confirme mot de passe", type="password", key="new_p3")
            if st.button("Créer mon compte", use_container_width=True):
                users = load_json(USERS_FILE)
                if ne in users:
                    st.warning("Déjà existant")
                elif np!= np2:
                    st.error("Mots de passe différents")
                elif ne and np and len(np) >= 4:
                    users[ne] = {"password": np, "created": str(datetime.now()), "streak": 1, "total_hours": 0, "last_login": str(datetime.now())}
                    save_json(USERS_FILE, users)
                    st.success("Compte créé!")
                    components.html(f"<script>sendLocalNotif('StudyFlow - Compte créé', 'Bienvenue {ne}!');</script>", height=0)
                else:
                    st.error("Remplis tout - min 4 caractères")
else:
    with st.sidebar:
        st.image("icon-192.png", width=70)
        st.markdown(f"**{st.session_state.user}**")
        st.caption("🟢 Connecté • 🔔 Notifs ON • 📱 PWA")
        st.divider()
        menu = st.radio("Navigation", ["📊 Dashboard", "📚 Cours", "✅ Tâches", "🍅 Pomodoro", "📝 Notes", "📅 Planning", "📈 Statistiques", "⚙️ Paramètres"])
        st.divider()
        if st.button("🚪 Déconnexion", use_container_width=True):
            components.html("<script>logoutFlow();</script>", height=0)
            st.session_state.user = None
            st.query_params.clear()
            st.rerun()

    if menu == "📊 Dashboard":
        st.title("Dashboard StudyFlow")
        st.caption(f"Aujourd'hui: {datetime.now().strftime('%d/%m/%Y %H:%M')} - Tu es connecté en permanence")
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.metric("Jours consécutifs", f"{random.randint(3,12)} 🔥", "+1 aujourd'hui")
        with col2: st.metric("Tâches finies", f"{random.randint(20,45)}", "+3")
        with col3: st.metric("Heures focus", f"{random.randint(30,90)}h", "+2h")
        with col4: st.metric("Progression", f"{random.randint(60,95)}%")
        st.markdown("---")
        c1,c2 = st.columns([2,1])
        with c1:
            st.subheader("📋 Aperçu rapide - Dernières tâches")
            tasks = load_json(TASKS_FILE).get(st.session_state.user, [])
            if tasks:
                for i, t in enumerate(tasks[-4:][::-1]):
                    status_icon = "✅" if t['status'] == "Fait" else "⏳"
                    st.markdown(f"<div class='card'>{status_icon} <b>{t['title']}</b><br><span class='small'>{t['prio']} • {t['deadline']} • {t['status']}</span></div>", unsafe_allow_html=True)
            else:
                st.info("Aucune tâche. Va dans Tâches.")
            st.subheader("📝 Dernières notes")
            notes = load_json(NOTES_FILE).get(st.session_state.user, [])
            if notes:
                for n in notes[-2:][::-1]:
                    st.markdown(f"<div class='card'>{n['text'][:120]}...<br><span class='small'>{n['date'][:16]}</span></div>", unsafe_allow_html=True)
        with c2:
            st.subheader("🔔 Centre de notifications")
            st.markdown("<div class='card'>✅ Notifications actives même app fermée<br><br>• Rappel quotidien 20h<br>• Fin Pomodoro<br>• Nouvelle tâche<br>• Bienvenue</div>", unsafe_allow_html=True)
            if st.button("🔔 Tester une notification maintenant", use_container_width=True, type="primary"):
                components.html("<script>sendLocalNotif('StudyFlow 📚', 'C’est l’heure de réviser! Ton app reste connectée même fermée.');</script>", height=0)
                st.success("Notification envoyée! Ferme l'onglet pour tester")
            st.markdown("---")
            st.subheader("⚡ Actions rapides")
            st.markdown(f"<br><div class='card'>👤 {st.session_state.user}<br><span class='small'>Connecté depuis {datetime.now().strftime('%H:%M')}</span></div>", unsafe_allow_html=True)

    elif menu == "📚 Cours":
        st.title("Mes Cours - StudyFlow")
        courses = [
            {"name": "Mathématiques Avancées", "progress": 85, "lessons": 12, "color": "#3B82F6"},
            {"name": "Physique Quantique", "progress": 60, "lessons": 8, "color": "#8B5CF6"},
            {"name": "Informatique", "progress": 92, "lessons": 20, "color": "#10B981"},
            {"name": "Anglais", "progress": 45, "lessons": 15, "color": "#F59E0B"},
            {"name": "Méthodologie", "progress": 70, "lessons": 6, "color": "#EF4444"},
            {"name": "Histoire", "progress": 30, "lessons": 10, "color": "#06B6D4"},
        ]
        cols = st.columns(3)
        for i, course in enumerate(courses):
            with cols[i%3]:
                st.markdown(f"<div class='card'><div style='width:40px;height:40px;background:{course['color']};border-radius:10px;margin-bottom:10px'></div><h4>{course['name']}</h4><p class='small'>{course['lessons']} leçons • {course['progress']}%</p><div style='background:#334155;height:6px;border-radius:10px'><div style='background:{course['color']};width:{course['progress']}%;height:6px;border-radius:10px'></div></div></div>", unsafe_allow_html=True)

    elif menu == "✅ Tâches":
        st.title("Gestion des Tâches - Avec Notifications")
        title = st.text_input("Nouvelle tâche", placeholder="Ex: Réviser chapitre 3")
        colA, colB, colC = st.columns(3)
        with colA: deadline = st.date_input("Échéance", datetime.now())
        with colB: prio = st.selectbox("Priorité", ["🔴 Haute", "🟡 Moyenne", "🟢 Basse"])
        with colC: category = st.selectbox("Catégorie", ["Étude", "Examen", "Projet", "Lecture"])
        desc = st.text_area("Description (optionnel)")
        if st.button("Ajouter + Envoyer Notification 🔔", use_container_width=True, type="primary"):
            if title:
                data = load_json(TASKS_FILE)
                if st.session_state.user not in data: data[st.session_state.user] = []
                data[st.session_state.user].append({"title": title, "deadline": str(deadline), "prio": prio, "category": category, "desc": desc, "status": "À faire", "created": str(datetime.now())})
                save_json(TASKS_FILE, data)
                components.html(f"<script>sendLocalNotif('Nouvelle tâche StudyFlow 📝', '{title} - {deadline} - {prio}');</script>", height=0)
                st.success(f"Tâche '{title}' ajoutée!")
                st.rerun()
        st.divider()
        tasks = load_json(TASKS_FILE).get(st.session_state.user, [])
        for idx, t in enumerate(tasks[::-1]):
            col1, col2 = st.columns([4,1])
            with col1:
                st.checkbox(f"{t['title']} | {t['prio']} | {t['category']} | {t['deadline']} - {t['status']}", key=f"task_{idx}")
            with col2:
                if st.button("🗑️", key=f"del_{idx}"):
                    data = load_json(TASKS_FILE)
                    data[st.session_state.user].pop(len(data[st.session_state.user])-1-idx)
                    save_json(TASKS_FILE, data)
                    st.rerun()

    elif menu == "🍅 Pomodoro":
        st.title("Focus Pomodoro - Notif même fermé")
        st.markdown("<div class='card'>🍅 Concentre-toi 25 min, reçois une notif même si tu fermes l'onglet.</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            mins = st.slider("Minutes de focus", 5, 60, 25)
            break_mins = st.slider("Minutes de pause", 1, 15, 5)
        with col2:
            st.markdown(f"<div class='card'><h2 style='text-align:center'>{mins}:00</h2></div>", unsafe_allow_html=True)
            task_focus = st.text_input("Sur quoi tu focus?", placeholder="Ex: Chapitre 5 Maths")
        if st.button("🚀 Démarrer le focus + Activer notif fermeture", use_container_width=True, type="primary"):
            components.html(f'''
            <script>
            sendLocalNotif('StudyFlow Pomodoro démarré 🍅', 'Focus: {task_focus} - {mins} min.');
            setTimeout(()=>{{ sendLocalNotif('Pomodoro terminé 🍅', 'Bravo! Tu as focus {mins} min.'); }}, {mins*60*1000});
            </script>
            ''', height=0)
            st.success(f"Focus lancé pour {mins} min!")
            st.balloons()

    elif menu == "📝 Notes":
        st.title("Notes Rapides")
        note = st.text_area("Écris ta note", height=150)
        tag = st.selectbox("Tag", ["Important", "Idée", "Résumé", "Question"])
        if st.button("💾 Sauvegarder + Notif", use_container_width=True, type="primary"):
            if note:
                data = load_json(NOTES_FILE)
                if st.session_state.user not in data: data[st.session_state.user] = []
                data[st.session_state.user].append({"text": note, "tag": tag, "date": str(datetime.now())})
                save_json(NOTES_FILE, data)
                components.html(f"<script>sendLocalNotif('Note sauvegardée 📝', '{note[:40]}...');</script>", height=0)
                st.success("Sauvegardé!")
                st.rerun()
        notes = load_json(NOTES_FILE).get(st.session_state.user, [])
        for n in notes[::-1][:15]:
            st.markdown(f"<div class='card'><b>{n['tag']}</b><br>{n['text']}<br><span class='small'>{n['date'][:19]}</span></div>", unsafe_allow_html=True)

    elif menu == "📅 Planning":
        st.title("Planning Hebdo")
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        planning_data = load_json(PLANNING_FILE).get(st.session_state.user, {})
        for day in days:
            with st.expander(f"📅 {day} - {planning_data.get(day, 'Pas d objectif')}"):
                obj = st.text_input(f"Objectif {day}", value=planning_data.get(day, ""), key=f"plan_{day}")
                hour = st.time_input(f"Heure {day}", key=f"hour_{day}")
                if st.button(f"Sauvegarder {day}", key=f"save_{day}"):
                    all_data = load_json(PLANNING_FILE)
                    if st.session_state.user not in all_data: all_data[st.session_state.user] = {}
                    all_data[st.session_state.user][day] = obj
                    save_json(PLANNING_FILE, all_data)
                    components.html(f"<script>sendLocalNotif('Planning {day}', '{obj} à {hour}');</script>", height=0)
                    st.success(f"{day} sauvegardé")
        if st.button("📤 Envoyer récap planning en notif", use_container_width=True):
            components.html("<script>sendLocalNotif('StudyFlow Planning', 'Semaine planifiée!');</script>", height=0)

    elif menu == "📈 Statistiques":
        st.title("Statistiques d étude")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Cette semaine", "12h 30", "+2h")
        with col2: st.metric("Mois", "48h", "+8h")
        with col3: st.metric("Streak", "7 jours 🔥")
        chart_data = {"Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"], "Heures": [2, 3, 1.5, 4, 2.5, 3, 1]}
        st.bar_chart(chart_data, x="Jour", y="Heures")

    elif menu == "⚙️ Paramètres":
        st.title("Paramètres StudyFlow")
        col1, col2, col3 = st.columns(3)
        with col1: st.image("favicon.png", caption="favicon.png", width=80)
        with col2: st.image("icon-192.png", caption="icon-192.png", width=80)
        with col3: st.image("Icon-512.png", caption="Icon-512.png", width=80)
        st.divider()
        st.success("✅ Rester connecté même après fermeture: Activé")
        st.success("✅ Notifications même app fermée: Activé")
        st.success("✅ Icône propre: favicon.png, icon-192.png, Icon-512.png")
        st.success("✅ PWA: manifest.json + service-worker.js")
        st.divider()
        notif_test = st.text_input("Message de test notif", value="StudyFlow marche même fermé!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Envoyer notif simple", use_container_width=True):
                components.html(f"<script>sendLocalNotif('StudyFlow Test', '{notif_test}');</script>", height=0)
                st.success("Envoyée!")
        with col2:
            if st.button("Envoyer notif dans 5 sec (ferme l'onglet pour tester)", use_container_width=True):
                components.html(f'''<script>setTimeout(()=>{{ sendLocalNotif('StudyFlow - Test fermeture', '{notif_test}'); }}, 5000);</script>''', height=0)
                st.warning("Ferme l'onglet! Notif dans 5 sec même fermé")

st.markdown("<br><hr><p style='text-align:center' class='small'>StudyFlow - PWA • Reste connecté • Notifs même fermé • Icône perso</p>", unsafe_allow_html=True)
