import streamlit as st
import os
import sys
import logging
import tempfile
import zipfile
import io

# Configure logging (console only — no persistent filesystem on HF Spaces)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Global exception handler to log unhandled exceptions
def _handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = _handle_unhandled_exception

from agents.protocol_generator import ProtocolGenerator
from mcp_interface.protocol_server import ProtocolServer
from agents.pi_agent import PIAgent
from agents.site_physician_agent import SitePhysicianAgent
from agents.health_authority_agent import HealthAuthorityAgent
from utils.risk_assessor import RiskAssessor
from utils.scoring_engine import ScoringEngine
from utils.document_processor import DocumentProcessor

st.set_page_config(layout="wide", page_title="Clinical Protocol AI Review")

# --- Sidebar ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

st.sidebar.header("About This System")
st.sidebar.info(
    "This is a prototype for an AI-powered clinical protocol generation and multi-agent review system. "
    "It leverages LangChain for agentic behavior and the Model Context Protocol (MCP) for structured "
    "protocol interaction."
)

# --- Gate all functionality behind API key ---
if not api_key:
    st.title("Clinical Protocol AI Review System")
    st.warning("Please enter your OpenAI API key in the sidebar to get started.")
    st.stop()

st.title("Clinical Protocol AI Review System")

# --- Protocol Generation Section ---
st.header("1. Protocol Generation")
with st.expander("Generate a New Protocol Draft"):
    st.write("Input parameters to generate a new clinical protocol draft.")
    study_title = st.text_input("Study Title", "A Phase III Study of Novel Drug X for Disease Y")
    indication = st.text_area("Indication", "Advanced metastatic solid tumors resistant to standard therapies.")
    objectives = st.text_area("Objectives", "Primary: Overall Response Rate. Secondary: Progression-Free Survival, Safety.")

    if st.button("Generate Protocol Draft"):
        with st.spinner("Generating protocol draft..."):
            logger.info("Starting protocol generation for: %s", study_title)
            protocol_generator = ProtocolGenerator(llm_model="gpt-4o")
            generated_protocol_content = protocol_generator.generate_protocol_draft(
                study_title=study_title,
                indication=indication,
                objectives=objectives,
                template_path="templates/ich_templates/ich_template_v1.md"
            )
            st.session_state["current_protocol"] = generated_protocol_content
            logger.info("Protocol draft generated successfully")
            st.success("Protocol draft generated!")


# --- Protocol Upload Section ---
st.header("2. Upload Existing Protocol")
uploaded_file = st.file_uploader("Upload a clinical protocol (PDF, TXT, MD)", type=["pdf", "txt", "md"])
if uploaded_file is not None:
    with st.spinner("Processing uploaded protocol..."):
        logger.info("Processing uploaded file: %s (type: %s)", uploaded_file.name, uploaded_file.type)
        doc_processor = DocumentProcessor()
        if uploaded_file.type == "application/pdf":
            st.session_state["current_protocol"] = doc_processor.extract_text_from_pdf(uploaded_file)
        else:
            st.session_state["current_protocol"] = uploaded_file.read().decode("utf-8")
        logger.info("Protocol uploaded and processed successfully")
        st.success("Protocol uploaded and processed!")

# --- Example Protocol ---
EXAMPLE_PROTOCOL_PATH = "example-protocols/Vemurafenib in Multiple Nonmelanoma Cancers with BRAF V600 Mutations.pdf"

if os.path.exists(EXAMPLE_PROTOCOL_PATH):
    if st.button("Use Example Protocol"):
        with st.spinner("Loading example protocol..."):
            logger.info("Loading example protocol: %s", EXAMPLE_PROTOCOL_PATH)
            doc_processor = DocumentProcessor()
            st.session_state["current_protocol"] = doc_processor.extract_text_from_pdf(EXAMPLE_PROTOCOL_PATH)
            logger.info("Example protocol loaded successfully")
            st.success("Example protocol loaded!")
            st.rerun()

if "current_protocol" in st.session_state and st.session_state["current_protocol"]:
    st.subheader("Current Protocol Content:")
    st.text_area("Protocol Content (loaded)", st.session_state["current_protocol"], height=400, key="loaded_protocol_display")


# --- Protocol Review Section ---
st.header("3. Multi-Agent Protocol Review")
if "current_protocol" in st.session_state and st.session_state["current_protocol"]:
    if st.button("Start Multi-Agent Review"):
        logger.info("Starting multi-agent protocol review")

        protocol_server = ProtocolServer(st.session_state["current_protocol"])

        pi_agent = PIAgent(llm_model="gpt-4o")
        site_physician_agent = SitePhysicianAgent(llm_model="gpt-4o")
        health_authority_agent = HealthAuthorityAgent(llm_model="gpt-4o")

        st.subheader("Agent Review Feedback:")

        with st.status("Principal Investigator Agent reviewing...", expanded=True) as status:
            logger.info("Running PI Agent review")
            pi_feedback = pi_agent.review_protocol(protocol_server)
            logger.info("PI Agent review complete")
            st.write(pi_feedback)
            status.update(label="Principal Investigator Agent — Complete", state="complete")

        with st.status("Site Physician Agent reviewing...", expanded=True) as status:
            logger.info("Running Site Physician Agent review")
            site_physician_feedback = site_physician_agent.review_protocol(protocol_server)
            logger.info("Site Physician Agent review complete")
            st.write(site_physician_feedback)
            status.update(label="Site Physician Agent — Complete", state="complete")

        with st.status("Health Authority Agent reviewing...", expanded=True) as status:
            logger.info("Running Health Authority Agent review")
            health_authority_feedback = health_authority_agent.review_protocol(protocol_server)
            logger.info("Health Authority Agent review complete")
            st.write(health_authority_feedback)
            status.update(label="Health Authority Agent — Complete", state="complete")

        all_feedback = {
            "pi": pi_feedback,
            "site_physician": site_physician_feedback,
            "health_authority": health_authority_feedback
        }
        st.session_state["all_feedback"] = all_feedback

        with st.status("Running risk assessment and scoring...", expanded=True) as status:
            logger.info("Running risk assessment")
            risk_assessor = RiskAssessor()
            amendment_risks = risk_assessor.assess_risks(all_feedback)
            logger.info("Risk assessment complete, found %d risks", len(amendment_risks))
            st.subheader("Amendment Risk Assessment:")
            for risk in amendment_risks:
                st.write(f"- **Risk:** {risk['description']} (Severity: {risk['severity']})")
                st.write(f"  **Rationale:** {risk['rationale']}")
                st.write(f"  **Recommendation:** {risk['recommendation']}")

            scoring_engine = ScoringEngine()
            protocol_score = scoring_engine.score_protocol(amendment_risks)
            logger.info("Protocol scored: %d/100", protocol_score)
            st.subheader("Overall Protocol Score:")
            st.success(f"The protocol scored: {protocol_score}/100")
            status.update(label="Risk Assessment & Scoring — Complete", state="complete")

        st.session_state["amendment_risks"] = amendment_risks
        st.session_state["protocol_score"] = protocol_score

else:
    st.info("Please generate or upload a protocol to proceed with the review.")

# --- Report Download Section ---
st.header("4. Download Report")
if (
    "all_feedback" in st.session_state
    and "amendment_risks" in st.session_state
    and "protocol_score" in st.session_state
):
    if st.button("Download Report"):
        from datetime import datetime
        from utils.pdf_converter import markdown_to_pdf

        base_name = "report"
        filename = base_name + ".md"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        feedback = st.session_state["all_feedback"]
        risks = st.session_state["amendment_risks"]
        score = st.session_state["protocol_score"]

        section_header = f"*From full report: {filename}*\n\n**Generated:** {now}\n\n---\n\n"

        # Build section contents as a dict of filename -> content
        sections = {}

        # 1. PI Agent
        sections[f"{base_name}_pi_agent.md"] = (
            f"# Principal Investigator Agent Review\n\n"
            f"{section_header}"
            f"{feedback['pi']}\n"
        )

        # 2. Site Physician Agent
        sections[f"{base_name}_site_physician_agent.md"] = (
            f"# Site Physician Agent Review\n\n"
            f"{section_header}"
            f"{feedback['site_physician']}\n"
        )

        # 3. Health Authority Agent
        sections[f"{base_name}_health_authority_agent.md"] = (
            f"# Health Authority Agent Review\n\n"
            f"{section_header}"
            f"{feedback['health_authority']}\n"
        )

        # 4. Risk Assessment
        risk_lines = [
            f"# Amendment Risk Assessment\n",
            f"{section_header}",
        ]
        for i, risk in enumerate(risks, 1):
            risk_lines.append(f"## Risk {i}: {risk['description']}\n")
            risk_lines.append(f"- **Severity:** {risk['severity']}")
            risk_lines.append(f"- **Rationale:** {risk['rationale']}")
            risk_lines.append(f"- **Recommendation:** {risk['recommendation']}\n")
        sections[f"{base_name}_risk_assessment.md"] = "\n".join(risk_lines)

        # 5. Score
        sections[f"{base_name}_score.md"] = (
            f"# Overall Protocol Score\n\n"
            f"{section_header}"
            f"**Score: {score}/100**\n"
        )

        # 6. Full combined report
        lines = [
            f"# Clinical Protocol Review Report",
            f"",
            f"**Generated:** {now}",
            f"",
            f"---",
            f"",
            f"## Agent Review Feedback",
            f"",
            f"### Principal Investigator Agent",
            f"",
            f"{feedback['pi']}",
            f"",
            f"### Site Physician Agent",
            f"",
            f"{feedback['site_physician']}",
            f"",
            f"### Health Authority Agent",
            f"",
            f"{feedback['health_authority']}",
            f"",
            f"---",
            f"",
            f"## Amendment Risk Assessment",
            f"",
        ]

        for i, risk in enumerate(risks, 1):
            lines.append(f"### Risk {i}: {risk['description']}")
            lines.append(f"")
            lines.append(f"- **Severity:** {risk['severity']}")
            lines.append(f"- **Rationale:** {risk['rationale']}")
            lines.append(f"- **Recommendation:** {risk['recommendation']}")
            lines.append(f"")

        lines.extend([
            f"---",
            f"",
            f"## Overall Protocol Score",
            f"",
            f"**Score: {score}/100**",
            f"",
        ])

        sections[filename] = "\n".join(lines)

        # Convert each markdown section to PDF
        pdfs = {}
        with st.spinner("Generating PDFs..."):
            for md_fname, md_content in sections.items():
                pdf_fname = md_fname.replace(".md", ".pdf")
                pdfs[pdf_fname] = markdown_to_pdf(md_content)

        # Create ZIP in memory with subfolders
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in sections.items():
                zf.writestr(f"report-markdowns/{fname}", content)
            for fname, pdf_bytes in pdfs.items():
                zf.writestr(f"report-pdfs/{fname}", pdf_bytes)
        zip_buffer.seek(0)

        logger.info("Report ZIP generated with %d markdown + %d PDF files", len(sections), len(pdfs))

        st.success("Report generated!")
        st.caption(
            f"**Files included in ZIP:**\n"
            f"- `report-markdowns/` — {len(sections)} markdown files\n"
            f"- `report-pdfs/` — {len(pdfs)} PDF files"
        )

        st.download_button(
            label="Download Report (ZIP)",
            data=zip_buffer,
            file_name="report.zip",
            mime="application/zip",
        )
else:
    st.info("Run the multi-agent review first to generate a report.")
