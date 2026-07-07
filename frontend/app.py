import streamlit as st
import requests
import json

API_URL = "https://fitmind-ai-backend-wopz.onrender.com"

st.set_page_config(page_title="Gym AI Coach", page_icon="💪", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("💪 Gym AI Coach")
page = st.sidebar.radio("Navigate", ["Generate Plan", "Chat with Coach", "Member Dashboard"])

# ========================
# PAGE 1 — Generate Plan
# ========================
if page == "Generate Plan":
    st.title("🏋️ Get Your Personalized Plan")
    st.markdown("Fill in your details and get a custom workout + diet plan instantly.")

    with st.form("member_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name")
            member_id = st.text_input("Member ID (e.g. MEM001)")
            age = st.number_input("Age", min_value=10, max_value=80, value=20)
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)

        with col2:
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=175.0)
            goal = st.selectbox("Goal", ["muscle gain", "weight loss", "maintain fitness", "improve stamina"])
            diet_type = st.selectbox("Diet Type", ["vegetarian", "non-vegetarian", "vegan"])
            experience = st.selectbox("Experience Level", ["beginner", "intermediate", "advanced"])

        injuries = st.text_input("Any injuries or limitations? (leave blank if none)", value="None")

        submitted = st.form_submit_button("Generate My Plan 💪")

    if submitted:
        if not name or not member_id:
            st.error("Please fill in Name and Member ID.")
        else:
            with st.spinner("Generating your personalized plan... this takes ~15 seconds"):
                payload = {
                    "member_id": member_id,
                    "name": name,
                    "age": age,
                    "weight": weight,
                    "height": height,
                    "goal": goal,
                    "diet_type": diet_type,
                    "injuries": injuries,
                    "experience": experience
                }
                response = requests.post(f"{API_URL}/generate-plan", json=payload)

                if response.status_code == 200:
                    plan = response.json()["plan"]
                    st.success("Your plan is ready!")
                    st.markdown("---")
                    st.markdown(plan)

                    st.session_state["current_member_id"] = member_id
                    st.session_state["current_name"] = name
                else:
                    st.error("Something went wrong. Make sure the backend is running.")

# ========================
# PAGE 2 — Chat
# ========================
elif page == "Chat with Coach":
    st.title("🤖 Chat with Your AI Coach")
    st.markdown("Ask anything about your workout, diet, recovery, or fitness goals.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    member_id = st.text_input("Enter your Member ID to start chatting", 
                               value=st.session_state.get("current_member_id", ""))

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    question = st.chat_input("Ask your coach...")

    if question and member_id:
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        with st.spinner("Coach is thinking..."):
            payload = {
                "member_id": member_id,
                "question": question,
                "history": st.session_state.chat_history
            }
            response = requests.post(f"{API_URL}/chat", json=payload)

            if response.status_code == 200:
                answer = response.json()["response"]
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.chat_message("assistant").write(answer)
            else:
                st.error("Backend not reachable.")

    elif question and not member_id:
        st.warning("Please enter your Member ID first.")

# ========================
# PAGE 3 — Dashboard
# ========================
elif page == "Member Dashboard":
    st.title("📊 Gym Owner Dashboard")
    st.markdown("View all registered members and their plans.")

    if st.button("Refresh Members"):
        st.session_state["refresh"] = True

    response = requests.get(f"{API_URL}/all-members")

    if response.status_code == 200:
        members = response.json()["members"]

        if not members:
            st.info("No members registered yet.")
        else:
            st.success(f"Total Members: {len(members)}")
            st.markdown("---")

            for m in members:
                with st.expander(f"👤 {m['name']} — {m['member_id']}"):
                    st.write(f"**Goal:** {m['goal']}")
                    st.write(f"**Experience:** {m['experience']}")

                    if st.button(f"View Full Plan — {m['member_id']}", key=m['member_id']):
                        detail = requests.get(f"{API_URL}/member/{m['member_id']}")
                        if detail.status_code == 200:
                            st.markdown(detail.json()["plan"])
    else:
        st.error("Could not fetch members. Make sure backend is running.")