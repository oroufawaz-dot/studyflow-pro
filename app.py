import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta
import re

URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
CELTIS = "0147794002"
MTN = "0196012563"
ADMIN_PWD = "parakou2024"
PRIX = 1000

supabase = create_client(URL, KEY)
st.set_page_config(page_title="Studyflow Parakou", layout="wide")

if "paye" not in st.session_state: st.session_state["paye"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "id_depot_actuel" not in st.session_state: st.session_state["id_depot_actuel"] = ""

def is_pro():
    return st.session_state["paye"] or st.session_state["is_admin"]

def afficher_pub():
    if not is_pro():
        st.info(f"📢 PUB - Passe Pro {PRIX}F! Celtis {CELTIS} / MTN {MTN}")

st.title("📚 Studyflow - Parakou")

with st.sidebar:
    st.header("🔐 Admin")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Connexion admin"):
        if pwd == ADMIN_PWD:
            st.session_state["is_admin"] = True
            st.session_state["paye"] = True
            st.success("Dépôt reçu et merci pour le soutien")

    st.divider()
    if st.session_state["is_admin"]:
        st.success("Compte Pro activé et merci pour le soutien")
        if st.button("Déconnexion"):
            st.session_state["is_admin"] = False
            st.session_state["paye"] = False
            st.rerun()
    else:
        st.header(f"💳 Pro {PRIX}F/mois")
        st.code(f"CELTIS: {CELTIS}\nMTN: {MTN}\n{PRIX}F")
        tel = st.text_input("Ton numéro")
        id_depot = st.text_input("ID du dépôt* (celui du dépôt MoMo)")
        if st.button("Envoyer ID du dépôt", type="primary", use_container_width=True):
            if not id_depot:
                st.error("Mets l'ID du dépôt")
            else:
                try:
                    exist = supabase.table("paiements").select("*").eq("id_depot", id_depot).execute().data
                    if exist:
                        p = exist[0]
                        if p["statut"] == "confirme" and p.get("valide_jusqua") and str(p["valide_jusqua"]) >= str(date.today()):
                            st.session_state["paye"] = True
                            st.session_state["id_depot_actuel"] = id_depot
                            st.success("Dépôt reçu et merci pour le soutien")
                            st.success("Compte Pro activé et merci pour le soutien")
                            st.balloons()
                            st.rerun()
                        elif p["statut"] == "en_attente":
                            st.warning("Dépôt reçu et merci pour le soutien - En attente de confirmation")
                        else:
                            st.error("Abonnement expiré, refais dépôt")
                    else:
                        supabase.table("paiements").insert({"id_depot": id_depot, "telephone": tel, "statut": "en_attente", "montant": PRIX}).execute()
                        st.success("Dépôt reçu et merci pour le soutien - En attente")
                except Exception as e:
                    st.session_state["paye"] = True
                    st.success("Dépôt reçu et merci pour le soutien")

paye = is_pro()

if st.session_state["is_admin"]:
    st.subheader("✅ Admin - Confirmer dépôts + Fin du mois")
    col1, col2 = st.columns(2)
    if col1.button("Voir expirations fin du mois"):
        try:
            fin = date.today().replace(day=28) + timedelta(days=4)
            fin = fin - timedelta(days=fin.day)
            all_p = supabase.table("paiements").select("*").eq("statut","confirme").execute().data
            ex = [x for x in all_p if x.get("valide_jusqua") and str(x["valide_jusqua"]) <= str(fin)]
            st.write(f"{len(ex)} expirent avant {fin}")
            for e in ex:
                st.write(f"- {e['id_depot']} | {e.get('telephone')} | {e.get('valide_jusqua')}")
        except Exception as e:
            st.write(e)
    if col2.button("🔴 RELANCER FIN DU MOIS"):
        try:
            supabase.table("paiements").update({"statut": "expire"}).lt("valide_jusqua", str(date.today())).execute()
            st.success("Relancé - Expirés désactivés")
        except Exception as e:
            st.write(e)
    st.divider()
    try:
        paies = supabase.table("paiements").select("*").order("created_at", desc=True).limit(50).execute().data
        for p in paies:
            c1, c2, c3, c4 = st.columns([2,2,2,2])
            c1.write(f"ID: {p['id_depot']}")
            c2.write(f"{p.get('telephone','-')}")
            c3.write(f"{p['statut']} | {p.get('valide_jusqua','-')}")
            if p['statut']!= 'confirme':
                if c4.button("Confirmer", key=f"cf_{p['id']}"):
                    vj = str(date.today() + timedelta(days=30))
                    supabase.table("paiements").update({"statut": "confirme", "valide_jusqua": vj}).eq("id", p["id"]).execute()
                    st.success(f"Confirmé jusqu'au {vj}")
                    st.rerun()
            else:
                c4.write("✅")
    except Exception as e:
        st.write(e)
    st.divider()

try:
    nb_mat = len(supabase.table("matieres").select("id").execute().data)
    nb_taches = len(supabase.table("taches").select("id").execute().data)
except:
    nb_mat = 0
    nb_taches = 0

tab1, tab2, tab3 = st.tabs(["📘 Matières", "✅ Tâches", "📝 Cours"])

with tab1:
    st.subheader("Matières + Rappel")
    if not paye:
        st.warning(f"Essai: {nb_mat}/1 matière max, 1 fois")
        afficher_pub()
    with st.form("f1", clear_on_submit=True):
        nom = st.text_input("Nom*")
        desc = st.text_area("Description")
        dr = st.date_input("Date rappel", value=date.today())
        if st.form_submit_button("Ajouter"):
            if not paye and nb_mat >= 1:
                st.error("Essai fini - Paye sur 0147794002")
            elif nom:
                supabase.table("matieres").insert({"nom": nom, "description": desc, "date_rappel": str(dr)}).execute()
                st.rerun()
    try:
        for m in supabase.table("matieres").select("*").order("date_rappel").execute().data:
            st.write(f"**{m['nom']}** - {m.get('date_rappel')} - {m.get('description','')}")
            if str(m.get('date_rappel')) == str(date.today()):
                st.warning(f"⏰ Aujourd'hui: {m['nom']}")
            st.divider()
    except Exception as e:
        st.write(e)

with tab2:
    st.subheader("Tâches + Date/Heure rappel")
    if not paye:
        st.warning(f"Essai: {nb_taches}/3 tâches max, pour 1 matière, 1 fois")
        afficher_pub()
    with st.form("f2", clear_on_submit=True):
        titre = st.text_input("Tâche*")
        det = st.text_input("Détails")
        c1, c2, c3 = st.columns(3)
        de = c1.date_input("Date échéance", value=date.today())
        hr = c2.time_input("Heure rappel")
        pr = c3.selectbox("Priorité", ["Basse","Normale","Haute","Urgente"])
        stt = st.selectbox("Statut", ["A faire","En cours","Terminé"])
        if st.form_submit_button("Ajouter"):
            if not paye and nb_taches >= 3:
                st.error("Essai 3 tâches max - Paye 1000F")
            elif titre:
                supabase.table("taches").insert({"titre": titre, "description": det, "date_echeance": str(de), "heure_rappel": str(hr), "priorite": pr, "statut": stt}).execute()
                st.rerun()
    try:
        for t in supabase.table("taches").select("*").order("date_echeance").execute().data:
            st.write(f"**{t['titre']}** | {t.get('date_echeance')} {t.get('heure_rappel')} | {t.get('priorite')} | {t.get('statut')}")
            if t.get('date_echeance') == str(date.today()) and t.get('statut')!= "Terminé":
                st.warning(f"⏰ Aujourd'hui {t.get('heure_rappel')}: {t['titre']}")
            st.divider()
    except Exception as e:
        st.write(e)

with tab3:
    st.subheader("Cours & Épreuves")
    if not paye:
        afficher_pub()
        st.warning(f"Paye {PRIX}F sur {CELTIS}/{MTN} pour PDF illimités")
    else:
        st.success("Dépôt reçu et merci pour le soutien - Compte Pro activé - PDF illimités")
        with st.form("f3", clear_on_submit=True):
            titre = st.text_input("Titre*")
            mat = st.selectbox("Matière", ["Maths","Physique","Chimie","SVT","Philo","Autre"])
            typ = st.selectbox("Type", ["Gratuit","Payant - A vendre"])
            pdf = st.file_uploader("PDF", type=["pdf"])
            if st.form_submit_button("Ajouter PDF"):
                if titre and pdf:
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf.name)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                    supabase.storage.from_(BUCKET).upload(fname, pdf.getvalue())
                    url = supabase.storage.from_(BUCKET).get_public_url(fname)
                    supabase.table("cours").insert({"titre": titre, "matiere": mat, "type": typ, "file_name": fname, "url": url, "prix": PRIX}).execute()
                    st.success("Compte Pro activé et merci pour le soutien - PDF ajouté")
                    st.rerun()
    try:
        for c in supabase.table("cours").select("*").order("created_at", desc=True).execute().data:
            st.write(f"**{c['titre']}** | {c.get('matiere')} | {c.get('type')}")
            if c.get('url'):
                if "Gratuit" in c.get('type','') or paye:
                    st.link_button("Ouvrir", c['url'])
                else:
                    st.write(f"🔒 Payant - {CELTIS}")
            st.divider()
    except Exception as e:
        st.write(e)

if not paye:
    st.divider()
    afficher_pub()
