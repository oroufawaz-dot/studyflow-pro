import streamlit as st
import json
import os
import uuid
import hashlib
import hmac
from datetime import datetime as dt, date, time, timedelta
from pathlib import Path
import pandas as pd

# ============================================================
# STUDYFLOW — application Streamlit
# Installation : pip install streamlit pandas
# Lancement    : streamlit run app.py
#
# Sécurité :
# - Configure STUDYFLOW_ADMIN_ID et STUDYFLOW_ADMIN_PASSWORD
#   dans les variables d'environnement avant de lancer l'app.
# - Les mots de passe des utilisateurs sont hachés.
# - Pour un vrai déploiement multi-utilisateurs, remplace le JSON
#   par une base de données (PostgreSQL/Supabase) et active HTTPS.
# ============================================================

st.set_page_config(
    page_title="StudyFlow",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "StudyFlow"
NUM_MOMO = os.getenv("STUDYFLOW_MOMO", "0147794002 / 0196012563")
PRIX_PRO = int(os.getenv("STUDYFLOW_PRO_PRICE", "1000"))
DB_FILE = Path(os.getenv("STUDYFLOW_DB", "db.json"))

ADMIN_ID = os.getenv("STUDYFLOW_ADMIN_ID", "admin")
ADMIN_PASSWORD = os.getenv("STUDYFLOW_ADMIN_PASSWORD", "")
TRIAL_LIMITS = {
    "taches": 3,
    "matieres": 1,
    "epreuves": 3,
    "emploi": 3,
}

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #0f172a; color: #f8fafc; }
[data-testid="stSidebar"] { background: #111c33; }
[data-testid="stMetric"] {
    background: #17243d; border: 1px solid #293956;
    padding: 14px; border-radius: 12px;
}
.stButton > button {
    border-radius: 9px; min-height: 42px; font-weight: 600;
}
div[data-testid="stAlert"] { border-radius: 10px; }
h1, h2, h3 { color: #f8fafc; }
small { color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)


# -------------------- Base de données JSON --------------------
def empty_user():
    return {
        "password_hash": "",
        "is_pro": False,
        "pro_until": None,
        "matieres": [],
        "taches": [],
        "epreuves": [],
        "emploi": [],
        "notes": [],
        "pomodoros": [],
        "places": [],
        "payments": [],
        "created": str(dt.now()),
    }


def load_db():
    if not DB_FILE.exists():
        return {"users": {}}
    try:
        with DB_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"users": {}}
        data.setdefault("users", {})
        return data
    except (json.JSONDecodeError, OSError):
        st.error("La base db.json est illisible. Fais une copie du fichier avant toute réparation.")
        return {"users": {}}


def save_db(data):
    temp_file = DB_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    temp_file.replace(DB_FILE)


db = load_db()


# -------------------- Authentification --------------------
def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 180_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored):
    # Compatibilité temporaire avec l'ancienne base : les anciens mots
    # de passe étaient enregistrés en clair. Après connexion, on les hache.
    if not stored:
        return False
    if "$" not in stored:
        return hmac.compare_digest(password, stored)
    salt, expected = stored.split("$", 1)
    actual = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual, expected)


def ensure_user_shape(user_data):
    defaults = empty_user()
    for key, value in defaults.items():
        user_data.setdefault(key, value.copy() if isinstance(value, (dict, list)) else value)
    # Migration de l'ancienne clé password vers password_hash
    if "password" in user_data and not user_data.get("password_hash"):
        user_data["password_hash"] = user_data.pop("password")
    return user_data


def login(username, password):
    if username == ADMIN_ID and ADMIN_PASSWORD and hmac.compare_digest(password, ADMIN_PASSWORD):
        st.session_state.user = "admin"
        st.session_state.is_admin = True
        return True

    users = db.get("users", {})
    if username in users:
        data = ensure_user_shape(users[username])
        if verify_password(password, data.get("password_hash", "")):
            # Hacher les anciens mots de passe en clair après connexion.
            if "$" not in data.get("password_hash", ""):
                data["password_hash"] = hash_password(password)
            db["users"][username] = data
            save_db(db)
            st.session_state.user = username
            st.session_state.is_admin = False
            return True
    return False


def register(username, password):
    username = username.strip()
    if len(username) < 3 or len(username) > 24:
        return False, "Le nom doit contenir entre 3 et 24 caractères."
    if not username.replace("_", "").replace("-", "").isalnum():
        return False, "Utilise seulement des lettres, chiffres, _ ou -."
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if username.lower() == "admin" or username in db.get("users", {}):
        return False, "Ce nom d'utilisateur est déjà pris."
    data = empty_user()
    data["password_hash"] = hash_password(password)
    db.setdefault("users", {})[username] = data
    save_db(db)
    return True, "Compte créé. Tu peux maintenant te connecter."


if "user" not in st.session_state:
    st.session_state.user = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


# -------------------- Fonctions métier --------------------
def current_user_data():
    if st.session_state.is_admin:
        return None
    data = db["users"].get(st.session_state.user)
    if data is None:
        return None
    return ensure_user_shape(data)


def save_user_data(data=None):
    if st.session_state.is_admin:
        save_db(db)
        return
    if data is None:
        data = current_user_data()
    if data is not None:
        db["users"][st.session_state.user] = data
        save_db(db)


def has_pro(data):
    if not data:
        return st.session_state.is_admin
    if not data.get("is_pro", False):
        return False
    until = data.get("pro_until")
    if not until:
        return True  # ancien compte PRO sans date d'expiration
    try:
        return dt.fromisoformat(until) >= dt.now()
    except (TypeError, ValueError):
        return False


def count_items(data, key):
    return len(data.get(key, []))


def can_add(data, key):
    return has_pro(data) or count_items(data, key) < TRIAL_LIMITS[key]


def limit_message(key):
    labels = {
        "taches": "tâches",
        "matieres": "matière",
        "epreuves": "épreuves",
        "emploi": "horaires dans le planning",
    }
    return (
        f"Tu as atteint la limite de l'essai gratuit : "
        f"{TRIAL_LIMITS[key]} {labels[key]}. Passe au Pass PRO pour continuer."
    )


def show_limit(data, key):
    if has_pro(data):
        st.caption("💎 PRO actif : accès illimité.")
    else:
        st.caption(
            f"Essai gratuit : {count_items(data, key)}/{TRIAL_LIMITS[key]} "
            f"utilisé(s) pour cette fonctionnalité."
        )


def request_payment(data, amount, transaction_id, method="MTN MoMo"):
    request = {
        "id": str(uuid.uuid4()),
        "user": st.session_state.user,
        "amount": int(amount),
        "method": method,
        "transaction_id": transaction_id.strip(),
        "status": "En attente",
        "created": str(dt.now()),
        "reviewed": None,
    }
    data.setdefault("payments", []).append(request)
    save_user_data(data)


# -------------------- Page de connexion --------------------
if not st.session_state.user:
    st.title("📚 StudyFlow")
    st.subheader("Ton espace d'étude, au même endroit")
    st.write("Organise tes cours, tes tâches, tes épreuves et ton planning.")
    tab_login, tab_register = st.tabs(["🔐 Connexion", "✨ Créer un compte"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
        if submitted:
            if login(username.strip(), password):
                st.rerun()
            else:
                st.error("Identifiants incorrects. Vérifie ton ID et ton mot de passe.")

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Choisis un nom d'utilisateur")
            new_password = st.text_input("Choisis un mot de passe", type="password")
            confirm_password = st.text_input("Confirme le mot de passe", type="password")
            submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
        if submitted:
            if new_password != confirm_password:
                st.error("Les deux mots de passe ne correspondent pas.")
            else:
                ok, message = register(new_username, new_password)
                (st.success if ok else st.error)(message)
    st.info("Essai gratuit : 3 tâches, 1 matière, 3 épreuves et 3 horaires.")
    st.stop()


user = st.session_state.user
is_admin = st.session_state.is_admin
user_data = current_user_data()

if not is_admin and user_data is None:
    st.session_state.user = None
    st.rerun()

is_pro = True if is_admin else has_pro(user_data)


# -------------------- Barre latérale et menu déroulant --------------------
with st.sidebar:
    st.title("📚 StudyFlow")
    st.caption("Apprendre • Planifier • Réussir")
    st.write(f"Connecté : **{user}**")
    st.write("👑 Administrateur" if is_admin else ("💎 Pass PRO" if is_pro else "🆓 Essai gratuit"))

    with st.expander("☰ Ouvrir le menu", expanded=True):
        menu_options = [
            "🏠 Tableau de bord",
            "📖 Matières / Cours",
            "✅ Tâches",
            "📝 Épreuves",
            "🗓️ Emploi du temps",
            "🍅 Pomodoro",
            "📓 Notes",
            "📍 Places / Salles",
            "💎 Pass PRO",
            "👤 Profil",
        ]
        if is_admin:
            menu_options.append("⚙️ Administration")
        menu = st.radio("Navigation", menu_options, label_visibility="collapsed")

    st.divider()
    if not is_admin:
        st.caption("Essai gratuit")
        for key, label in [
            ("taches", "Tâches"),
            ("matieres", "Matières"),
            ("epreuves", "Épreuves"),
            ("emploi", "Horaires"),
        ]:
            used = count_items(user_data, key)
            max_allowed = "∞" if is_pro else str(TRIAL_LIMITS[key])
            st.write(f"{label} : {used}/{max_allowed}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.user = None
        st.session_state.is_admin = False
        st.rerun()


# -------------------- Tableau de bord --------------------
if menu == "🏠 Tableau de bord":
    st.title("🏠 Tableau de bord")
    if is_admin:
        st.info("Tu es connecté en mode administrateur.")
        st.metric("Utilisateurs inscrits", len(db.get("users", {})))
        st.metric(
            "Demandes de paiement",
            sum(len(u.get("payments", [])) for u in db.get("users", {}).values()),
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Matières", count_items(user_data, "matieres"))
        c2.metric("Tâches", count_items(user_data, "taches"))
        c3.metric("Épreuves", count_items(user_data, "epreuves"))
        c4.metric("Horaires", count_items(user_data, "emploi"))

        if is_pro:
            st.success("💎 Ton Pass PRO est actif.")
        else:
            st.info(
                "🆓 Essai gratuit : 3 tâches • 1 matière • 3 épreuves • 3 horaires. "
                "Les autres fonctions de base restent accessibles."
            )
        st.subheader("Prochaines tâches")
        pending = [t for t in user_data.get("taches", []) if not t.get("done")]
        pending.sort(key=lambda x: (x.get("date", ""), x.get("heure", "")))
        if pending:
            for task in pending[:5]:
                st.write(f"• **{task.get('title', 'Sans titre')}** — {task.get('date')} à {task.get('heure', '')}")
        else:
            st.write("Aucune tâche en attente.")
        st.subheader("Prochaines épreuves")
        exams = sorted(user_data.get("epreuves", []), key=lambda x: x.get("date", ""))
        if exams:
            for exam in exams[:5]:
                st.write(f"• **{exam.get('matiere', 'Matière')}** — {exam.get('date')} ({exam.get('type', 'Épreuve')})")
        else:
            st.write("Aucune épreuve enregistrée.")


# -------------------- Matières --------------------
elif menu == "📖 Matières / Cours":
    st.title("📖 Matières et cours")
    show_limit(user_data, "matieres")
    if can_add(user_data, "matieres"):
        with st.form("add_subject"):
            name = st.text_input("Nom de la matière")
            teacher = st.text_input("Nom du professeur (facultatif)")
            room = st.text_input("Salle (facultatif)")
            pdf = st.file_uploader("Ajouter un PDF de cours (facultatif)", type=["pdf"])
            submitted = st.form_submit_button("Ajouter la matière")
        if submitted:
            if not name.strip():
                st.error("Entre le nom de la matière.")
            else:
                saved_pdf = ""
                if pdf:
                    folder = Path("uploads") / user
                    folder.mkdir(parents=True, exist_ok=True)
                    safe_name = f"{uuid.uuid4().hex}_{Path(pdf.name).name}"
                    target = folder / safe_name
                    target.write_bytes(pdf.getvalue())
                    saved_pdf = str(target)
                user_data.setdefault("matieres", []).append({
                    "id": str(uuid.uuid4()),
                    "nom": name.strip(),
                    "prof": teacher.strip(),
                    "salle": room.strip(),
                    "pdf": saved_pdf,
                    "created": str(dt.now()),
                })
                save_user_data(user_data)
                st.success("Matière ajoutée.")
                st.rerun()
    else:
        st.warning(limit_message("matieres"))
        st.button("Voir le Pass PRO", on_click=lambda: st.session_state.update(force_pro=True))
    subjects = user_data.get("matieres", [])
    if subjects:
        for subject in subjects:
            with st.container(border=True):
                st.markdown(f"**{subject.get('nom', 'Matière')}**")
                st.write(f"Professeur : {subject.get('prof') or 'Non précisé'}")
                st.write(f"Salle : {subject.get('salle') or 'Non précisée'}")
                if subject.get("pdf") and Path(subject["pdf"]).exists():
                    with open(subject["pdf"], "rb") as f:
                        st.download_button("Télécharger le PDF", f.read(), file_name=Path(subject["pdf"]).name, key=f"pdf_{subject['id']}")
                if st.button("Supprimer", key=f"del_subject_{subject['id']}"):
                    user_data["matieres"] = [x for x in subjects if x.get("id") != subject["id"]]
                    save_user_data(user_data)
                    st.rerun()
    else:
        st.info("Tu n'as pas encore ajouté de matière.")


# -------------------- Tâches et rappels --------------------
elif menu == "✅ Tâches":
    st.title("✅ Mes tâches")
    show_limit(user_data, "taches")
    if can_add(user_data, "taches"):
        with st.form("add_task"):
            title = st.text_input("Titre de la tâche")
            task_date = st.date_input("Date de la tâche", value=date.today())
            task_time = st.time_input("Heure", value=time(18, 0))
            details = st.text_area("Détails / objectif")
            reminder_on = st.checkbox("Ajouter un rappel")
            reminder_date = st.date_input("Date du rappel", value=date.today(), key="task_reminder_date")
            reminder_time = st.time_input("Heure du rappel", value=time(17, 50), key="task_reminder_time")
            submitted = st.form_submit_button("Enregistrer la tâche")
        if submitted:
            if not title.strip():
                st.error("Le titre de la tâche est obligatoire.")
            else:
                reminder = None
                if reminder_on:
                    reminder = str(dt.combine(reminder_date, reminder_time))
                user_data.setdefault("taches", []).append({
                    "id": str(uuid.uuid4()),
                    "title": title.strip(),
                    "date": str(task_date),
                    "heure": str(task_time),
                    "motif": details.strip(),
                    "reminder": reminder,
                    "done": False,
                    "created": str(dt.now()),
                })
                save_user_data(user_data)
                st.success("Tâche enregistrée.")
                st.rerun()
    else:
        st.warning(limit_message("taches"))
    tasks = user_data.get("taches", [])
    if tasks:
        for task in tasks:
            with st.container(border=True):
                col1, col2, col3 = st.columns([5, 1, 1])
                col1.markdown(f"**{task.get('title', 'Sans titre')}**")
                col1.write(f"{task.get('date')} à {task.get('heure', '')}")
                if task.get("motif"):
                    col1.caption(task["motif"])
                if task.get("reminder"):
                    col1.caption(f"Rappel prévu : {task['reminder']}")
                if task.get("done"):
                    col1.success("Terminée")
                elif col2.button("Fait", key=f"done_{task['id']}"):
                    task["done"] = True
                    task["completed_at"] = str(dt.now())
                    save_user_data(user_data)
                    st.rerun()
                if col3.button("Supprimer", key=f"del_task_{task['id']}"):
                    user_data["taches"] = [x for x in tasks if x.get("id") != task["id"]]
                    save_user_data(user_data)
                    st.rerun()
    else:
        st.info("Aucune tâche pour le moment.")
    st.caption("Note : les rappels automatiques fiables, même navigateur fermé, nécessitent un service de notifications push côté serveur. Le code JavaScript injecté dans Streamlit ne suffit pas à garantir cela.")


# -------------------- Épreuves --------------------
elif menu == "📝 Épreuves":
    st.title("📝 Épreuves, devoirs et examens")
    show_limit(user_data, "epreuves")
    if can_add(user_data, "epreuves"):
        with st.form("add_exam"):
            subject = st.text_input("Matière")
            exam_date = st.date_input("Date de l'épreuve")
            exam_time = st.time_input("Heure de l'épreuve", value=time(8, 0))
            exam_type = st.selectbox("Type", ["Devoir", "Examen", "TD", "TP", "Concours", "Présentation"])
            note = st.text_area("Consignes (facultatif)")
            submitted = st.form_submit_button("Ajouter l'épreuve")
        if submitted:
            if not subject.strip():
                st.error("Indique la matière.")
            else:
                user_data.setdefault("epreuves", []).append({
                    "id": str(uuid.uuid4()),
                    "matiere": subject.strip(),
                    "date": str(exam_date),
                    "heure": str(exam_time),
                    "type": exam_type,
                    "consignes": note.strip(),
                })
                save_user_data(user_data)
                st.success("Épreuve ajoutée.")
                st.rerun()
    else:
        st.warning(limit_message("epreuves"))
    exams = sorted(user_data.get("epreuves", []), key=lambda x: (x.get("date", ""), x.get("heure", "")))
    if exams:
        st.dataframe(pd.DataFrame(exams).drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)
        options = {f"{e.get('matiere')} — {e.get('date')} — {e.get('type')}": e["id"] for e in exams}
        selected = st.selectbox("Supprimer une épreuve", ["— Choisir —"] + list(options.keys()))
        if selected != "— Choisir —" and st.button("Supprimer l'épreuve"):
            selected_id = options[selected]
            user_data["epreuves"] = [e for e in exams if e["id"] != selected_id]
            save_user_data(user_data)
            st.rerun()
    else:
        st.info("Aucune épreuve enregistrée.")


# -------------------- Emploi du temps --------------------
elif menu == "🗓️ Emploi du temps":
    st.title("🗓️ Emploi du temps")
    show_limit(user_data, "emploi")
    if can_add(user_data, "emploi"):
        with st.form("add_schedule"):
            weekday = st.selectbox("Jour", ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"])
            start_time = st.time_input("Heure de début", value=time(8, 0))
            end_time = st.time_input("Heure de fin", value=time(10, 0))
            course = st.text_input("Cours / activité")
            room = st.text_input("Salle")
            submitted = st.form_submit_button("Ajouter au planning")
        if submitted:
            if not course.strip():
                st.error("Le nom du cours est obligatoire.")
            elif end_time <= start_time:
                st.error("L'heure de fin doit être après l'heure de début.")
            else:
                user_data.setdefault("emploi", []).append({
                    "id": str(uuid.uuid4()),
                    "jour": weekday,
                    "debut": str(start_time),
                    "fin": str(end_time),
                    "cours": course.strip(),
                    "salle": room.strip(),
                })
                save_user_data(user_data)
                st.success("Horaire ajouté.")
                st.rerun()
    else:
        st.warning(limit_message("emploi"))
    schedule = user_data.get("emploi", [])
    order = {day: i for i, day in enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"])}
    schedule = sorted(schedule, key=lambda x: (order.get(x.get("jour"), 99), x.get("debut", "")))
    if schedule:
        st.dataframe(pd.DataFrame(schedule).drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)
        schedule_labels = {f"{x.get('jour')} {x.get('debut')} — {x.get('cours')}": x["id"] for x in schedule}
        selected = st.selectbox("Supprimer un horaire", ["— Choisir —"] + list(schedule_labels.keys()))
        if selected != "— Choisir —" and st.button("Supprimer l'horaire"):
            sid = schedule_labels[selected]
            user_data["emploi"] = [x for x in schedule if x["id"] != sid]
            save_user_data(user_data)
            st.rerun()
    else:
        st.info("Ton planning est vide.")


# -------------------- Pomodoro --------------------
elif menu == "🍅 Pomodoro":
    st.title("🍅 Pomodoro et suivi de concentration")
    st.write("Travaille 25 minutes, puis prends une pause de 5 minutes.")
    st.warning("Cette page ne peut pas garantir une notification si le navigateur est fermé. Utilise un minuteur système ou un vrai service push pour les alertes en arrière-plan.")
    if st.button("Démarrer un cycle de 25 minutes"):
        st.session_state.pomodoro_started = str(dt.now())
        st.success("Cycle démarré à " + st.session_state.pomodoro_started)
    with st.form("save_pomodoro"):
        minutes = st.number_input("Minutes réellement étudiées", min_value=1, max_value=600, value=25)
        subject = st.text_input("Matière étudiée (facultatif)")
        comment = st.text_input("Commentaire (facultatif)")
        submitted = st.form_submit_button("Enregistrer ma session")
    if submitted:
        user_data.setdefault("pomodoros", []).append({
            "id": str(uuid.uuid4()),
            "minutes": int(minutes),
            "matiere": subject.strip(),
            "commentaire": comment.strip(),
            "date": str(dt.now()),
        })
        save_user_data(user_data)
        st.success("Session enregistrée.")
    sessions = user_data.get("pomodoros", [])
    total = sum(int(x.get("minutes", 0)) for x in sessions)
    st.metric("Temps d'étude enregistré", f"{total // 60} h {total % 60} min")
    if sessions:
        st.dataframe(pd.DataFrame(sessions).drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)


# -------------------- Notes --------------------
elif menu == "📓 Notes":
    st.title("📓 Carnet de notes")
    with st.form("add_note"):
        title = st.text_input("Titre")
        content = st.text_area("Contenu", height=160)
        tags = st.text_input("Tags (séparés par des virgules)")
        submitted = st.form_submit_button("Enregistrer la note")
    if submitted:
        if not title.strip() or not content.strip():
            st.error("Le titre et le contenu sont obligatoires.")
        else:
            user_data.setdefault("notes", []).append({
                "id": str(uuid.uuid4()),
                "titre": title.strip(),
                "contenu": content.strip(),
                "tags": [x.strip() for x in tags.split(",") if x.strip()],
                "date": str(dt.now()),
            })
            save_user_data(user_data)
            st.success("Note enregistrée.")
            st.rerun()
    search = st.text_input("Rechercher dans mes notes")
    notes = list(reversed(user_data.get("notes", [])))
    for note in notes:
        haystack = (note.get("titre", "") + " " + note.get("contenu", "") + " " + " ".join(note.get("tags", []))).lower()
        if search.lower() in haystack:
            with st.expander(f"📓 {note.get('titre')} — {note.get('date', '')[:10]}"):
                st.write(note.get("contenu", ""))
                st.caption("Tags : " + ", ".join(note.get("tags", [])))
                if st.button("Supprimer la note", key=f"del_note_{note['id']}"):
                    user_data["notes"] = [x for x in user_data["notes"] if x["id"] != note["id"]]
                    save_user_data(user_data)
                    st.rerun()


# -------------------- Places --------------------
elif menu == "📍 Places / Salles":
    st.title("📍 Réservation personnelle de place")
    with st.form("add_place"):
        place_name = st.text_input("Salle / lieu")
        seat_number = st.text_input("Numéro de place")
        place_date = st.date_input("Date", value=date.today())
        place_time = st.time_input("Heure", value=time(8, 0))
        reason = st.text_input("Motif")
        submitted = st.form_submit_button("Enregistrer ma place")
    if submitted:
        if not place_name.strip():
            st.error("Indique le lieu.")
        else:
            user_data.setdefault("places", []).append({
                "id": str(uuid.uuid4()),
                "salle": place_name.strip(),
                "numero": seat_number.strip(),
                "date": str(place_date),
                "heure": str(place_time),
                "motif": reason.strip(),
                "created": str(dt.now()),
            })
            save_user_data(user_data)
            st.success("Place enregistrée dans ton compte.")
            st.rerun()
    for place in user_data.get("places", []):
        with st.container(border=True):
            st.write(f"**{place.get('salle')}** — place {place.get('numero') or 'non précisée'}")
            st.write(f"{place.get('date')} à {place.get('heure')} — {place.get('motif')}")
            if st.button("Annuler", key=f"cancel_place_{place['id']}"):
                user_data["places"] = [x for x in user_data["places"] if x["id"] != place["id"]]
                save_user_data(user_data)
                st.rerun()


# -------------------- Pass PRO / Paiement --------------------
elif menu == "💎 Pass PRO":
    st.title("💎 Pass PRO StudyFlow")
    st.subheader(f"{PRIX_PRO} F CFA / mois")
    st.write("Le Pass PRO enlève les limites sur les tâches, matières, épreuves et horaires.")
    st.info(f"1. Envoie {PRIX_PRO} F CFA par MoMo au : **{NUM_MOMO}**")
    st.info("2. Copie l'ID de transaction fourni par MoMo et envoie-le ci-dessous.")
    st.info("3. L'administrateur vérifie le paiement puis active ton Pass PRO.")
    st.caption("N'envoie jamais ton code PIN MoMo. Seul l'ID de transaction est nécessaire.")
    if is_pro:
        expiry = user_data.get("pro_until")
        st.success("Ton accès PRO est actif." + (f" Expiration : {expiry[:10]}." if expiry else ""))
    else:
        with st.form("payment_request"):
            method = st.selectbox("Moyen de paiement", ["MTN MoMo", "Moov Money", "Autre"])
            transaction_id = st.text_input("ID de transaction")
            submitted = st.form_submit_button("Envoyer la demande de validation")
        if submitted:
            if len(transaction_id.strip()) < 4:
                st.error("Entre un ID de transaction valide.")
            else:
                already_pending = any(
                    p.get("transaction_id") == transaction_id.strip()
                    and p.get("status") == "En attente"
                    for p in user_data.get("payments", [])
                )
                if already_pending:
                    st.warning("Cette demande est déjà en attente.")
                else:
                    request_payment(user_data, PRIX_PRO, transaction_id, method)
                    st.success("Demande enregistrée. L'admin doit vérifier le dépôt avant activation.")
                    st.rerun()
    st.subheader("Historique de mes demandes")
    payments = user_data.get("payments", [])
    if payments:
        st.dataframe(pd.DataFrame(payments).drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)
    else:
        st.caption("Aucune demande de paiement envoyée.")


# -------------------- Profil --------------------
elif menu == "👤 Profil":
    st.title("👤 Mon profil")
    st.write(f"Nom d'utilisateur : **{user}**")
    st.write("Statut : **PRO**" if is_pro else "**Essai gratuit**")
    if not is_pro:
        st.write("Limites de l'essai gratuit :")
        st.write("- 3 tâches")
        st.write("- 1 matière")
        st.write("- 3 épreuves")
        st.write("- 3 horaires")
    st.subheader("Changer mon mot de passe")
    with st.form("change_password"):
        old_password = st.text_input("Mot de passe actuel", type="password")
        new_password = st.text_input("Nouveau mot de passe (8 caractères minimum)", type="password")
        confirm_new = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submitted = st.form_submit_button("Changer le mot de passe")
    if submitted:
        if not verify_password(old_password, user_data.get("password_hash", "")):
            st.error("Mot de passe actuel incorrect.")
        elif len(new_password) < 8:
            st.error("Le nouveau mot de passe doit contenir au moins 8 caractères.")
        elif new_password != confirm_new:
            st.error("Les nouveaux mots de passe ne correspondent pas.")
        else:
            user_data["password_hash"] = hash_password(new_password)
            save_user_data(user_data)
            st.success("Mot de passe changé.")


# -------------------- Administration --------------------
elif menu == "⚙️ Administration" and is_admin:
    st.title("⚙️ Administration StudyFlow")
    st.warning("Vérifie le paiement MoMo dans ton application officielle avant d'activer le PRO. Ne valide jamais sur la seule base d'une capture d'écran.")
    users = db.get("users", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Utilisateurs", len(users))
    c2.metric("Comptes PRO actifs", sum(1 for x in users.values() if has_pro(ensure_user_shape(x))))
    c3.metric(
        "Demandes en attente",
        sum(1 for x in users.values() for p in x.get("payments", []) if p.get("status") == "En attente"),
    )

    st.subheader("Demandes de Pass PRO")
    all_requests = []
    for uname, data in users.items():
        ensure_user_shape(data)
        for payment in data.get("payments", []):
            all_requests.append({**payment, "user": uname})
    pending = [p for p in all_requests if p.get("status") == "En attente"]
    if pending:
        for payment in pending:
            with st.container(border=True):
                st.markdown(f"**Utilisateur : {payment['user']}**")
                st.write(f"Montant : {payment.get('amount')} F CFA")
                st.write(f"Moyen : {payment.get('method')}")
                st.write(f"ID transaction : `{payment.get('transaction_id')}`")
                st.write(f"Envoyé le : {payment.get('created')}")
                days = st.selectbox("Durée du Pass PRO", [30, 90, 180, 365], index=0, key=f"days_{payment['id']}")
                col1, col2 = st.columns(2)
                if col1.button("✅ Confirmer le paiement et activer PRO", key=f"approve_{payment['id']}"):
                    # L'administrateur doit vérifier le dépôt dans l'application MoMo.
                    target_user = db["users"][payment["user"]]
                    target_user["is_pro"] = True
                    target_user["pro_until"] = str(dt.now() + timedelta(days=int(days)))
                    for item in target_user.get("payments", []):
                        if item.get("id") == payment["id"]:
                            item["status"] = "Approuvé"
                            item["reviewed"] = str(dt.now())
                    save_db(db)
                    st.success(f"PRO activé pour {payment['user']} pendant {days} jours.")
                    st.rerun()
                if col2.button("❌ Refuser la demande", key=f"reject_{payment['id']}"):
                    target_user = db["users"][payment["user"]]
                    for item in target_user.get("payments", []):
                        if item.get("id") == payment["id"]:
                            item["status"] = "Refusé"
                            item["reviewed"] = str(dt.now())
                    save_db(db)
                    st.success("Demande refusée.")
                    st.rerun()
    else:
        st.info("Aucune demande en attente.")

    st.subheader("Liste des utilisateurs")
    rows = []
    for uname, data in users.items():
        ensure_user_shape(data)
        rows.append({
            "Utilisateur": uname,
            "PRO actif": has_pro(data),
            "Expiration PRO": data.get("pro_until") or "—",
            "Matières": len(data.get("matieres", [])),
            "Tâches": len(data.get("taches", [])),
            "Épreuves": len(data.get("epreuves", [])),
            "Horaires": len(data.get("emploi", [])),
            "Inscription": data.get("created", ""),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Activer / prolonger PRO manuellement")
    if users:
        selected_user = st.selectbox("Utilisateur", list(users.keys()))
        duration = st.selectbox("Durée", [30, 90, 180, 365], key="manual_duration")
        if st.button("Activer PRO manuellement"):
            target = users[selected_user]
            target["is_pro"] = True
            target["pro_until"] = str(dt.now() + timedelta(days=int(duration)))
            save_db(db)
            st.success(f"PRO activé pour {selected_user}.")
            st.rerun()
    else:
        st.info("Aucun utilisateur inscrit.")

    st.subheader("Exporter les demandes de paiement")
    if all_requests:
        st.download_button(
            "Télécharger CSV des paiements",
            data=pd.DataFrame(all_requests).to_csv(index=False).encode("utf-8"),
            file_name="studyflow_paiements.csv",
            mime="text/csv",
        )


# -------------------- Pied de page --------------------
st.divider()
st.caption(
    f"StudyFlow © {date.today().year} • Support MoMo : {NUM_MOMO} • "
    "Sauvegarde locale dans db.json"
)
