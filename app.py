"""Interactive Streamlit dashboard for the Internship Skill Analyzer."""

import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


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

skill_counts = skill_frequency(filtered)
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
        st.plotly_chart(figure, use_container_width=True)
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
        st.plotly_chart(figure, use_container_width=True)

st.markdown("### Internship opportunities")
st.caption("Choose a row to inspect the full description and application link below.")
display = filtered[["company", "job_title", "location", "experience_level", "skill_count", "source_url"]].copy()
display.columns = ["Company", "Role", "Location", "Difficulty", "Skills", "Apply"]
selection = st.dataframe(display, use_container_width=True, hide_index=True, on_select="rerun",
    selection_mode="single-row", column_config={
        "Apply": st.column_config.LinkColumn("Apply", display_text="Open posting ↗"),
        "Skills": st.column_config.NumberColumn("Skills", format="%d")})

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
    st.write(posting["description"])
    st.link_button("Apply on company site ↗", posting["source_url"], type="primary")
else:
    st.info("Select an internship row to view its skills and full description.")

with st.expander("About this data"):
    st.write("This dashboard uses the latest processed US dataset. Public career postings are "
             "limited to five per company. Difficulty follows the analysis pipeline's advanced-skill rule.")
