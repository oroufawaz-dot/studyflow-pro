import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

st.set_page_config(page_title="Studyflow Parakou", page_icon="📚", layout="wide")

SUPABASE_URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
SUPABASE_KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASS = "parakou2024"
PRIX = 1000
NUM_MOMO = "0147794002 / 0196012563"

if "USER_ID" not in st.session_state: st.session_state.USER_ID=""
if "is_admin" not in st.session_state: st.session_state.is_admin=False

if not st.session_state.USER_ID:
    st.title("📚 Studyflow Parakou")
    p=st.text_input("Prénom")
    n=st.text_input("Pseudo que tu donnes")
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
    except: return []

def get_paiements():
    try: return supabase.table("paiements").select("*").eq("telephone",USER_ID).execute().data or []
    except: return []

matieres=load("matieres"); taches=load("taches"); epreuves=load("epreuves"); emplois=load("emplois")
paiements_user=get_paiements()

is_pro=st.session_state.is_admin
for r in paiements_user:
    if r.get("statut")=="confirme" and r.get("valide_jusqua"):
        try:
            if datetime.fromisoformat(str(r["valide_jusqua"]).replace("Z",""))>datetime.now(): is_pro=True
        except: pass

def get_notifs():
    notifs=[]; now=datetime.now(); today=now.date()
    jour_fr=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][today.weekday()]
    
    # TACHES = 10 MIN AVANT
    for t in taches:
        if not t.get("faite"):
            try:
                h_str=t.get("heure","08:00:00")[:5]
                h=datetime.strptime(h_str,"%H:%M").time()
                t_time=datetime.combine(today,h)
                diff=(t_time-now).total_seconds()/60
                if 0 < diff <= 10: notifs.append(f"⏰ Dans {int(diff)}min: Ta tâche '{t['nom']}' doit être accomplie à {h_str}!")
                elif -1 < diff <= 0: notifs.append(f"🚨 MAINTENANT {h_str}: Ta tâche '{t['nom']}' à {h_str}!")
            except: pass
            
    # COURS = 1H AVANT
    for em in emplois:
        if em.get("jour")==jour_fr:
            try:
                hd_str=em.get("heure_debut","09:00:00")[:5]; hf_str=em.get("heure_fin","12:00:00")[:5]
                hd=datetime.strptime(hd_str,"%H:%M").time()
                c_time=datetime.combine(today,hd)
                diff=(c_time-now).total_seconds()/60
                if 0 < diff <= 60: notifs.append(f"🔔 Dans {int(diff)}min (1h avant): Ton cours {em.get('cours')} commence à {hd_str} et finit à {hf_str}. Apprête toi!")
                elif -2 < diff <= 0: notifs.append(f"🚀 MAINTENANT: Cours {em.get('cours')} de {hd_str} à {hf_str}!")
            except: pass
    return notifs

notifs=get_notifs()
if notifs:
    for n in notifs: st.toast(n, icon="🔔")
    with st.container(border=True):
        st.subheader(f"🔔 Rappels ({len(notifs)})")
        for n in notifs:
            if "MAINTENANT" in n: st.error(n)
            else: st.warning(n)

with st.sidebar:
    st.header(f"👤 {USER_ID}")
    st.write("✅ PRO 👑" if is_pro else "🆓 ESSAI")
    if st.button("Changer fenêtre"): st.session_state.USER_ID=""; st.rerun()
    st.divider()
    if not is_pro:
        st.subheader(f"PRO {PRIX}F")
        st.code(NUM_MOMO)
        idd=st.text_input("ID dépôt MoMo")
        if st.button("Envoyer ID",type="primary",use_container_width=True) and idd:
            try:
                if supabase.table("paiements").select("*").eq("id_depot",idd).execute().data: st.error("ID déjà utilisé")
                else:
                    supabase.table("paiements").insert({"id_depot":idd,"telephone":USER_ID,"statut":"en_attente","montant":PRIX}).execute()
                    st.success("Reçu! Attente admin")
            except Exception as e: st.error(f"{e}")
    else: st.success("PRO activé 🎈")
    st.divider()
    if not st.session_state.is_admin:
        with st.expander("Admin"):
            pw=st.text_input("Pass",type="password")
            if st.button("Login") and pw==ADMIN_PASS: st.session_state.is_admin=True; st.rerun()
    else:
        st.error("MODE ADMIN")
        if st.button("Quitter"): st.session_state.is_admin=False; st.rerun()
        try:
            en_attente=supabase.table("paiements").select("*").eq("statut","en_attente").execute().data or []
            for a in en_attente:
                st.write(f"{a['id_depot']} - {a['telephone']}")
                c1,c2=st.columns(2)
                if c1.button("✅",key=f"c{a['id']}"):
                    fin=(datetime.now()+timedelta(days=30)).isoformat()
                    supabase.table("paiements").update({"statut":"confirme","valide_jusqua":fin}).eq("id",a["id"]).execute(); st.rerun()
                if c2.button("❌",key=f"r{a['id']}"): supabase.table("paiements").delete().eq("id",a["id"]).execute(); st.rerun()
        except: pass

if not st.session_state.is_admin and not is_pro and len(matieres)>=1 and len(taches)>=3:
    st.error("⛔ Fin essai - Passe PRO 1000F")
    st.stop()

st.title(f"Bienvenue {USER_ID}!")
tab1,tab2,tab3,tab4=st.tabs(["📖 Matières","✅ Tâches","📝 Épreuves","🗓️ Horaires"])

with tab1:
    lim=is_pro or len(matieres)<1
    nm=st.text_input("Matière")
    if st.button("Ajouter matière") and nm and lim: supabase.table("matieres").insert({"nom":nm,"user_id":USER_ID}).execute(); st.rerun()
    for m in matieres:
        a,b=st.columns([6,1]); a.write(f"📘 {m['nom']}")
        if b.button("🗑️",key=f"dm{m['id']}"): supabase.table("matieres").delete().eq("id",m["id"]).execute(); st.rerun()

with tab2:
    lim=is_pro or len(taches)<3
    c1,c2=st.columns([2,1]); nt=c1.text_input("Tâche"); ht=c2.time_input("Heure",value=datetime.strptime("08:00","%H:%M").time())
    if st.button("Ajouter tâche",use_container_width=True) and nt and lim: supabase.table("taches").insert({"nom":nt,"heure":str(ht),"user_id":USER_ID,"faite":False}).execute(); st.rerun()
    for t in taches:
        a,b,c=st.columns([1,5,1]); chk=a.checkbox("",value=t.get("faite",False),key=f"chk{t['id']}")
        if chk!=t.get("faite",False): supabase.table("taches").update({"faite":chk}).eq("id",t["id"]).execute(); st.rerun()
        b.write(f"⏰ {t.get('heure','08:00')[:5]} - {t['nom']}" if not chk else f"~~{t.get('heure','08:00')[:5]} - {t['nom']}~~")
        if c.button("X",key=f"dt{t['id']}"): supabase.table("taches").delete().eq("id",t["id"]).execute(); st.rerun()

with tab3:
    ne=st.text_input("Épreuve"); de=st.date_input("Date")
    if st.button("Ajouter épreuve") and ne: supabase.table("epreuves").insert({"nom":ne,"date":str(de),"user_id":USER_ID}).execute(); st.rerun()
    for e in epreuves: st.info(f"{e['nom']} - {e.get('date','')}")

with tab4:
    c1,c2,c3=st.columns(3); j=c1.selectbox("Jour",["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]); hd=c2.time_input("Début",value=datetime.strptime("09:00","%H:%M").time()); hf=c3.time_input("Fin",value=datetime.strptime("12:00","%H:%M").time())
    cou=st.text_input("Cours + Salle")
    if st.button("Ajouter horaire",type="primary",use_container_width=True) and cou: supabase.table("emplois").insert({"jour":j,"heure":f"{hd.strftime('%H:%M')}-{hf.strftime('%H:%M')}","heure_debut":str(hd),"heure_fin":str(hf),"cours":cou,"user_id":USER_ID}).execute(); st.rerun()
    for jour in ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]:
        cj=[e for e in emplois if e.get("jour")==jour]
        if cj:
            st.markdown(f"### {jour}")
            for em in sorted(cj,key=lambda x: x.get("heure_debut","")):
                a,b=st.columns([5,1]); a.write(f"⏰ **{em.get('heure_debut','')[:5]}-{em.get('heure_fin','')[:5]}** : {em.get('cours')}")
                if b.button("🗑️",key=f"de{em['id']}"): supabase.table("emplois").delete().eq("id",em["id"]).execute(); st.rerun()
