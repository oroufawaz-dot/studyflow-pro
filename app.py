import streamlit as st
st.markdown('<link rel="manifest" href="manifest.json"><link rel="apple-touch-icon" href="0e3309b2-d8ee-6996-3018-5d74e8147d8d.jpeg"><link rel="icon" href="0e3309b2-d8ee-6996-3018-5d74e8147d8d.jpeg"><meta name="apple-mobile-web-app-title" content="StudyFlow"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">', unsafe_allow_html=True)
st.markdown('<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script><script>window.OneSignalDeferred=window.OneSignalDeferred||[];OneSignalDeferred.push(async function(OneSignal){await OneSignal.init({appId:"00000000-0000-0000-0000-000000000000"});});</script><script>if("serviceWorker" in navigator){navigator.serviceWorker.register("sw.js");} if("Notification" in window){Notification.requestPermission();}</script>', unsafe_allow_html=True)

from supabase import create_client
from datetime import datetime, timedelta, date
import base64
import re
import requests

SUPABASE_URL = "https://wxxmkklrdktsgaxyidnc.supabase.co"
SUPABASE_KEY = "sb_publishable_YOvG0CvpU9h47--gNP3eYg_85vr90gc"
BUCKET = "Epreuves"
BUCKET2 = "epreuves"
ADMIN_PASS = "parakou2024"
PRIX = 1000
NUM_MOMO = "0147794002 / 0196012563"
CELTIS = "0147794002"
MTN = "0196012563"

st.set_page_config(page_title="Studyflow Parakou", page_icon="📚", layout="wide")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if "USER_ID" not in st.session_state: st.session_state.USER_ID=""
if "is_admin" not in st.session_state: st.session_state.is_admin=False
if "paye" not in st.session_state: st.session_state.paye=False
if "essai_utilise" not in st.session_state: st.session_state.essai_utilise=False

def send_push(title, body):
    try:
        st.markdown(f"<script>if('Notification' in window && Notification.permission==='granted'){{new Notification('{title}', {{body:'{body[:50]}', icon:'0e3309b2-d8ee-6996-3018-5d74e8147d8d.jpeg'}});}} if(window.OneSignal){{OneSignal.User.PushSubscription.optIn();}}</script>", unsafe_allow_html=True)
    except: pass

if not st.session_state.USER_ID:
    st.title("📚 Studyflow Parakou")
    p=st.text_input("Prénom")
    n=st.text_input("Pseudo que tu donnes ex: TleD01")
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

matieres=load("matieres"); taches=load("taches"); epreuves=load("epreuves"); emplois=load("emplois"); cours_list=load("cours")
paiements_user=get_paiements()

is_pro=st.session_state.is_admin or st.session_state.paye
for r in paiements_user:
    if r.get("statut")=="confirme" and r.get("valide_jusqua"):
        try:
            if datetime.fromisoformat(str(r["valide_jusqua"]).replace("Z",""))>datetime.now(): is_pro=True
        except: pass

def afficher_pub():
    if not is_pro:
        st.info("📢 PUB - Studyflow Pro à 1000F seulement! Supprime les pubs + PDF illimités. Paye sur 0147794002 / 0196012563")
        st.image("https://via.placeholder.com/728x90?text=PUB+Studyflow+Pro+1000F", use_column_width=True)

def get_notifs():
    notifs=[]; now=datetime.now(); today=now.date()
    jour_fr=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][today.weekday()]
    for t in taches:
        if not t.get("faite") and not t.get("statut")=="Terminé":
            try:
                d_str=t.get("date", t.get("date_echeance",str(today))); h_str=t.get("heure", t.get("heure_rappel","19:00:00"))[:5]
                try: d=datetime.strptime(d_str,"%Y-%m-%d").date()
                except: d=today
                if d==today:
                    h=datetime.strptime(h_str,"%H:%M").time()
                    t_time=datetime.combine(today,h)
                    diff=(t_time-now).total_seconds()/60
                    if 0 < diff <= 10: notifs.append(f"⏰ Dans {int(diff)}min (10min avant): Tâche à accomplir '{t.get('nom',t.get('titre'))}' [{t.get('matiere','')}] à {h_str}")
                    elif -1 < diff <= 0: notifs.append(f"🚨 MAINTENANT {h_str}: Tâche '{t.get('nom',t.get('titre'))}' à faire!")
            except: pass
    for e in epreuves:
        try:
            d_str=e.get("date",""); h_str=e.get("heure","19:00:00")[:5]
            try: d=datetime.strptime(d_str,"%Y-%m-%d").date()
            except: continue
            if d==today:
                h=datetime.strptime(h_str,"%H:%M").time()
                e_time=datetime.combine(today,h)
                diff=(e_time-now).total_seconds()/60
                if 0 < diff <= 10: notifs.append(f"📝 Dans {int(diff)}min: Épreuve '{e['nom']}' [{e.get('matiere','')}] à {h_str} - Durée {e.get('duree','')}")
        except: pass
    for em in emplois:
        if em.get("jour")==jour_fr:
            try:
                hd_str=em.get("heure_debut","16:00:00")[:5]; hf_str=em.get("heure_fin","18:00:00")[:5]
                hd=datetime.strptime(hd_str,"%H:%M").time()
                c_time=datetime.combine(today,hd)
                diff=(c_time-now).total_seconds()/60
                if 0 < diff <= 60: notifs.append(f"🔔 Dans {int(diff)}min (1h avant): Cours {em.get('cours')} [{em.get('matiere','')}] commence à {hd_str} finit à {hf_str}. Apprête toi!")
                elif -2 < diff <= 0: notifs.append(f"🚀 MAINTENANT: Cours {em.get('cours')} de {hd_str} à {hf_str}!")
            except: pass
    return notifs

notifs=get_notifs()
if notifs:
    for n in notifs:
        st.toast(n, icon="🔔")
        send_push("Studyflow Parakou", n)
    with st.container(border=True):
        st.subheader(f"🔔 Rappels Téléphone ({len(notifs)}) - Dès que réseau connecté + Push")
        for n in notifs:
            if "MAINTENANT" in n: st.error(n)
            else: st.warning(n)

afficher_pub()

with st.sidebar:
    st.header(f"👤 {USER_ID}")
    st.write("✅ PRO 👑" if is_pro else f"🆓 ESSAI - {len(matieres)}/1 mat / {len(taches)}/3 tâches")
    if st.button("Changer fenêtre"): st.session_state.USER_ID=""; st.rerun()
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
                    st.success("Reçu! Attente admin - Dépôt reçu et merci pour le soutien")
            except Exception as e: st.error(f"{e}")
    else: st.success("PRO activé 🎈 Compte Pro activé et merci pour le soutien - Dépôt reçu et merci pour le soutien")
    st.divider()
    if not st.session_state.is_admin:
        with st.expander("Admin"):
            pw=st.text_input("Mot de passe",type="password")
            if st.button("Login") and pw==ADMIN_PASS: st.session_state.is_admin=True; st.session_state.paye=True; st.rerun()
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

if not st.session_state.is_admin and not is_pro and len(matieres)>=1 and len(taches)>=3:
    st.error("⛔ Fin essai gratuit - Au plus 3 tâches pour 1 matière utilisable 1 fois - Passe PRO 1000F sur 0147794002 / 0196012563")
    afficher_pub()
    st.stop()

st.title(f"Bienvenue {USER_ID}!")
c1,c2,c3=st.columns(3); c1.metric("Matières",len(matieres)); c2.metric("Tâches restantes",len([x for x in taches if not x.get("faite")])); c3.metric("Statut","PRO 👑" if is_pro else "Essai")

tab1,tab2,tab3,tab4,tab5=st.tabs(["📖 Matières (Essai 1 max)","✅ Tâches liées (Essai 3 max)","📝 Épreuves liées","🗓️ Horaires liés","📚 Cours & PDF"])

liste_mat = [m['nom'] for m in matieres]

with tab1:
    if not is_pro: st.warning(f"Essai gratuit: {len(matieres)}/1 matière utilisée. Utilisable 1 fois.")
    nm=st.text_input("Nouvelle matière ex: Math Tle D")
    desc_m=st.text_area("Description matière")
    d_rappel=st.date_input("Date rappel matière", value=date.today())
    if st.button("Ajouter matière"):
        if not is_pro and len(matieres)>=1:
            st.error("Essai gratuit terminé! Tu as déjà utilisé ta 1 matière gratuite. Active Compte Pro pour illimité.")
            st.session_state.essai_utilise=True
        elif nm:
            supabase.table("matieres").insert({"nom":nm,"description":desc_m,"date_rappel":str(d_rappel),"user_id":USER_ID}).execute(); st.rerun()
    for m in matieres:
        a,b=st.columns([6,1]); a.write(f"📘 {m['nom']} - Rappel: {m.get('date_rappel','')} | {m.get('description','')}")
        if b.button("🗑️",key=f"dm{m['id']}"): supabase.table("matieres").delete().eq("id",m["id"]).execute(); st.rerun()

with tab2:
    if not is_pro: st.warning(f"Essai gratuit: {len(taches)}/3 tâches. Au plus 3 tâches pour une matière, utilisable 1 fois.")
    st.markdown("**Tâche liée à une matière et une épreuve**")
    cc1,cc2,cc3=st.columns(3)
    nt=cc1.text_input("Ex: exo math")
    mat_sel=cc2.selectbox("Matière", [""]+liste_mat)
    ep_sel=cc3.selectbox("Lier à épreuve", [""]+[f"{e['id']}-{e['nom']}" for e in epreuves])
    c1,c2,c3=st.columns(3)
    dt=c1.date_input("Date", value=datetime(2026,9,10))
    ht=c2.time_input("Heure",value=datetime.strptime("19:00","%H:%M").time())
    prio=c3.selectbox("Priorité", ["Basse","Normale","Haute","Urgente"])
    if st.button("Ajouter tâche liée",type="primary",use_container_width=True) and nt:
        if not is_pro and len(taches)>=3:
            st.error("Essai gratuit: 3 tâches max atteint! Passe en Compte Pro pour illimité sur 0147794002")
            st.session_state.essai_utilise=True
        else:
            eid=int(ep_sel.split("-")[0]) if ep_sel else None
            supabase.table("taches").insert({"nom":nt,"titre":nt,"matiere":mat_sel,"date":str(dt),"date_echeance":str(dt),"heure":str(ht),"heure_rappel":str(ht),"priorite":prio,"epreuve_id":eid,"user_id":USER_ID,"faite":False,"statut":"A faire"}).execute(); st.rerun()
    for t in taches:
        a,b,c=st.columns([1,5,1]); chk=a.checkbox("",value=t.get("faite",False),key=f"chk{t['id']}")
        if chk!=t.get("faite",False):
            supabase.table("taches").update({"faite":chk,"statut":"Terminé" if chk else "A faire"}).eq("id",t["id"]).execute()
            if chk: st.balloons(); st.success(f"Success ✅ Tâche '{t.get('nom',t.get('titre'))}' accomplie!"); send_push("Success ✅", f"Tâche {t.get('nom')} accomplie!")
            st.rerun()
        label=f"⏰ {t.get('date',t.get('date_echeance',''))} {t.get('heure',t.get('heure_rappel',''))[:5]} - {t.get('nom',t.get('titre'))} [{t.get('matiere','')}] {t.get('priorite','')}"
        b.write(f"~~{label}~~" if chk else label)
        if c.button("X",key=f"dt{t['id']}"): supabase.table("taches").delete().eq("id",t["id"]).execute(); st.rerun()

with tab3:
    st.markdown("**Épreuve = fichier PDF ou apprendre son cours + durée + heure 19h00**")
    ne=st.text_input("Nom épreuve ex: apprendre son cours")
    c1,c2,c3=st.columns(3)
    mat_e=c1.selectbox("Matière épreuve", [""]+liste_mat, key="mate")
    de=c2.date_input("Date épreuve", value=datetime(2026,9,10), key="de")
    he=c3.time_input("Heure épreuve", value=datetime.strptime("19:00","%H:%M").time(), key="he")
    duree=st.text_input("Durée ex: 2h ou 1h30")
    desc=st.text_area("Description / apprendre son cours")
    pdf=st.file_uploader("Fichier PDF épreuve", type=["pdf"], key="pdf_ep")
    fichier_url=""
    if pdf:
        try:
            file_bytes=pdf.read()
            supabase.storage.from_(BUCKET2).upload(f"{USER_ID}/{pdf.name}", file_bytes, {"content-type":"application/pdf"})
            fichier_url=supabase.storage.from_(BUCKET2).get_public_url(f"{USER_ID}/{pdf.name}")
            st.success("PDF uploadé")
        except Exception as e:
            try: fichier_url=supabase.storage.from_(BUCKET2).get_public_url(f"{USER_ID}/{pdf.name}")
            except: st.error(f"Erreur PDF {e}")
    if st.button("Ajouter épreuve liée") and ne:
        supabase.table("epreuves").insert({"nom":ne,"matiere":mat_e,"date":str(de),"heure":str(he),"duree":duree,"description":desc,"fichier_url":fichier_url,"user_id":USER_ID}).execute(); st.rerun()
    for e in epreuves:
        st.info(f"📝 **{e['nom']}** [{e.get('matiere','')}] - {e.get('date','')} à {e.get('heure','')[:5]} - Durée: {e.get('duree','')}\n\n{e.get('description','')}")
        if e.get("fichier_url"): st.link_button("📄 Ouvrir PDF", e["fichier_url"])
        liees=[t for t in taches if t.get("epreuve_id")==e["id"]]
        if liees: st.caption(f"Tâches liées: {', '.join([t.get('nom',t.get('titre')) for t in liees])}")

with tab4:
    st.markdown("**Cours lié à matière - rappel 1h avant**")
    c1,c2,c3=st.columns(3)
    j=c1.selectbox("Jour",["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"])
    hd=c2.time_input("Début",value=datetime.strptime("16:00","%H:%M").time())
    hf=c3.time_input("Fin",value=datetime.strptime("18:00","%H:%M").time())
    c4,c5=st.columns(2)
    mat_h=c4.selectbox("Matière du cours", [""]+liste_mat, key="math")
    date_c=c5.date_input("Date du cours (optionnel)", value=datetime.now().date())
    cou=st.text_input("Cours ex: Math - Salle 3")
    if st.button("Ajouter horaire lié",type="primary",use_container_width=True) and cou:
        supabase.table("emplois").insert({"jour":j,"date":str(date_c),"heure":f"{hd.strftime('%H:%M')}-{hf.strftime('%H:%M')}","heure_debut":str(hd),"heure_fin":str(hf),"cours":cou,"matiere":mat_h,"user_id":USER_ID}).execute()
        st.success(f"Ajouté {j} {hd.strftime('%H:%M')}-{hf.strftime('%H:%M')}"); st.rerun()
    for jour in ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]:
        cj=[e for e in emplois if e.get("jour")==jour]
        if cj:
            st.markdown(f"### {jour}")
            for em in sorted(cj,key=lambda x: x.get("heure_debut","")):
                a,b=st.columns([5,1]); a.write(f"⏰ **{em.get('heure_debut','')[:5]}-{em.get('heure_fin','')[:5]}** [{em.get('matiere','')}] : {em.get('cours')} - {em.get('date','')}")
                if b.button("🗑️",key=f"de{em['id']}"): supabase.table("emplois").delete().eq("id",em["id"]).execute(); st.rerun()

with tab5:
    st.subheader("Cours & Épreuves à vendre - PDF illimités si PRO")
    if not is_pro:
        afficher_pub()
        st.warning(f"Gratuit = voir seulement. Pour ajouter PDF illimités, Paye {PRIX}F sur {CELTIS} / {MTN}")
    else:
        st.success("Dépôt reçu et merci pour le soutien - Compte Pro activé et merci pour le soutien - PDF illimités")
        with st.form("cours_f", clear_on_submit=True):
            titre = st.text_input("Titre*")
            mat = st.selectbox("Matière", ["Maths","Physique","Chimie","SVT","Philo","Autre"]+liste_mat)
            typ = st.selectbox("Type", ["Gratuit", "Payant - A vendre"])
            pdf2 = st.file_uploader("PDF", type=["pdf"])
            if st.form_submit_button("Ajouter PDF illimité"):
                if titre and pdf2:
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', pdf2.name)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
                    supabase.storage.from_(BUCKET).upload(fname, pdf2.getvalue())
                    url = supabase.storage.from_(BUCKET).get_public_url(fname)
                    supabase.table("cours").insert({"titre": titre, "matiere": mat, "type": typ, "file_name": fname, "url": url, "prix": 0 if typ=="Gratuit" else PRIX, "user_id": USER_ID}).execute()
                    st.success("Compte Pro activé et merci pour le soutien - PDF ajouté! Tu peux en ajouter encore!")
                    st.rerun()
    try:
        for c in supabase.table("cours").select("*").order("created_at", desc=True).execute().data:
            st.write(f"**{c['titre']}** | {c['matiere']} | {c['type']}")
            if c.get('url'):
                if "Gratuit" in c['type'] or is_pro:
                    st.link_button("Ouvrir", c['url'])
                else:
                    st.write(f"🔒 Payant {PRIX}F - {CELTIS} - Essai gratuit ne peut pas ouvrir")
            st.divider()
    except: pass

if not is_pro:
    st.divider()
    afficher_pub()
    st.error("Fin de l'essai gratuit? Passe Pro 1000F - 0147794002 / 0196012563 pour supprimer les pubs")
