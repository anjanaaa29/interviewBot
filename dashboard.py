import streamlit as st
import pandas as pd
import plotly.express as px
import os
from groq import Groq
from dotenv import load_dotenv
import urllib.parse

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# Constants
HR_RESULTS_FILE = "hr_results.json"
TECH_RESULTS_FILE = "tech_results.json"
MAX_COURSES = 5
MAX_JOBS = 5

def display_table(data, label):
    """Display data in a formatted table"""
    if not data:
        st.warning(f"No {label} data found.")
        return

    df = pd.DataFrame(data)
    columns = ["candidate_id", "domain", "question", "answer", "score", "feedback"]
    existing_cols = [col for col in columns if col in df.columns]
    df = df[existing_cols]
    st.markdown(f"### {label} Feedback")
    st.dataframe(df.style.highlight_max(subset=['score'], color='lightgreen'), 
                use_container_width=True)

def generate_domain_feedback(domain, hr_data, tech_data):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Combine all answers for context
    combined_answers = " ".join([item.get("answer", "") for item in (hr_data + tech_data)])

    prompt = f"""
    The candidate has completed an interview for the domain: {domain}.

    Based on their responses below, suggest short and precise:
    1. The top 3 technical topics or concepts they should focus on next.
    2. Any soft skills or HR-related improvements.
    3. Career advice or learning path to become job-ready in this domain.

    Answers:
    {combined_answers}

    Give feedback in bullet points and be specific to the domain.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a career guidance coach."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

def fetch_course_links(domain):
    """Return only course search links based on the predicted domain"""
    query = urllib.parse.quote_plus(f"free {domain} course")
    course_links = [
        ("Coursera", f"https://www.coursera.org/search?query={query}&price=1"),
        ("edX", f"https://www.edx.org/search?q={query}&price=Free"),
        ("Udemy", f"https://www.udemy.com/courses/search/?q={query}&price=price-free"),
        ("freeCodeCamp", f"https://www.google.com/search?q=site%3Afreecodecamp.org+{query}"),
        ("YouTube", f"https://www.youtube.com/results?search_query={query}")
    ]
    return course_links

def display_course_recommendations(domain):
    """Display only course platform links for the predicted domain"""
    st.subheader("🎓 Free Course Search Links")
    st.caption(f"Based on your interest in `{domain}`")

    course_links = fetch_course_links(domain)

    for name, url in course_links:
        st.markdown(f"- [{name}]({url})", unsafe_allow_html=True)

def search_job_portals(domain, location):
    query = urllib.parse.quote_plus(f"{domain} jobs in {location}")
    return [
        ("LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={query}&location={urllib.parse.quote_plus(location)}"),
        ("Indeed", f"https://in.indeed.com/jobs?q={query}&l={urllib.parse.quote_plus(location)}"),
        ("Glassdoor", f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={query}&locT=C&locId=115&locKeyword={urllib.parse.quote_plus(location)}"),
        ("Naukri", f"https://www.naukri.com/{query}-jobs-in-{urllib.parse.quote_plus(location)}")
    ]

def fetch_jobs_with_agent(domain, location="India"):
    """Agentic job search wrapper: combines reasoning + actionable links"""
    st.subheader("💼 AI-Powered Job Recommendations")
    st.caption(f"Based on your interest in `{domain}` and location `{location}`")

    planning_prompt = f"""
    You're helping a fresher in the {domain} domain find jobs.
    What 5 job titles or roles should they search for as a beginner?
    Respond as a comma-separated list.
    """
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a job planning assistant."},
            {"role": "user", "content": planning_prompt}
        ]
    )

    job_roles = response.choices[0].message.content.strip()
    st.write(job_roles)

    st.markdown("#### 🔗 Search Job Portals")
    job_links = search_job_portals(domain, location)
    for name, url in job_links:
        st.markdown(f"- [{name}]({url})", unsafe_allow_html=True)

def show_dashboard(hr_data, tech_data, candidate_id, domain):
    """Main dashboard function"""
    if not candidate_id:
        st.error("❌ Candidate ID is missing.")
        return

    if not hr_data and not tech_data:
        st.warning("⚠️ No interview data found.")
        return

    num_hr = len(hr_data)
    num_tech = len(tech_data)
    total_questions = num_hr + num_tech
    total_hr_score = sum(item.get("score", 0) for item in hr_data)
    total_tech_score = sum(item.get("score", 0) for item in tech_data)
    avg_score = round((total_hr_score + total_tech_score) / total_questions, 2) if total_questions > 0 else 0

    st.title("📊 Interview Performance Dashboard")
    st.markdown(f"**Candidate ID:** `{candidate_id}` | **Domain:** `{domain}`")

    st.subheader("📊 Your Performance Summary")
    cols = st.columns(3)
    cols[0].metric("HR Score", f"{total_hr_score}/{num_hr*10}", help="Your total HR score out of possible points")
    cols[1].metric("Tech Score", f"{total_tech_score}/{num_tech*10}", help="Your total Technical score out of possible points")
    cols[2].metric("Overall Average", f"{avg_score}/10", delta=f"{(avg_score-5):.1f} vs baseline" if avg_score else None)

    tab1, tab2 = st.tabs(["📈 Score Analysis", "📝 Detailed Feedback"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(names=["HR", "Technical"], values=[num_hr, num_tech], title="Question Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_bar = px.bar(x=["HR", "Technical"],
                             y=[total_hr_score/num_hr if num_hr else 0, total_tech_score/num_tech if num_tech else 0],
                             title="Average Scores",
                             labels={'x': 'Round', 'y': 'Average Score'})
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        display_table(hr_data, "HR Round")
        display_table(tech_data, "Technical Round")

        st.header("📌 Personalized Feedback")
        with st.spinner("Generating feedback based on your answers..."):
            feedback = generate_domain_feedback(domain, hr_data, tech_data)
            st.markdown(feedback)

    display_course_recommendations(domain)
    fetch_jobs_with_agent(domain)

    st.divider()
    st.caption("ℹ️ Recommendations powered by Groq AI")
