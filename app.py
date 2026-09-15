"""Interactive Streamlit dashboard for the Internship Skill Analyzer."""

import html
import hashlib
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAIError

from src.chatbot import (
    BOT_NAME,
    answer_question_with_trace,
    chat_settings,
    check_agent_health,
    classify_openai_error,
    configured_health,
    dataset_context,
)
from src.candidate_profile import (
    CandidateUploadError,
    build_candidate_profile,
    clear_candidate_session,
    extract_candidate_document,
    generate_application_guidance,
    rank_candidate_matches,
)
from src.coaching import build_coaching_question
from src.extract_skills import SKILL_CATALOG, extract_skills
from src.learning_plan import (
    TIMEFRAME_OPTIONS,
    build_learning_plan_evidence,
    generate_learning_plan,
)
from src.personalization import build_personalization_context, profile_fingerprint
from src.retrieval import selection_fingerprint
from src.skill_gap import calculate_skill_gap, rank_missing_skills, score_postings


ROOT = Path(__file__).resolve().parent
POSTINGS_PATH = ROOT / "data/processed/us/postings_with_skills.csv"
DIFFICULTY_PATH = ROOT / "data/processed/us/analysis/posting_difficulty.csv"

st.set_page_config(page_title="Internship Skill Analyzer", page_icon="🎯", layout="wide")
st.markdown("""
<style>
.stApp { background: #f7f8fc; }
[data-testid="stSidebar"] { background: #111827; }
[data-testid="stSidebar"] * { color: #f9fafb; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] [data-baseweb="input"] *,
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #111827 !important;
}
[data-testid="stSidebar"] input::placeholder {
    color: #6b7280 !important;
    opacity: 1;
}
[data-testid="stSidebar"] [data-baseweb="tag"] * {
    color: #1e3a8a !important;
}
[data-testid="stMetric"] { background:white; border:1px solid #e5e7eb; border-radius:14px;
padding:16px 18px; box-shadow:0 4px 14px rgba(15,23,42,.05); }
.hero { padding:28px 30px; border-radius:20px; color:white; margin-bottom:20px;
background:linear-gradient(120deg,#172554 0%,#1d4ed8 58%,#0891b2 100%);
box-shadow:0 12px 28px rgba(29,78,216,.2); }
.hero h1 { margin:0 0 8px; font-size:2.35rem; } .hero p { margin:0; color:#dbeafe; }
.eyebrow { color:#1d4ed8; font-weight:700; letter-spacing:.08em; font-size:.76rem; }
.job-card { background:white; border:1px solid #e5e7eb; border-radius:14px; padding:18px 20px; }
.pill { display:inline-block; background:#eff6ff; color:#1d4ed8; border-radius:999px;
padding:4px 10px; margin:3px 4px 3px 0; font-size:.8rem; font-weight:600; }
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load enriched postings and attach their calculated difficulty."""
    postings = pd.read_csv(POSTINGS_PATH).fillna("")
    difficulty = pd.read_csv(DIFFICULTY_PATH).fillna("")
    keep = difficulty[["posting_id", "experience_level", "advanced_skill_count"]]
    data = postings.merge(keep, on="posting_id", how="left")
    data["skills_list"] = data["skills_extracted"].apply(
        lambda value: [skill for skill in str(value).split("|") if skill]
    )
    return data


def skill_frequency(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate skill counts for only the currently visible postings."""
    skills = frame[["posting_id", "skills_list"]].explode("skills_list")
    skills = skills.loc[skills["skills_list"].ne("")]
    return (skills.groupby("skills_list")["posting_id"].nunique().sort_values(ascending=False)
            .rename_axis("skill").reset_index(name="postings"))


if not POSTINGS_PATH.exists() or not DIFFICULTY_PATH.exists():
    st.error("The processed US data is missing. Run Steps 3–5 before opening the dashboard.")
    st.stop()

data = load_data()
with st.sidebar:
    st.markdown("## 🎯 Filters")
    st.caption("Narrow the internship market to what matters to you.")
    search = st.text_input("Search job titles", placeholder="e.g. software, machine learning")
    companies = st.multiselect("Companies", sorted(data["company"].unique()))
    locations = st.multiselect("Locations", sorted(data["location"].unique()))
    all_skills = sorted({skill for skills in data["skills_list"] for skill in skills})
    selected_skills = st.multiselect("Required skills", all_skills)
    levels = st.multiselect("Difficulty", sorted(data["experience_level"].unique()))
    st.divider()
    st.caption("Public structured career feeds · US internships only")

filtered = data.copy()
if search:
    filtered = filtered.loc[filtered["job_title"].str.contains(search, case=False, na=False)]
if companies:
    filtered = filtered.loc[filtered["company"].isin(companies)]
if locations:
    filtered = filtered.loc[filtered["location"].isin(locations)]
if selected_skills:
    filtered = filtered.loc[filtered["skills_list"].apply(
        lambda skills: all(skill in skills for skill in selected_skills))]
if levels:
    filtered = filtered.loc[filtered["experience_level"].isin(levels)]

st.markdown("""
<div class="hero"><div style="font-size:.78rem;font-weight:700;letter-spacing:.12em;color:#bae6fd">
US INTERNSHIP INTELLIGENCE</div><h1>Build the skills employers want.</h1>
<p>Explore current data and software internships, compare demand, and find your next application.</p></div>
""", unsafe_allow_html=True)

catalog_skills = sorted(
    skill for category in SKILL_CATALOG.values() for skill in category
)
with st.expander("🧭 My Skills", expanded=True):
    st.markdown("### My Skills")
    st.caption("Select skills you already have. These choices stay in this browser session and do not change the CSV files.")
    profile_skills = st.multiselect(
        "Skills I already have",
        options=catalog_skills,
        key="profile_skills",
        placeholder="Search for Python, SQL, Tableau…",
    )
    profile_left, profile_right = st.columns([3, 1])
    with profile_left:
        if profile_skills:
            st.success(f"{len(profile_skills)} skill{'s' if len(profile_skills) != 1 else ''} selected")
        else:
            st.info("Select at least one skill to calculate matches and learning priorities.")
    with profile_right:
        st.button(
            "Clear my skills",
            disabled=not profile_skills,
            on_click=lambda: st.session_state.update(profile_skills=[]),
            width="stretch",
        )

    minimum_overlap = st.slider(
        "Minimum skill overlap",
        min_value=0,
        max_value=100,
        value=0,
        step=10,
        disabled=not profile_skills,
        help="Navigation aid only—not a qualification or interview prediction.",
    )

    filtered = score_postings(filtered, profile_skills)
    if profile_skills:
        filtered = filtered.loc[
            filtered["match_percentage"].isna()
            | filtered["match_percentage"].ge(minimum_overlap)
        ].sort_values("match_percentage", ascending=False, na_position="last")
        available_scores = filtered["match_percentage"].dropna()
        gap_metrics = st.columns(3)
        gap_metrics[0].metric(
            "Average skill overlap",
            f"{available_scores.mean():.0f}%" if not available_scores.empty else "Unavailable",
        )
        gap_metrics[1].metric(
            "Strongest overlap",
            f"{available_scores.max():.0f}%" if not available_scores.empty else "Unavailable",
        )
        gap_metrics[2].metric("Visible at threshold", len(filtered))

        recommendations = rank_missing_skills(filtered).head(5)
        st.markdown("#### Learn next")
        if recommendations.empty:
            st.success("You selected every detected skill in the visible postings.")
        else:
            st.caption("Prioritized by how many visible internships request a skill you did not select.")
            st.dataframe(
                recommendations.rename(columns={"skill": "Skill", "posting_count": "Visible postings"}),
                hide_index=True,
                width="stretch",
            )
    else:
        st.caption("Skill-overlap scoring, sorting, and recommendations appear after you select a skill.")

    st.markdown("#### Personalized learning plan")
    plan_left, plan_right = st.columns([2, 1])
    with plan_left:
        timeframe_weeks = st.selectbox(
            "Available time",
            options=TIMEFRAME_OPTIONS,
            format_func=lambda weeks: f"{weeks} weeks",
            help="Choose a planning horizon. This does not predict when you will be job-ready.",
        )
    with plan_right:
        st.write("")
        create_plan = st.button(
            "Create learning plan",
            disabled=not profile_skills,
            width="stretch",
        )
    if create_plan:
        key, model = chat_settings(ROOT)
        if not key:
            st.error("Add OPENAI_API_KEY to the local .env file before creating a plan.")
        else:
            evidence = build_learning_plan_evidence(filtered, profile_skills, timeframe_weeks)
            try:
                with st.spinner("Building your evidence-based plan…"):
                    plan, used_fallback = generate_learning_plan(key, model, evidence)
                st.session_state.learning_plan = plan
                st.session_state.learning_plan_fallback = used_fallback
                st.session_state.learning_plan_context = (
                    f"{profile_fingerprint(profile_skills)}:{selection_fingerprint(filtered)}:{timeframe_weeks}"
                )
            except OpenAIError as error:
                failure = classify_openai_error(error)
                st.error(f"{failure.label}: {failure.message}")
    plan_context = f"{profile_fingerprint(profile_skills)}:{selection_fingerprint(filtered)}:{timeframe_weeks}"
    if st.session_state.get("learning_plan_context") == plan_context:
        plan = st.session_state.get("learning_plan")
        if plan:
            if st.session_state.get("learning_plan_fallback"):
                st.warning("The AI response could not be validated, so the app displayed a safe fallback plan.")
            st.markdown(f"##### {plan['title']}")
            st.caption(plan["limitations"])
            st.markdown("**Data-backed priorities**")
            priorities = pd.DataFrame(plan["data_backed_priorities"])
            if priorities.empty:
                st.success("No missing catalog skills were detected in the visible postings.")
            else:
                st.dataframe(priorities, hide_index=True, width="stretch")
            st.markdown("**Weekly practice steps**")
            for step in plan["weekly_steps"]:
                st.write(
                    f"Weeks {step['week_start']}–{step['week_end']}: **{step['focus']}** — "
                    f"{step['practice_task']}"
                )
            project = plan["portfolio_project"]
            st.markdown(f"**Portfolio project: {project['title']}**")
            st.write(project["description"])
            st.caption("General coaching guidance: " + " ".join(plan["general_guidance"]))

with st.expander("📄 Candidate Profile", expanded=False):
    st.markdown("### Candidate Profile")
    st.caption(
        "Upload a PDF, DOCX, or TXT resume up to 5 MB. Extraction happens locally and "
        "only reviewed fields are used. Uploaded data stays in this browser session."
    )
    privacy_left, privacy_right = st.columns([4, 1])
    with privacy_left:
        st.info(
            "Private by default: the original file is not saved to the repository or a database. "
            "Nothing is sent to OpenAI unless you explicitly request AI guidance below."
        )
    with privacy_right:
        if st.button(
            "Delete uploaded data",
            disabled="candidate_document" not in st.session_state,
            width="stretch",
        ):
            clear_candidate_session(st.session_state)
            st.rerun()

    upload_version = st.session_state.get("candidate_upload_version", 0)
    uploaded_resume = st.file_uploader(
        "Resume or application document",
        type=["pdf", "docx", "txt"],
        key=f"candidate_upload_{upload_version}",
        help="Password-protected PDFs and image-only scans are not supported.",
    )
    if uploaded_resume is not None:
        upload_bytes = uploaded_resume.getvalue()
        upload_fingerprint = hashlib.sha256(upload_bytes).hexdigest()
        current_document = st.session_state.get("candidate_document", {})
        if current_document.get("fingerprint") != upload_fingerprint:
            try:
                document = extract_candidate_document(uploaded_resume.name, upload_bytes)
                document["fingerprint"] = upload_fingerprint
                st.session_state.candidate_document = document
                st.session_state.candidate_skills = document["detected_skills"]
                st.session_state.candidate_summary = ""
                st.session_state.candidate_education = ""
                st.session_state.candidate_experience = document["text"][:4000]
                st.session_state.candidate_projects = ""
                st.session_state.candidate_portfolio_urls = ""
                st.session_state.candidate_preferred_roles = ""
                st.session_state.candidate_preferred_locations = ""
                st.session_state.candidate_work_authorization = "Prefer not to say"
                st.session_state.pop("candidate_guidance", None)
            except CandidateUploadError as error:
                st.error(str(error))

    document = st.session_state.get("candidate_document")
    if document:
        st.success(
            f"Extracted {document['character_count']:,} characters locally from "
            f"{document['filename']}. Review and correct everything below."
        )
        st.multiselect(
            "Verified skills",
            options=catalog_skills,
            key="candidate_skills",
            help="Only selected catalog skills are used for deterministic matching.",
        )
        review_left, review_right = st.columns(2)
        with review_left:
            st.text_area("Professional summary", key="candidate_summary", height=120)
            st.text_area("Education", key="candidate_education", height=120)
            st.text_area(
                "Experience and reviewed document text",
                key="candidate_experience",
                height=220,
                help="Correct extraction mistakes and remove anything you do not want used.",
            )
            st.text_area("Projects", key="candidate_projects", height=140)
        with review_right:
            st.text_area("Portfolio or GitHub URLs", key="candidate_portfolio_urls", height=100)
            st.text_area("Preferred roles", key="candidate_preferred_roles", height=100)
            st.text_area("Preferred US locations", key="candidate_preferred_locations", height=100)
            st.selectbox(
                "Work authorization",
                ["Prefer not to say", "Authorized to work in the US", "Requires sponsorship", "Other"],
                key="candidate_work_authorization",
            )

        candidate_profile = build_candidate_profile(
            skills=st.session_state.candidate_skills,
            summary=st.session_state.candidate_summary,
            education=st.session_state.candidate_education,
            experience=st.session_state.candidate_experience,
            projects=st.session_state.candidate_projects,
            portfolio_urls=st.session_state.candidate_portfolio_urls,
            preferred_roles=st.session_state.candidate_preferred_roles,
            preferred_locations=st.session_state.candidate_preferred_locations,
            work_authorization=st.session_state.candidate_work_authorization,
        )

        st.markdown("#### Resume-to-internship matches")
        if not candidate_profile["skills"]:
            st.warning("Confirm at least one skill above to calculate matches.")
        else:
            candidate_matches = rank_candidate_matches(candidate_profile, filtered)
            match_display = candidate_matches[
                ["company", "job_title", "match_percentage", "matched_skills", "missing_skills"]
            ].head(10).copy()
            match_display.columns = ["Company", "Role", "Skill overlap", "Matched skills", "Missing skills"]
            st.dataframe(
                match_display,
                hide_index=True,
                width="stretch",
                column_config={
                    "Skill overlap": st.column_config.NumberColumn(format="%.0f%%"),
                },
            )
            st.caption("Catalog-skill overlap is a navigation aid—not an eligibility or hiring prediction.")

        st.markdown("#### Tailored application guidance")
        if filtered.empty:
            st.info("No internship is available under the current dashboard filters.")
        else:
            target_rows = {str(row["posting_id"]): row for _, row in filtered.iterrows()}
            if st.session_state.get("candidate_target_id") not in target_rows:
                st.session_state.candidate_target_id = next(iter(target_rows))
            target_id = st.selectbox(
                "Target internship",
                options=list(target_rows),
                format_func=lambda identifier: (
                    f"{target_rows[identifier]['company']} — {target_rows[identifier]['job_title']}"
                ),
                key="candidate_target_id",
            )
            guidance_type = st.radio(
                "Guidance type",
                options=["resume", "cover_letter"],
                format_func=lambda value: "Resume suggestions" if value == "resume" else "Cover-letter draft",
                horizontal=True,
                key="candidate_guidance_type",
            )
            st.checkbox(
                "I understand that the reviewed fields above and selected job data will be sent to OpenAI for this request.",
                key="candidate_ai_consent",
            )
            if st.button(
                "Generate application guidance",
                disabled=not st.session_state.candidate_ai_consent,
                type="primary",
            ):
                key, model = chat_settings(ROOT)
                if not key:
                    st.error("Add OPENAI_API_KEY to the local .env file before requesting AI guidance.")
                else:
                    try:
                        with st.spinner("Creating guidance from your reviewed profile…"):
                            st.session_state.candidate_guidance = generate_application_guidance(
                                key,
                                model,
                                candidate_profile,
                                target_rows[target_id],
                                guidance_type,
                            )
                    except OpenAIError as error:
                        failure = classify_openai_error(error)
                        st.error(f"{failure.label}: {failure.message}")
            if st.session_state.get("candidate_guidance"):
                st.markdown("##### Generated guidance")
                st.write(st.session_state.candidate_guidance)

with st.expander("📝 Quick Job Description Analyzer", expanded=False):
    st.markdown("### Quick Job Description Analyzer")
    st.caption(
        "Paste a job description to detect catalog skills locally. The text is not saved "
        "and is not sent to OpenAI."
    )
    custom_description = st.text_area(
        "Job description",
        key="custom_job_description",
        height=180,
        max_chars=10_000,
        placeholder="Paste a job description here…",
    )
    if st.button("Analyze description", disabled=not custom_description.strip()):
        detected_pairs = extract_skills(custom_description)
        st.session_state.custom_analysis = {
            "description_fingerprint": hashlib.sha256(custom_description.encode()).hexdigest(),
            "skills": [skill for skill, _ in detected_pairs],
            "categories": sorted({category for _, category in detected_pairs}),
        }
    custom_analysis = st.session_state.get("custom_analysis")
    current_description_id = hashlib.sha256(custom_description.encode()).hexdigest()
    if custom_analysis and custom_analysis["description_fingerprint"] == current_description_id:
        if custom_analysis["skills"]:
            st.write("**Detected skills:** " + ", ".join(custom_analysis["skills"]))
            st.write("**Skill categories:** " + ", ".join(custom_analysis["categories"]))
            if profile_skills:
                custom_gap = calculate_skill_gap(custom_analysis["skills"], profile_skills)
                st.metric(
                    "Your catalog-skill overlap",
                    f"{custom_gap['match_percentage']:.0f}%" if custom_gap["match_percentage"] is not None else "Unavailable",
                )
                st.write("**Matched:** " + (", ".join(custom_gap["matched_skills"]) or "None"))
                st.write("**Missing:** " + (", ".join(custom_gap["missing_skills"]) or "None"))
        else:
            st.info("No skills from the current project catalog were detected.")

skill_counts = skill_frequency(filtered)
with st.expander(f"💬 {BOT_NAME}", expanded=True):
    st.markdown(f"### {BOT_NAME}")
    st.caption("Ask about the internships shown by your current filters. Changing filters starts a new chat.")
    context_id = f"{selection_fingerprint(filtered)}:{profile_fingerprint(profile_skills)}"
    if st.session_state.get("chat_context_id") != context_id:
        st.session_state.chat_context_id = context_id
        st.session_state.chat_messages = []
    key, model = chat_settings(ROOT)
    configuration_id = f"{bool(key)}:{model}"
    if st.session_state.get("agent_configuration_id") != configuration_id:
        st.session_state.agent_configuration_id = configuration_id
        st.session_state.agent_health = configured_health(key, model).to_dict()

    health = st.session_state.agent_health
    health_left, health_right = st.columns([4, 1])
    with health_left:
        status_text = f"**{health['label']}** — {health['message']}"
        if health["status"] == "ready":
            st.success(status_text)
        elif health["status"] == "not_checked":
            st.warning(status_text)
        else:
            st.error(status_text)
        st.caption(f"API key: {'configured securely (hidden)' if key else 'not configured'}")
        st.caption(f"Configured model: `{model}`")
    with health_right:
        if st.button("Check connection", disabled=not key, width="stretch"):
            with st.spinner("Checking API access…"):
                st.session_state.agent_health = check_agent_health(key, model).to_dict()
            st.rerun()

    if not key:
        st.info("AI replies are not enabled yet. Add OPENAI_API_KEY to the project's local .env file. "
                "Do not paste your key into chat or commit it to GitHub.")
    if profile_skills:
        st.caption(
            f"Personalization active with {len(profile_skills)} selected skill"
            f"{'s' if len(profile_skills) != 1 else ''}. Match values come from the app's calculations."
        )
    else:
        st.caption("Select skills under My Skills to receive personalized match explanations.")
    st.caption('Try: “Which internships mention Python?” or “Why do these roles match my skills?”')
    st.caption("When you send a message, your question, recent chat history, and selected job data "
               "are sent to OpenAI. API usage may incur charges; avoid entering personal information.")
    history_left, history_right = st.columns([4, 1])
    with history_left:
        st.markdown("#### Chat history")
        if not st.session_state.chat_messages:
            st.caption("Your messages will appear here after you start a conversation.")
    with history_right:
        if st.button(
            "Clear chat",
            key="clear_chat",
            disabled=not st.session_state.chat_messages,
            width="stretch",
        ):
            st.session_state.chat_messages = []
            st.rerun()
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("trace"):
                with st.expander("How this answer was produced"):
                    for item in message["trace"]:
                        icon = "✓" if item["status"] == "completed" else "⚠"
                        st.write(f"{icon} `{item['tool']}` — {item['summary']}")
    typed_question = st.chat_input("Ask Internship Assistant…", disabled=not key, max_chars=2000)
    pending_question = st.session_state.pop("pending_coaching_question", None)
    question = pending_question or typed_question
    if question and question.strip():
        context = dataset_context(filtered, question)
        personalization = build_personalization_context(filtered, profile_skills)
        with st.chat_message("user"):
            st.write(question)
        try:
            with st.spinner("Internship Assistant is checking the dataset…"):
                result = answer_question_with_trace(
                    key,
                    model,
                    context,
                    st.session_state.chat_messages,
                    question,
                    personalization,
                    filtered,
                    profile_skills,
                )
            st.session_state.chat_messages.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": result.text, "trace": result.trace},
            ])
            st.session_state.last_agent_diagnostics = result.diagnostics
            st.session_state.chat_messages = st.session_state.chat_messages[-8:]
            with st.chat_message("assistant"):
                st.write(result.text)
                if result.trace:
                    with st.expander("How this answer was produced"):
                        for item in result.trace:
                            icon = "✓" if item["status"] == "completed" else "⚠"
                            st.write(f"{icon} `{item['tool']}` — {item['summary']}")
        except OpenAIError as error:
            failure = classify_openai_error(error)
            st.session_state.agent_health = failure.to_dict()
            st.error(f"{failure.label}: {failure.message} Your dashboard still works.")

    with st.expander("Developer diagnostics", expanded=False):
        diagnostics = st.session_state.get("last_agent_diagnostics")
        if not diagnostics:
            st.caption("Diagnostics appear after an assistant response.")
        else:
            diagnostic_columns = st.columns(4)
            diagnostic_columns[0].metric("Status", diagnostics["status"])
            diagnostic_columns[1].metric("Latency", f"{diagnostics['latency_ms']} ms")
            diagnostic_columns[2].metric("Tool calls", diagnostics["tool_call_count"])
            diagnostic_columns[3].metric("Citations", diagnostics["citation_count"])
            st.caption(
                f"Tokens — input: {diagnostics['input_tokens']}; output: {diagnostics['output_tokens']}. "
                "No prompts, API keys, resume text, or private skill selections are logged."
            )

advanced_count = int(filtered["experience_level"].eq("Advanced").sum())
metrics = st.columns(4)
metrics[0].metric("Matching internships", len(filtered), f"of {len(data)} collected")
metrics[1].metric("Companies", filtered["company"].nunique())
metrics[2].metric("Skills detected", len(skill_counts))
metrics[3].metric("Beginner-friendly", len(filtered) - advanced_count)

st.markdown("### Market overview")
chart_left, chart_right = st.columns((1.45, 1))
with chart_left:
    top_skills = skill_counts.head(10).sort_values("postings")
    if top_skills.empty:
        st.info("No skills match the current filters.")
    else:
        figure = px.bar(top_skills, x="postings", y="skill", orientation="h", color="postings",
                        color_continuous_scale=["#bfdbfe", "#1d4ed8"],
                        labels={"postings": "Postings", "skill": ""})
        figure.update_layout(title="Most requested skills", coloraxis_showscale=False,
                             plot_bgcolor="white", paper_bgcolor="white", height=420,
                             margin=dict(l=10, r=15, t=55, b=20))
        st.plotly_chart(figure, width="stretch")
with chart_right:
    counts = filtered["experience_level"].value_counts().rename_axis("level").reset_index(name="postings")
    if counts.empty:
        st.info("No difficulty data matches the current filters.")
    else:
        figure = px.pie(counts, values="postings", names="level", hole=.62, color="level",
                        color_discrete_map={"Beginner-friendly": "#22c55e", "Advanced": "#f97316"})
        figure.update_traces(textposition="outside", textinfo="label+value")
        figure.update_layout(title="Posting difficulty", showlegend=False, height=420,
                             margin=dict(l=20, r=20, t=55, b=20), paper_bgcolor="white")
        st.plotly_chart(figure, width="stretch")

st.markdown("### Internship opportunities")
st.caption("Choose a row to inspect the full description and application link below.")
display_columns = ["company", "job_title", "location", "experience_level", "skill_count"]
display_names = ["Company", "Role", "Location", "Difficulty", "Skills"]
if profile_skills:
    display_columns.append("match_percentage")
    display_names.append("Skill overlap")
display_columns.append("source_url")
display_names.append("Apply")
display = filtered[display_columns].copy()
display.columns = display_names
selection = st.dataframe(display, width="stretch", hide_index=True, on_select="rerun",
    selection_mode="single-row", column_config={
        "Apply": st.column_config.LinkColumn("Apply", display_text="Open posting ↗"),
        "Skills": st.column_config.NumberColumn("Skills", format="%d"),
        "Skill overlap": st.column_config.NumberColumn("Skill overlap", format="%.0f%%")})

if selection.selection.rows:
    posting = filtered.iloc[selection.selection.rows[0]]
    safe_company = html.escape(str(posting["company"]))
    safe_title = html.escape(str(posting["job_title"]))
    safe_location = html.escape(str(posting["location"]))
    safe_level = html.escape(str(posting["experience_level"]))
    st.markdown("### Selected opportunity")
    st.markdown(f"<div class='job-card'><div class='eyebrow'>{safe_company}</div>"
                f"<h3>{safe_title}</h3><p>📍 {safe_location} &nbsp; · &nbsp; "
                f"{safe_level}</p></div>", unsafe_allow_html=True)
    st.markdown(" ".join(f"<span class='pill'>{html.escape(skill)}</span>"
                         for skill in posting["skills_list"]),
                unsafe_allow_html=True)
    if profile_skills:
        if pd.isna(posting["match_percentage"]):
            st.info("Skill overlap: Not enough detected skill data")
        else:
            st.markdown(f"#### Skill overlap: {posting['match_percentage']:.0f}%")
            matched = posting["matched_skills"]
            missing = posting["missing_skills"]
            st.write("**You selected:** " + (", ".join(matched) if matched else "None of the detected skills"))
            st.write("**Not selected:** " + (", ".join(missing) if missing else "None"))
            st.caption("This is catalog skill overlap, not a qualification or interview prediction.")
    st.write(posting["description"])
    action_left, action_right = st.columns(2)
    with action_left:
        st.link_button("Apply on company site ↗", posting["source_url"], type="primary", width="stretch")
    with action_right:
        if st.button("Ask Internship Assistant", type="secondary", width="stretch"):
            st.session_state.pending_coaching_question = build_coaching_question(posting)
            st.rerun()
else:
    st.info("Select an internship row to view its skills and full description.")

with st.expander("About this data"):
    st.write("This dashboard uses the latest processed US dataset. Public career postings are "
             "limited to five per company. Difficulty follows the analysis pipeline's advanced-skill rule.")
