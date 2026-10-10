import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import PyPDF2

st.set_page_config(page_title="Studyflow Parakou", page_icon="📚", layout="wide")

SUPABASE_URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
SUPABASE_KEY = "TON_CLE_ANON_ICI"  # <-- REMETS TA CLÉ
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASS = "parakou2024"
PRIX = 1000
NUM_MOMO = "0147794002 / 0196012563"

if "USER_ID" not in st.session_state: st.session_state.USER_ID=""
if "is_admin" not in st.session_state: st.session_state.is_admin=False

if not st.session_state.USER_ID:
    st.title("📚 Studyflow Parakou")
    p=st.text_input("Prénom"); n=st.text_input("Pseudo unique")
    if st.button("Entrer",type="primary",use_container_width=True):
        if p and n:
            st.session_state.USER_ID=f"{p.strip()}{n.strip()}".replace(" ","").lower()
            st.rerun()
    st.stop()

USER_ID=st.session_state.USER_ID

def load(table):
    try:
        if st.session_state.is_admin:
            return supabase.table(table).select("*").order("created_at",desc=True).execute().data or []
        else:
            return supabase.table(table).select("*").eq("user_id",USER_ID).order("created_at",desc=True).execute().data or []
    except Exception as e:
        # st.error(f"Erreur {table}: {e}") # cache l'erreur pour pas planter
        return []

def get_paiements():
    try:
        return supabase.table("paiements").select("*").eq("telephone",USER_ID).execute().data or []
    except:
        return []

matieres=load("matieres"); taches=load("taches"); epreuves=load("epreuves"); emplois=load("emplois")
paiements_user=get_paiements()

# Vérif PRO
is_pro=st.session_state.is_admin
for r in paiements_user:
    if r.get("statut")=="confirme" and r.get("valide_jusqua"):
        try:
            if datetime.fromisoformat(str(r["valide_jusqua"]).replace("Z",""))>datetime.now(): 
                is_pro=True
        except: pass

# Blocage fin du mois
if not st.session_state.is_admin and not is_pro and len(matieres)>=1:
    st.error("⛔ ACCES BLOQUE - Fin du mois d'essai")
    st.warning(f"Dépôt {PRIX}F sur {NUM_MOMO} + tape ton ID à gauche. L'admin confirme à sa place.")
    st.stop()

# Rappels
def get_notifs():
    notifs=[]; today=datetime.now().date()
    jour=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][today.weekday()]
    for t in taches:
        if not t.get("faite"): notifs.append(f"📌 À faire: {t['nom']}")
    for em in emplois:
        if em.get("jour")==jour: notifs.append(f"📚 Aujourd'hui {em.get('heure','')}: {em.get('cours')}")
    for ep in epreuves:
        try:
            d=datetime.fromisoformat(str(ep.get("date",""))).date(); diff=(d-today).days
            if diff==3: notifs.append(f"⚠️ Épreuve dans 3j: {ep['nom']}")
            if diff==1: notifs.append(f"🚨 Épreuve DEMAIN: {ep['nom']}")
            if diff==0: notifs.append(f"🔥 Épreuve AUJOURD'HUI: {ep['nom']}")
        except: pass
    return notifs

notifs=get_notifs()

with st.sidebar:
    st.header(f"👤 {USER_ID}")
    st.write("✅ PRO 👑" if is_pro else "🆓 ESSAI")
    if notifs:
        st.markdown(f"### 🔔 {len(notifs)} Rappels")
        for n in notifs: st.warning(n)
    else: st.success("✅ À jour!")
    st.divider()
    if st.button("Changer fenêtre"): st.session_state.USER_ID=""; st.rerun()
    st.divider()
    if not is_pro:
        st.subheader(f"PRO {PRIX}F/mois")
        st.code(NUM_MOMO)
        idd=st.text_input("ID dépôt")
        if st.button("Envoyer ID",type="primary",use_container_width=True):
            if idd:
                try:
                    exists=supabase.table("paiements").select("*").eq("id_depot",idd).execute().data
                    if exists: st.error("ID déjà utilisé")
                    else:
                        supabase.table("paiements").insert({"id_depot":idd,"telephone":USER_ID,"statut":"en_attente","montant":PRIX}).execute()
                        st.success("Dépôt reçu et merci pour le soutien - Attente admin")
                except Exception as e: st.error(f"Erreur: {e}")
    else: st.success("Compte Pro activé et merci pour le soutien 🎈")
    st.divider()
    if not st.session_state.is_admin:
        with st.expander("Admin"):
            pw=st.text_input("Mot de passe",type="password")
            if st.button("Login") and pw==ADMIN_PASS: st.session_state.is_admin=True; st.rerun()
    else:
        st.error("MODE ADMIN")
        if st.button("Quitter admin"): st.session_state.is_admin=False; st.rerun()
        try:
            en_attente=supabase.table("paiements").select("*").eq("statut","en_attente").execute().data or []
            for a in en_attente:
                st.write(f"ID:{a['id_depot']} - {a['telephone']}")
                c1,c2=st.columns(2)
                if c1.button("✅",key=f"c{a['id']}"):
                    fin=(datetime.now()+timedelta(days=30)).isoformat()
                    supabase.table("paiements").update({"statut":"confirme","valide_jusqua":fin}).eq("id",a["id"]).execute(); st.rerun()
                if c2.button("❌",key=f"r{a['id']}"): supabase.table("paiements").delete().eq("id",a["id"]).execute(); st.rerun()
        except Exception as e: st.error(f"Erreur paiements: {e}")

st.title(f"Bienvenue {USER_ID}!")
c1,c2,c3=st.columns(3); c1.metric("Matières",len(matieres)); c2.metric("Tâches",len(taches)); c3.metric("Statut","PRO" if is_pro else "Essai")
tab1,tab2,tab3,tab4,tab5=st.tabs(["📖 Matières","✅ Tâches","📝 Épreuves","🗓️ Horaires","📊 Stats"])

with tab1:
    lim=is_pro or len(matieres)<1
    nm=st.text_input("Matière ex: Math Tle D")
    if st.button("Ajouter") and nm and lim: 
        supabase.table("matieres").insert({"nom":nm,"user_id":USER_ID}).execute(); st.rerun()
    for m in matieres:
        a,b=st.columns([6,1]); a.write(f"📘 {m['nom']}")
        if b.button("🗑️",key=f"dm{m['id']}"): supabase.table("matieres").delete().eq("id",m["id"]).execute(); st.rerun()

with tab2:
    lim=is_pro or len(taches)<3
    nt=st.text_input("Nouvelle tâche")
    if st.button("Ajouter tâche",use_container_width=True) and nt and lim: supabase.table("taches").insert({"nom":nt,"user_id":USER_ID,"faite":False}).execute(); st.rerun()
    for t in taches:
        a,b,c=st.columns([1,6,1]); chk=a.checkbox("",value=t.get("faite",False),key=f"chk{t['id']}")
        if chk!=t.get("faite",False): supabase.table("taches").update({"faite":chk}).eq("id",t["id"]).execute(); st.rerun()
        b.write(f"~~{t['nom']}~~" if chk else t['nom'])
        if c.button("X",key=f"dt{t['id']}"): supabase.table("taches").delete().eq("id",t["id"]).execute(); st.rerun()

with tab3:
    ne=st.text_input("Nom épreuve"); de=st.date_input("Date épreuve")
    if st.button("Ajouter épreuve") and ne: supabase.table("epreuves").insert({"nom":ne,"date":str(de),"user_id":USER_ID}).execute(); st.rerun()
    for e in epreuves: st.info(f"📝 {e['nom']} - {e.get('date','')}")

with tab4:
    st.subheader("🗓️ Horaires de cours")
    c1,c2,c3=st.columns(3)
    j=c1.selectbox("Jour",["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"])
    hd=c2.time_input("Début")
    hf=c3.time_input("Fin")
    cou=st.text_input("Matière + Salle ex: Math - Salle 3")
    if st.button("Ajouter horaire",type="primary",use_container_width=True) and cou:
        supabase.table("emplois").insert({"jour":j,"heure":f"{hd.strftime('%Hh%M')}-{hf.strftime('%Hh%M')}","heure_debut":str(hd),"heure_fin":str(hf),"cours":cou,"user_id":USER_ID}).execute()
        st.success(f"Ajouté: {j} {hd}-{hf}"); st.rerun()
    st.divider()
    for jour in ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]:
        cj=[e for e in emplois if e.get("jour")==jour]
        if cj:
            st.markdown(f"### {jour}")
            for em in sorted(cj,key=lambda x: x.get("heure_debut","")):
                colA,colB=st.columns([5,1])
                colA.write(f"⏰ **{em.get('heure')}** : {em.get('cours')}")
                if colB.button("🗑️",key=f"de{em['id']}"): supabase.table("emplois").delete().eq("id",em["id"]).execute(); st.rerun()

with tab5:
    if st.session_state.is_admin:
        st.header("Stats")
        try:
            all_p=supabase.table("paiements").select("*").execute().data or []
            users=set([x["telephone"] for x in all_p if x.get("telephone")])
            for u in users:
                cm=len(supabase.table("matieres").select("*").eq("user_id",u).execute().data or [])
                st.write(f"👤 {u} -> {cm} matières")
        except: st.write("Pas de stats")
