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
st.set_page_config(page_title="Studyflow", layout="wide")

if "paye" not in st.session_state: st.session_state["paye"] = False
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False
if "user_id" not in st.session_state: st.session_state["user_id"] = ""
if "id_depot_actuel" not in st.session_state: st.session_state["id_depot_actuel"] = ""

def is_pro():
    return st.session_state["paye"] or st.session_state["is_admin"]

def afficher_pub():
    if not is_pro():
        st.info(f"📢 PUB - Pro {PRIX}F sans pub! Celtis {CELTIS} / MTN {MTN}")

st.title("📚 Studyflow - Parakou")

# --- FENETRE PERSO ---
if not st.session_state["user_id"] and not st.session_state["is_admin"]:
    st.subheader("🪟 Connexion fenêtre perso")
    st.write("Chaque élève a sa fenêtre perso. Entre ton numéro.")
    uid = st.text_input("Ton numéro / pseudo perso* (ex: 0196012563 ou Alphonse)", key="uid")
    c1, c2 = st.columns(2)
    if c1.button("Ouvrir ma fenêtre", type="primary", use_container_width=True):
        if uid:
            uid = uid.strip()
            st.session_state["user_id"] = uid
            # auto-check si pro
            try:
                paies = supabase.table("paiements").select("*").eq("telephone", uid).eq("statut","confirme").execute().data
                for p in paies:
                    if p.get("valide_jusqua") and str(p["valide_jusqua"]) >= str(date.today()):
                        st.session_state["paye"] = True
                        st.session_state["id_depot_actuel"] = p["id_depot"]
                        break
            except:
                pass
            st.rerun()
    with st.sidebar:
        st.header("🔐 Admin")
        pwd = st.text_input("Mot de passe admin", type="password")
        if st.button("Connexion admin"):
            if pwd == ADMIN_PWD:
                st.session_state["is_admin"] = True
                st.session_state["paye"] = True
                st.success("Dépôt reçu et merci pour le soutien")
                st.rerun()
    st.stop()

USER_ID = st.session_state["user_id"] if st.session_state["user_id"] else "ADMIN"

if st.session_state["user_id"]:
    col_u1, col_u2 = st.columns([3,1])
    col_u1.info(f"🪟 Fenêtre perso: **{USER_ID}** | {'✅ Pro activé' if is_pro() else '🆓 Essai gratuit'}")
    if col_u2.button("Quitter"):
        st.session_state["user_id"] = ""
        st.session_state["paye"] = False
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    if not st.session_state["is_admin"]:
        st.header("🔐 Admin")
        pwd2 = st.text_input("Admin pwd", type="password", key="pwd2")
        if st.button("Connexion"):
            if pwd2 == ADMIN_PWD:
                st.session_state["is_admin"] = True
                st.session_state["paye"] = True
                st.rerun()

    st.divider()
    if st.session_state["is_admin"]:
        st.success("Compte Pro activé et merci pour le soutien - Admin")
        if st.button("Déconnexion admin"):
            st.session_state["is_admin"] = False
            st.session_state["paye"] = False
            st.session_state["user_id"] = ""
            st.rerun()
    else:
        st.header(f"💳 Pro {PRIX}F/mois")
        st.code(f"CELTIS: {CELTIS}\nMTN: {MTN}")
        st.write(f"Fenêtre: {USER_ID}")
        id_depot = st.text_input("ID du dépôt MoMo* (celui du dépôt)", key="iddep")
        if st.button("Envoyer ID du dépôt", type="primary", use_container_width=True):
            if not id_depot:
                st.error("Mets ID du dépôt")
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
                        elif p["statut"] == "en_attente":
                            st.warning("Dépôt reçu et merci pour le soutien - En attente")
                        else:
                            st.error("Expiré - refais dépôt")
                    else:
                        supabase.table("paiements").insert({"id_depot": id_depot, "telephone": USER_ID, "statut": "en_attente", "montant": PRIX}).execute()
                        st.success("Dépôt reçu et merci pour le soutien - En attente de confirmation")
                except Exception as e:
                    st.write(e)

        if is_pro():
            st.success("Compte Pro activé et merci pour le soutien")
        else:
            st.warning("Essai: 1 matière + 3 tâches max, 1 fois, avec pub")

# --- ADMIN PANEL ---
if st.session_state["is_admin"]:
    st.subheader("✅ Admin - Confirmer ID + Fin du mois")
    c1, c2 = st.columns(2)
    if c1.button("Voir qui expire ce mois"):
        try:
            fin = date.today().replace(day=28) + timedelta(days=4)
            fin = fin - timedelta(days=fin.day)
            all_p = supabase.table("paiements").select("*").eq("statut","confirme").execute().data
            ex = [x for x in all_p if x.get("valide_jusqua") and str(x["valide_jusqua"]) <= str(fin)]
            st.write(f"{len(ex)} expirent avant {fin}")
            for e in ex:
                st.write(f"- ID {e['id_depot']} | Tel/Fenêtre {e.get('telephone')} | {e.get('valide_jusqua')}")
        except Exception as e:
            st.write(e)
    if c2.button("🔴 RELANCER FIN DU MOIS"):
        try:
            supabase.table("paiements").update({"statut": "expire"}).lt("valide_jusqua", str(date.today())).execute()
            st.success("Relancé - expirés désactivés")
        except Exception as e:
            st.write(e)
    st.divider()
    try:
        paies = supabase.table("paiements").select("*").order("created_at", desc=True).limit(50).execute().data
        for p in paies:
            a,b,c,d = st.columns([2,2,2,2])
            a.write(f"ID:{p['id_depot']}")
            b.write(f"Fenêtre:{p.get('telephone')}")
            c.write(f"{p['statut']} | {p.get('valide_jusqua','-')}")
            if p['statut']!= 'confirme':
                if d.button("Confirmer", key=f"cf_{p['id']}"):
                    vj = str(date.today() + timedelta(days=30))
                    supabase.table("paiements").update({"statut": "confirme", "valide_jusqua": vj}).eq("id", p["id"]).execute()
                    st.success(f"Confirmé jusqu'au {vj} - Dépôt reçu et merci")
                    st.rerun()
            else:
                d.write("✅")
    except Exception as e:
        st.write(e)
    st.divider()

# --- COMPTEUR ESSAI PAR FENETRE ---
try:
    if st.session_state["is_admin"]:
        nb_mat = 0
        nb_taches = 0
    else:
        nb_mat = len(supabase.table("matieres").select("id").eq("user_id", USER_ID).execute().data)
        nb_taches = len(supabase.table("taches").select("id").eq("user_id", USER_ID).execute().data)
except:
    nb_mat = 0
    nb_taches = 0

paye = is_pro()
tab1, tab2, tab3 = st.tabs(["📘 Matières + Rappel", "✅ Tâches + Date", "📝 Cours"])

with tab1:
    st.subheader(f"Matières - Fenêtre {USER_ID}")
    if not paye:
        st.warning(f"Essai gratuit: {nb_mat}/1 matière max, utilisable une fois")
        afficher_pub()
    with st.form("mat", clear_on_submit=True):
        nom = st.text_input("Nom matière*")
        desc = st.text_area("Description")
        dr = st.date_input("Date rappel", value=date.today())
        if st.form_submit_button("Ajouter"):
            if not paye and nb_mat >= 1:
                st.error("Essai fini pour cette fenêtre - Paye sur 0147794002")
            elif nom:
                supabase.table("matieres").insert({"nom": nom, "description": desc, "date_rappel": str(dr), "user_id": USER_ID}).execute()
                st.rerun()
    try:
        q = supabase.table("matieres").select("*")
        if not st.session_state["is_admin"]:
            q = q.eq("user_id", USER_ID)
        for m in q.order("date_rappel").execute().data:
            st.write(f"**{m['nom']}** | {m.get('date_rappel')} | {m.get('description','')} | Fenêtre: {m.get('user_id')}")
            if str(m.get('date_rappel')) == str(date.today()):
                st.warning(f"⏰ Rappel aujourd'hui: {m['nom']}")
            if st.button("Suppr", key=f"dm_{m['id']}"):
                supabase.table("matieres").delete().eq("id", m["id"]).execute()
                st.rerun()
            st.divider()
    except Exception as e:
        st.write(e)

with tab2:
    st.subheader(f"Tâches - Fenêtre {USER_ID}")
    if not paye:
        st.warning(f"Essai: {nb_taches}/3 tâches max, pour 1 matière, 1 fois")
        afficher_pub()
    with st.form("tach", clear_on_submit=True):
        titre = st.text_input("Tâche*")
        det = st.text_input("Détails")
        c1,c2,c3 = st.columns(3)
        de = c1.date_input("Date échéance", value=date.today())
        hr = c2.time_input("Heure rappel")
        pr = c3.selectbox("Priorité", ["Basse","Normale","Haute","Urgente"])
        stt = st.selectbox("Statut", ["A faire","En cours","Terminé"])
        if st.form_submit_button("Ajouter"):
            if not paye and nb_taches >= 3:
                st.error("Essai 3 max pour cette fenêtre")
            elif titre:
                supabase.table("taches").insert({"titre": titre, "description": det, "date_echeance": str(de), "heure_rappel": str(hr), "priorite": pr, "statut": stt, "user_id": USER_ID}).execute()
                st.rerun()
    try:
        q = supabase.table("taches").select("*")
        if not st.session_state["is_admin"]:
            q = q.eq("user_id", USER_ID)
        for t in q.order("date_echeance").execute().data:
            st.write(f"**{t['titre']}** | {t.get('date_echeance')} {t.get('heure_rappel')} | {t.get('priorite')} | Fenêtre {t.get('user_id')}")
            if t.get('date_echeance') == str(date.today()) and t.get('statut')!="Terminé":
                st.warning(f"⏰ Aujourd'hui {t.get('heure_rappel')}: {t['titre']}")
            cc1,cc2 = st.columns(2)
            if cc1.button("Terminé", key=f"dt_{t['id']}"):
                supabase.table("taches").update({"statut":"Terminé"}).eq("id", t["id"]).execute()
                st.rerun()
            if cc2.button("Suppr", key=f"del_t_{t['id']}"):
                supabase.table("taches").delete().eq("id", t["id"]).execute()
                st.rerun()
            st.divider()
    except Exception as e:
        st.write(e)

with tab3:
    st.subheader(f"Cours - Fenêtre {USER_ID}")
    if not paye:
        afficher_pub()
        st.warning(f"Paye {PRIX}F sur {CELTIS}/{MTN} pour PDF illimités")
    else:
        st.success("Dépôt reçu et merci pour le soutien - Compte Pro activé - PDF illimités")
        with st.form("cours", clear_on_submit=True):
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
                    supabase.table("cours").insert({"titre": titre, "matiere": mat, "type": typ, "file_name": fname, "url": url, "prix": PRIX, "user_id": USER_ID}).execute()
                    st.success("Compte Pro activé et merci pour le soutien - PDF ajouté")
                    st.rerun()
    try:
        q = supabase.table("cours").select("*")
        if not st.session_state["is_admin"]:
            q = q.eq("user_id", USER_ID)
        for c in q.order("created_at", desc=True).execute().data:
            st.write(f"**{c['titre']}** | {c.get('matiere')} | {c.get('type')} | Fenêtre {c.get('user_id')}")
            if c.get('url'):
                if "Gratuit" in c.get('type','') or paye or st.session_state["is_admin"]:
                    st.link_button("Ouvrir PDF", c['url'])
                else:
                    st.write(f"🔒 Payant - {CELTIS}")
            st.divider()
    except Exception as e:
        st.write(e)
