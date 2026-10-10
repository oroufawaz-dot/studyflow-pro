import streamlit as st

st.set_page_config(page_title="StudyFlow Pro", page_icon="📚", layout="wide")

# --- SIDEBAR PRO ---
st.sidebar.header("🔓 Débloquer Pro")
code = st.sidebar.text_input("Code Pro", placeholder="ex: PRO1000")

# .upper() = accepte pro1000, Pro1000, PRO1000
if code.upper() == "PRO1000":
    is_pro = True
    st.sidebar.success("✅ Pro activé !")
else:
    is_pro = False
    if code != "":
        st.sidebar.error("❌ Code invalide")

st.sidebar.divider()
st.sidebar.markdown("""
**💰 Pour avoir ton code Pro:**
1. Envoie 1000F par MoMo
2. Envoie la capture sur WhatsApp
3. Je t'envoie ton code

📱 **MTN:** 01 XX XX XX XX
""")

st.title("📚 StudyFlow Pro")
st.write("Gère tes cours et tâches - Bénin")

if is_pro:
    st.balloons()
    st.success("Mode Pro activé - Rappels WhatsApp débloqués")
else:
    st.info("👈 Entre ton code Pro à gauche pour débloquer")
