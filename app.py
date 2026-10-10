import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="Studyflow", page_icon="📚", layout="wide")

SUPABASE_URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
SUPABASE_KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASS = "parakou2024"
PRIX = 1000
NUM_MOMO = "0147794002 / 0196012563"

if "USER_ID" not in st.session_state: st.session_state.USER_ID=""
if "is_admin" not in st.session_state: st.session_state.is_admin=False

# --- CONNEXION POUR TOUJOURS - SANS PAQUET QUI PLANTE ---
def save_permanent(uid):
    components.html(f"""
    <script>
    localStorage.setItem("studyflow_user", "{uid}");
    const url = new URL(window.parent.location.href);
    url.searchParams.set("u", "{uid}");
    window.parent.history.replaceState(null, "", url.toString());
    </script>
    """, height=0)

def load_permanent():
    components.html("""
    <script>
    const saved = localStorage.getItem("studyflow_user");
    const params = new URLSearchParams(window.parent.location.search);
    if (saved &&!params.get("u")) {
        const url = new URL(window.parent.location.href);
        url.searchParams.set("u", saved);
        window.parent.location.href = url.toString();
    }
    </script>
    """, height=0)

qp = st.query_params
if "u" in qp and qp["u"]:
    st.session_state.USER_ID = qp["u"]
    save_permanent(qp["u"])
else:
    load_permanent()

if not st.session_state.USER_ID:
    st.title("📚 Studyflow")
    st.caption("Pour tous les élèves - Pas seulement Parakou")
    st.info("💡 Tu resteras connecté pour toujours après cette connexion")
    p=st.text_input("Prénom")
    n=st.text_input("Pseudo ex: TleD01")
    if st.button("Entrer",type="primary",use_container_width=True):
        if p and n:
            uid=f"{p.strip()}{n.strip()}".replace(" ","").lower()
            st.session_state.USER_ID=uid
            save_permanent(uid)
            st.query_params["u"]=uid
            st.rerun()
    st.stop()
else:
    save_permanent(st.session_state.USER_ID)
    st.query_params["u"]=st.session_state.USER_ID

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

# --- NOTIFICATIONS RAPPELS ---
def get_notifs():
    notifs=[]; now=datetime.now(); today=now.date()
    jour_fr=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][today.weekday()]
    for t in taches:
        if not t.get("faite"):
            try:
                d_str=t.get("date",str(today)); h_str=t.get("heure","19:00:00")[:5]
                try: d=datetime.strptime(d_str,"%Y-%m-%d").date()
                except: d=today
                if d==today:
                    h=datetime.strptime(h_str,"%H:%M").time()
                    t_time=datetime.combine(today,h)
                    diff=(t_time-now).total_seconds()/60
                    if 0 < diff <= 10: notifs.append(f"⏰ {int(diff)}min: {t['nom']} à {h_str}")
                    elif -1 < diff <= 0: notifs.append(f"🚨 MAINTENANT: {t['nom']}!")
            except: pass
    for e in epreuves:
        try:
            d_str=e.get("date",""); h_str=e.get("heure","19:00:00")[:5]
            d=datetime.strptime(d_str,"%Y-%m-%d").date()
            if d==today:
                h=datetime.strptime(h_str,"%H:%M").time()
                e_time=datetime.combine(today,h)
                diff=(e_time-now).total_seconds()/60
                if 0 < diff <= 10: notifs.append(f"📝 {int(diff)}min: Épreuve {e['nom']}")
        except: pass
    for em in emplois:
        if em.get("jour")==jour_fr:
            try:
                hd_str=em.get("heure_debut","16:00:00")[:5]
                hd=datetime.strptime(hd_str,"%H:%M").time()
                c_time=datetime.combine(today,hd)
                diff=(c_time-now).total_seconds()/60
                if 0 < diff <= 60: notifs.append(f"🔔 {int(diff)}min: Cours {em.get('cours')} à {hd_str}")
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
    if is_pro: st.write("✅ PRO 👑 - Toujours connecté")
    else: st.write(f"🆓 ESSAI: {len(matieres)}/1 | {len(taches)}/3 | {len(epreuves)}/3 | {len(emplois)}/3")
    st.caption("Stocké dans ton téléphone - Ne se déconnecte plus")
    if st.button("Se déconnecter vraiment"):
        components.html('<script>localStorage.removeItem("studyflow_user");</script>', height=0)
        st.session_state.USER_ID=""; st.query_params.clear(); time.sleep(1); st.rerun()
    st.divider()
    if not is_pro:
        st.subheader(f"PRO {PRIX}F / 30j")
        st.code(NUM_MOMO)
        idd=st.text_input("ID dépôt MoMo")
        if st.button("Envoyer ID",type="primary",use_container_width=True) and idd:
            try:
                if supabase.table("paiements").select("*").eq("id_depot",idd).execute().data: st.error("ID déjà utilisé")
                else:
                    supabase.table("paiements").insert({"id_depot":idd,"telephone":USER_ID,"statut":"en_attente","montant":PRIX}).execute()
                    st.success("Reçu! Attente admin")
            except Exception as e: st.error(f"{e}")
    else: st.success("PRO activé")
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
            st.write(f"{len(en_attente)} en attente")
            for a in en_attente:
                st.write(f"ID:{a['id_depot']} - {a['telephone']}")
                c1,c2=st.columns(2)
                if c1.button("✅",key=f"c{a['id']}"):
                    fin=(datetime.now()+timedelta(days=30)).isoformat()
                    supabase.table("paiements").update({"statut":"confirme","valide_jusqua":fin}).eq("id",a["id"]).execute(); st.rerun()
                if c2.button("❌",key=f"r{a['id']}"): supabase.table("paiements").delete().eq("id",a["id"]).execute(); st.rerun()
        except: pass

st.title(f"Bienvenue {USER_ID}!")
c1,c2,c3,c4=st.columns(4)
c1.metric("Matières",f"{len(matieres)}/1" if not is_pro else len(matieres))
c2.metric("Tâches",f"{len(taches)}/3" if not is_pro else len(taches))
c3.metric("Épreuves",f"{len(epreuves)}/3" if not is_pro else len(epreuves))
c4.metric("Horaires",f"{len(emplois)}/3" if not is_pro else len(emplois))

liste_mat=[m['nom'] for m in matieres]
tab1,tab2,tab3,tab4=st.tabs(["📖 Matières (1)","✅ Tâches (3)","📝 Épreuves (3)","🗓️ Horaires (3)"])

with tab1:
    lim_mat=is_pro or len(matieres)<1
    nm=st.text_input("Matière")
    if st.button("Ajouter matière") and nm:
        if lim_mat: supabase.table("matieres").insert({"nom":nm,"user_id":USER_ID}).execute(); st.rerun()
        else: st.error("⛔ 1 max - Passe PRO")
    for m in matieres:
        a,b=st.columns([6,1]); a.write(f"📘 {m['nom']}")
        if b.button("🗑️",key=f"dm{m['id']}"): supabase.table("matieres").delete().eq("id",m["id"]).execute(); st.rerun()

with tab2:
    lim_tache=is_pro or len(taches)<3
    st.subheader("Créer tâche")
    choix=st.radio("Choisis ton type", ["📝 AVEC ÉPREUVES", "📖 SANS ÉPREUVES - Réviser partie non maîtrisée"], horizontal=False)

    if choix=="📝 AVEC ÉPREUVES":
        st.markdown("### 📝 Avec Épreuves - PDF + horaires + matière")
        n1,c2=st.columns(2)
        nt=n1.text_input("Nom tâche", placeholder="Ex: Faire épreuve Bac 2023", key="nom_avec")
        mat=c2.selectbox("Matière", [""]+liste_mat, key="mat_avec2")
        ep_list=[""]+[f"{e['id']}|{e['nom']} - {e.get('matiere','')} - {e.get('date','')}" for e in epreuves]
        ep_sel=st.selectbox("Choisir PDF / Épreuve", ep_list, key="pdf_avec")
        d1,d2,d3=st.columns(3)
        dt=d1.date_input("Date", value=datetime.now().date(), key="date_avec")
        ht=d2.time_input("Heure", value=datetime.strptime("19:00","%H:%M").time(), key="heure_avec")
        duree=d3.text_input("Durée", placeholder="2h", key="duree_avec")
        desc=st.text_area("Description - Nom + détails", placeholder="Ex: Faire partie A, chronométré 2h", key="desc_avec")
        if ep_sel:
            try:
                eid=int(ep_sel.split("|")[0]); ev=[e for e in epreuves if e["id"]==eid]
                if ev and ev[0].get("fichier_url"): st.link_button("📄 Ouvrir PDF lié", ev[0]["fichier_url"])
            except: pass
        if st.button("✅ Créer tâche AVEC épreuve",type="primary",use_container_width=True):
            if nt and lim_tache:
                eid=int(ep_sel.split("|")[0]) if ep_sel and "|" in ep_sel else None
                supabase.table("taches").insert({"nom":nt,"matiere":mat,"date":str(dt),"heure":str(ht),"duree":duree,"description":desc,"epreuve_id":eid,"type":"avec_epreuve","user_id":USER_ID,"faite":False}).execute(); st.rerun()
            elif not lim_tache: st.error("⛔ 3 max - Passe PRO")

    else:
        st.markdown("### 📖 Sans Épreuves - Reviser partie non maîtrisée")
        st.caption("Pour réviser un chapitre que tu n'as pas bien compris ou un autre truc")
        n1,c2=st.columns(2)
        nt=n1.text_input("Nom tâche", placeholder="Ex: Reviser leçon 3", key="nom_sans")
        mat=c2.selectbox("Matière", [""]+liste_mat, key="mat_sans2")
        d1,d2=st.columns(2)
        dt=d1.date_input("Date", value=datetime.now().date(), key="date_sans")
        ht=d2.time_input("Heure", value=datetime.strptime("16:00","%H:%M").time(), key="heure_sans")
        desc=st.text_area("Description - Apprendre son cours", placeholder="Ex: Apprendre son cours - Chapitre fonction logarithme, je n'ai pas compris la dérivée. Revoir pages 45-50 + exo 12 - Partie non maîtrisée", key="desc_sans")
        duree2=st.text_input("Temps prévu + Horaire", placeholder="Ex: 1h30 de 16h à 17h30", key="duree_sans")
        if st.button("✅ Créer tâche SANS épreuve - Apprendre cours",type="primary",use_container_width=True):
            if nt and lim_tache:
                supabase.table("taches").insert({"nom":nt,"matiere":mat,"date":str(dt),"heure":str(ht),"duree":duree2,"description":desc,"type":"sans_epreuve","user_id":USER_ID,"faite":False}).execute(); st.rerun()
            elif not lim_tache: st.error("⛔ 3 max - Passe PRO")

    st.divider()
    st.subheader("Mes tâches")
    for t in taches:
        a,b,c=st.columns([1,5,1])
        chk=a.checkbox("",value=t.get("faite",False),key=f"chk{t['id']}")
        if chk!=t.get("faite",False):
            supabase.table("taches").update({"faite":chk}).eq("id",t["id"]).execute()
            if chk: st.balloons()
            st.rerun()
        icon="📝" if t.get("type")=="avec_epreuve" else "📖"
        txt=f"{icon} {t.get('date','')} {t.get('heure','')[:5]} - {t['nom']} [{t.get('matiere','')}] Durée:{t.get('duree','')} - {t.get('description','')}"
        b.write(f"~~{txt}~~" if chk else txt)
        if c.button("X",key=f"dt{t['id']}"): supabase.table("taches").delete().eq("id",t["id"]).execute(); st.rerun()

with tab3:
    lim_epreuve=is_pro or len(epreuves)<3
    ne=st.text_input("Nom épreuve")
    c1,c2,c3=st.columns(3)
    mat_e=c1.selectbox("Matière épreuve", [""]+liste_mat, key="mate")
    de=c2.date_input("Date épreuve", value=datetime(2026,9,10), key="de")
    he=c3.time_input("Heure épreuve", value=datetime.strptime("19:00","%H:%M").time(), key="he")
    duree=st.text_input("Durée ex: 2h")
    desc=st.text_area("Description")
    pdf=st.file_uploader("Fichier PDF", type=["pdf"])
    fichier_url=""
    if pdf:
        try:
            file_bytes=pdf.read()
            supabase.storage.from_("epreuves").upload(f"{USER_ID}/{pdf.name}", file_bytes, {"content-type":"application/pdf"})
            fichier_url=supabase.storage.from_("epreuves").get_public_url(f"{USER_ID}/{pdf.name}")
        except:
            try: fichier_url=supabase.storage.from_("epreuves").get_public_url(f"{USER_ID}/{pdf.name}")
            except: pass
    if st.button("Ajouter épreuve") and ne:
        if lim_epreuve:
            supabase.table("epreuves").insert({"nom":ne,"matiere":mat_e,"date":str(de),"heure":str(he),"duree":duree,"description":desc,"fichier_url":fichier_url,"user_id":USER_ID}).execute(); st.rerun()
        else: st.error("⛔ 3 max")
    for e in epreuves:
        st.info(f"📝 {e['nom']} [{e.get('matiere','')}] {e.get('date','')} {e.get('heure','')[:5]} Durée:{e.get('duree','')}\n\n{e.get('description','')}")
        if e.get("fichier_url"): st.link_button("📄 PDF", e["fichier_url"])
        if st.button("🗑️",key=f"depr{e['id']}"): supabase.table("epreuves").delete().eq("id",e["id"]).execute(); st.rerun()

with tab4:
    lim_horaire=is_pro or len(emplois)<3
    c1,c2,c3=st.columns(3)
    j=c1.selectbox("Jour",["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"])
    hd=c2.time_input("Début",value=datetime.strptime("16:00","%H:%M").time())
    hf=c3.time_input("Fin",value=datetime.strptime("18:00","%H:%M").time())
    c4,c5=st.columns(2)
    mat_h=c4.selectbox("Matière cours", [""]+liste_mat, key="math")
    date_c=c5.date_input("Date cours", value=datetime.now().date())
    cou=st.text_input("Cours")
    if st.button("Ajouter horaire",type="primary",use_container_width=True) and cou:
        if lim_horaire:
            supabase.table("emplois").insert({"jour":j,"date":str(date_c),"heure":f"{hd.strftime('%H:%M')}-{hf.strftime('%H:%M')}","heure_debut":str(hd),"heure_fin":str(hf),"cours":cou,"matiere":mat_h,"user_id":USER_ID}).execute(); st.rerun()
        else: st.error("⛔ 3 max")
    for jour in ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]:
        cj=[e for e in emplois if e.get("jour")==jour]
        if cj:
            st.markdown(f"### {jour}")
            for em in sorted(cj,key=lambda x: x.get("heure_debut","")):
                a,b=st.columns([5,1]); a.write(f"⏰ {em.get('heure_debut','')[:5]}-{em.get('heure_fin','')[:5]} [{em.get('matiere','')}] {em.get('cours')} - {em.get('date','')}")
                if b.button("🗑️",key=f"de{em['id']}"): supabase.table("emplois").delete().eq("id",em["id"]).execute(); st.rerun()
