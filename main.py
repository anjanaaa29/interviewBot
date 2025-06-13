import streamlit as st
from streamlit_chat import message
from voice import VoiceRecorder
from domain import identify_domain, client
from hr import generate_hr_questions, evaluate_hr_answer
from technical import generate_technical_questions, evaluate_technical_answer
from storage import save_hr_result, load_hr_results, save_tech_result, load_tech_results
from dashboard import show_dashboard
from chatbot import chatbot_page
import uuid

st.set_page_config(page_title="Mock Interview Bot", layout="centered")

def generate_candidate_id():
    return f"cand-{uuid.uuid4().hex[:6]}"

def initialize_session_state():
    keys_with_defaults = {
        "candidate_id": generate_candidate_id(),
        "user_authenticated": False,
        "current_step": 0,
        "stage": 'start',
        "jd": '',
        "domain": '',
        "hr_qns": [],
        "hr_index": 0,
        "tech_qns": [],
        "tech_index": 0,
        "chat_history": [],
        "recording": False,
        "recording_duration": 20,
        "hr_answers": [],
        "tech_answers": [],
        "page": "interview",
        "voice_recorder": VoiceRecorder(model_size="base"),
        "id_verified": False,
        "id_prompt_shown": False,
        "result_shown": False
    }
    for key, default in keys_with_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def main():
    initialize_session_state() 

    st.title("🧠 AI Interview Bot")

    # initialize session state
    if 'stage' not in st.session_state:
        st.session_state.update({
            'stage': 'start',
            'jd': '',
            'domain': '',
            'hr_qns': [],
            'hr_index': 0,
            'tech_qns': [],
            'tech_index': 0,
            'chat_history': [],
            'recording': False,
            'recording_duration': 20,
            'hr_answers': [],
            'tech_answers': [],
            'candidate_id': generate_candidate_id(),
            'page': "interview",
            'voice_recorder': VoiceRecorder(model_size="base")
        })

    # Display candidate ID
    if st.session_state.candidate_id:
        st.markdown(f"### 🆔 Candidate ID: `{st.session_state.candidate_id}`")

    def display_chat():
        for i, chat in enumerate(st.session_state.chat_history):
            message(chat['msg'], is_user=chat['user'], key=f"chat_{i}")

    def add_message(msg, is_user):
        st.session_state.chat_history.append({'msg': msg, 'user': is_user})

    # Interview stages
    if st.session_state.stage == 'start':
        display_chat()
        jd = st.text_input("Paste Job Description here:", key="jd_input")
        
        if jd and jd != st.session_state.jd:
            st.session_state.jd = jd
            add_message(jd, True)
            
            domain = identify_domain(jd, client)
            st.session_state.domain = domain
            add_message(f"Predicted domain: {domain}. Is this correct? (yes/recheck)", False)
            st.session_state.stage = 'confirm_domain'
            st.rerun()

    elif st.session_state.stage == 'confirm_domain':
        display_chat()

        if st.session_state.get("clear_confirm_domain_input", False):
            st.session_state.confirm_domain_input = ""
            st.session_state.clear_confirm_domain_input = False

        user_input = st.text_input("", key="confirm_domain_input")
        
        if user_input:
            add_message(user_input, True)
            
            if user_input.lower() == 'yes':
                add_message("Shall we start the HR round? Type 'Yes' to proceed", False)
                st.session_state.stage = 'start_hr_prompt'
            elif user_input.lower() == 'recheck':
                domain = identify_domain(st.session_state.jd, client)
                st.session_state.domain = domain

                add_message(f"🔄 Rechecked domain: **{domain}**. Is this correct? (yes/recheck)", False)
                st.session_state.stage = 'confirm_domain'

            st.session_state.clear_confirm_domain_input = True  # Clear input on next rerun
            st.rerun()

    elif st.session_state.stage == 'start_hr_prompt':
        display_chat()
        user_input = st.text_input("", key="start_hr_input")
        if user_input:
            add_message(user_input, True)
            if user_input.lower() == 'yes':
                st.session_state.hr_qns = generate_hr_questions()
                question = st.session_state.hr_qns[0]
                add_message(f"HR Q1: {question}", False)
                st.session_state.stage = 'hr_round'
            st.rerun()

    elif st.session_state.stage == 'hr_round':
        display_chat()
        
        if st.session_state.hr_index < len(st.session_state.hr_qns):
            question = st.session_state.hr_qns[st.session_state.hr_index]
            # st.write(f"**HR Q{st.session_state.hr_index + 1}:** {question}")

            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎙️ Start Recording"):
                    st.session_state.voice_recorder.start_recording()
                    st.session_state.recording = True
                    st.success("Recording started - speak now!")
            
            with col2:
                if st.button("⏹️ Stop & Submit"):
                    if st.session_state.recording:
                        audio_data = st.session_state.voice_recorder.stop_recording()
                        st.session_state.recording = False
                        
                        if audio_data is not None:
                            with st.spinner("Processing your answer..."):
                                transcription = st.session_state.voice_recorder.transcribe(audio_data)
                                transcript = transcription['text']
                                
                                if transcript:
                                    score, feedback, confidence = evaluate_hr_answer(question, transcript)

                                    add_message(transcript, True)
                                    add_message(f"✅ Feedback: {feedback} (Score: {score}/10)", False)

                                    st.session_state.hr_answers.append((transcript, score, feedback))
                                    save_hr_result(st.session_state.candidate_id, {
                                        "question": question,
                                        "answer": transcript,
                                        "score": score,
                                        "feedback": feedback
                                    })

                                    st.session_state.hr_index += 1
                                    if st.session_state.hr_index < len(st.session_state.hr_qns):
                                        next_q = st.session_state.hr_qns[st.session_state.hr_index]
                                        add_message(f"HR Q{st.session_state.hr_index + 1}: {next_q}", False)
                                    else:
                                        add_message("HR round complete! Ready for technical? Types 'Yes' to proceed", False)
                                        st.session_state.stage = 'tech_prompt'
                                    st.rerun()
                                else:
                                    st.error("Could not transcribe your answer. Please try again.")
                        else:
                            st.error("No audio recorded. Please try again.")

    elif st.session_state.stage == 'tech_prompt':
        display_chat()
        user_input = st.text_input("", key="start_tech_input")
        
        if user_input:
            add_message(user_input, True)
            if user_input.lower() == 'yes':
                st.session_state.tech_qns = generate_technical_questions(st.session_state.domain)
                question = st.session_state.tech_qns[0]
                add_message(f"Tech Q1: {question}", False)
                st.session_state.stage = 'tech_round'
            st.rerun()

    elif st.session_state.stage == 'tech_round':
        display_chat()
        if st.session_state.tech_index < len(st.session_state.tech_qns):
            question = st.session_state.tech_qns[st.session_state.tech_index]
            st.write(f"**Tech Q{st.session_state.tech_index + 1}:** {question}")

            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎙️ Start Recording"):
                    st.session_state.voice_recorder.start_recording()
                    st.session_state.recording = True
                    st.success("Recording started - speak now!")
            
            with col2:
                if st.button("⏹️ Stop & Submit"):
                    if st.session_state.recording:
                        audio_data = st.session_state.voice_recorder.stop_recording()
                        st.session_state.recording = False
                        
                        if audio_data is not None:
                            with st.spinner("Processing your answer..."):
                                transcription = st.session_state.voice_recorder.transcribe(audio_data)
                                transcript = transcription['text']
                                
                                if transcript:
                                    score, feedback = evaluate_technical_answer(question, transcript, st.session_state.domain)

                                    add_message(transcript, True)
                                    add_message(f"✅ Feedback: {feedback} (Score: {score}/10)", False)

                                    st.session_state.tech_answers.append((transcript, score, feedback))
                                    save_tech_result(st.session_state.candidate_id, {
                                        "question": question,
                                        "answer": transcript,
                                        "score": score,
                                        "feedback": feedback
                                    })

                                    st.session_state.tech_index += 1
                                    if st.session_state.tech_index < len(st.session_state.tech_qns):
                                        next_q = st.session_state.tech_qns[st.session_state.tech_index]
                                        add_message(f"Tech Q{st.session_state.tech_index + 1}: {next_q}", False)
                                    else:
                                        add_message("Interview complete! Type 'show result' to view your dashboard.", False)
                                        st.session_state.stage = 'result_wait'  # Fixed stage name
                                    st.rerun()
                                else:
                                    st.error("Could not transcribe your answer. Please try again.")
                        else:
                            st.error("No audio recorded. Please try again.")

    elif st.session_state.stage == 'result_wait':
        display_chat()

        # First phase: Verify candidate ID
        if not st.session_state.get("id_verified", False):
            if not st.session_state.get("id_prompt_shown", False):
                add_message("Please enter your candidate ID to view your results", False)
                st.session_state.id_prompt_shown = True
                st.rerun()
            
            user_input = st.text_input("", key="id_input", placeholder="Enter your candidate ID")
            
            if user_input:
                if user_input.strip() == st.session_state.candidate_id:
                    st.session_state.id_verified = True
                    add_message("Candidate ID verified. Type 'show result' to view your interview dashboard", False)
                    st.rerun()
                else:
                    st.error("Incorrect candidate ID. Please try again.")
                    st.rerun()
        
        # Second phase: After ID verification, show results prompt
        elif st.session_state.get("id_verified", False) and not st.session_state.get("result_shown", False):
            user_input = st.text_input("", key="result_input", placeholder="Type 'show result'")
            
            if user_input and user_input.lower().strip() == 'show result':
                # Prepare the data for dashboard
                hr_results = [
                    {
                        "candidate_id": st.session_state.candidate_id,
                        "domain": st.session_state.domain,
                        "question": st.session_state.hr_qns[i],
                        "answer": ans[0],
                        "score": ans[1],
                        "feedback": ans[2]
                    }
                    for i, ans in enumerate(st.session_state.hr_answers)
                ]
                
                tech_results = [
                    {
                        "candidate_id": st.session_state.candidate_id,
                        "domain": st.session_state.domain,
                        "question": st.session_state.tech_qns[i],
                        "answer": ans[0],
                        "score": ans[1],
                        "feedback": ans[2]
                    }
                    for i, ans in enumerate(st.session_state.tech_answers)
                ]
                
                # Save to session state and storage
                st.session_state.hr_data = hr_results
                st.session_state.tech_data = tech_results
                save_hr_result(st.session_state.candidate_id, hr_results)
                save_tech_result(st.session_state.candidate_id, tech_results)
            
                # Mark results as shown
                st.session_state.result_shown = True
                st.rerun()
        
        # Third phase: Show dashboard
        if st.session_state.get("result_shown", False):
            st.markdown("### 📊 INTERVIEW DASHBOARD")
            
            # Call the show_dashboard function with the prepared data
            show_dashboard(
                hr_data=st.session_state.hr_data,
                tech_data=st.session_state.tech_data,
                candidate_id=st.session_state.candidate_id,
                domain=st.session_state.domain
            )

            if st.session_state.page == "chatbot":
                chatbot_page()
            else:
                # Interview result and button layout
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔁 Start New Interview"):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.session_state.stage = 'start'
                        st.rerun()

                with col2:
                    if st.button("💬 Start Chatbot Discussion"):
                        st.session_state.page = "chatbot"
                        st.rerun()
            

if __name__ == "__main__":
    main()