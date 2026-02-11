import streamlit as st
from dotenv import load_dotenv
import os
import sys
import logging

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
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

# Assuming you have these modules implemented
from agents.protocol_generator import ProtocolGenerator
from mcp_interface.protocol_server import ProtocolServer
from agents.pi_agent import PIAgent
from agents.site_physician_agent import SitePhysicianAgent
from agents.health_authority_agent import HealthAuthorityAgent
from utils.risk_assessor import RiskAssessor
from utils.scoring_engine import ScoringEngine
from utils.document_processor import DocumentProcessor

load_dotenv() # Load environment variables

st.set_page_config(layout="wide", page_title="Clinical Protocol AI Review")

st.title("Clinical Protocol AI Review System")

# --- Protocol Generation Section ---
st.header("1. Protocol Generation")
with st.expander("Generate a New Protocol Draft"):
    st.write("Input parameters to generate a new clinical protocol draft.")
    study_title = st.text_input("Study Title", "A Phase III Study of Novel Drug X for Disease Y")
    indication = st.text_area("Indication", "Advanced metastatic solid tumors resistant to standard therapies.")
    objectives = st.text_area("Objectives", "Primary: Overall Response Rate. Secondary: Progression-Free Survival, Safety.")
    # Add more parameters as needed based on your templates

    if st.button("Generate Protocol Draft"):
        with st.spinner("Generating protocol draft..."):
            logger.info("Starting protocol generation for: %s", study_title)
            protocol_generator = ProtocolGenerator(llm_model="gpt-4o") # or your preferred model
            generated_protocol_content = protocol_generator.generate_protocol_draft(
                study_title=study_title,
                indication=indication,
                objectives=objectives,
                template_path="templates/ich_templates/ich_template_v1.md" # Placeholder
            )
            st.session_state["current_protocol"] = generated_protocol_content
            logger.info("Protocol draft generated successfully")
            st.success("Protocol draft generated!")
            st.subheader("Generated Protocol Draft:")
            st.text_area("Protocol Content", generated_protocol_content, height=400)


# --- Protocol Upload Section ---
st.header("2. Upload Existing Protocol")
uploaded_file = st.file_uploader("Upload a clinical protocol (PDF, TXT, MD)", type=["pdf", "txt", "md"])
if uploaded_file is not None:
    with st.spinner("Processing uploaded protocol..."):
        logger.info("Processing uploaded file: %s (type: %s)", uploaded_file.name, uploaded_file.type)
        doc_processor = DocumentProcessor()
        if uploaded_file.type == "application/pdf":
            st.session_state["current_protocol"] = doc_processor.extract_text_from_pdf(uploaded_file)
        else: # Assuming txt or md
            st.session_state["current_protocol"] = uploaded_file.read().decode("utf-8")
        logger.info("Protocol uploaded and processed successfully")
        st.success("Protocol uploaded and processed!")
        st.subheader("Uploaded Protocol Content:")
        st.text_area("Protocol Content", st.session_state["current_protocol"], height=400)


# --- Protocol Review Section ---
st.header("3. Multi-Agent Protocol Review")
if "current_protocol" in st.session_state and st.session_state["current_protocol"]:
    if st.button("Start Multi-Agent Review"):
        with st.spinner("Agents are reviewing the protocol..."):
            logger.info("Starting multi-agent protocol review")

            # Initialize MCP Server (to simulate structured access for agents)
            protocol_server = ProtocolServer(st.session_state["current_protocol"])

            # Initialize Agents
            pi_agent = PIAgent(llm_model="gpt-4o")
            site_physician_agent = SitePhysicianAgent(llm_model="gpt-4o")
            health_authority_agent = HealthAuthorityAgent(llm_model="gpt-4o")

            # Perform Reviews
            st.subheader("Agent Review Feedback:")

            logger.info("Running PI Agent review")
            pi_feedback = pi_agent.review_protocol(protocol_server)
            logger.info("PI Agent review complete")
            st.write(f"**Principal Investigator Agent Feedback:**\n{pi_feedback}")

            logger.info("Running Site Physician Agent review")
            site_physician_feedback = site_physician_agent.review_protocol(protocol_server)
            logger.info("Site Physician Agent review complete")
            st.write(f"**Site Physician Agent Feedback:**\n{site_physician_feedback}")

            logger.info("Running Health Authority Agent review")
            health_authority_feedback = health_authority_agent.review_protocol(protocol_server)
            logger.info("Health Authority Agent review complete")
            st.write(f"**Health Authority Agent Feedback:**\n{health_authority_feedback}")

            # Consolidate feedback (this can be done by a meta-agent or a utility)
            all_feedback = {
                "pi": pi_feedback,
                "site_physician": site_physician_feedback,
                "health_authority": health_authority_feedback
            }
            st.session_state["all_feedback"] = all_feedback

            # Risk Assessment and Scoring
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

            # Store results in session state for report generation
            st.session_state["amendment_risks"] = amendment_risks
            st.session_state["protocol_score"] = protocol_score

else:
    st.info("Please generate or upload a protocol to proceed with the review.")

# --- Markdown Report Generation Section ---
st.header("4. Generate Markdown Report")
if (
    "all_feedback" in st.session_state
    and "amendment_risks" in st.session_state
    and "protocol_score" in st.session_state
):
    report_filename = st.text_input(
        "Report filename (without extension)",
        placeholder="e.g. protocol_review_report",
    )

    if st.button("Generate Report"):
        if not report_filename.strip():
            st.warning("Please enter a filename for the report.")
        else:
            from datetime import datetime

            base_name = report_filename.strip().replace(" ", "_")
            filename = base_name + ".md"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            feedback = st.session_state["all_feedback"]
            risks = st.session_state["amendment_risks"]
            score = st.session_state["protocol_score"]

            # --- Create output directory for individual section files ---
            reports_dir = os.path.join(os.getcwd(), "reports", base_name)
            os.makedirs(reports_dir, exist_ok=True)

            # --- Build individual section markdowns ---
            section_header = f"*From full report: {filename}*\n\n**Generated:** {now}\n\n---\n\n"

            # 1. PI Agent
            pi_content = (
                f"# Principal Investigator Agent Review\n\n"
                f"{section_header}"
                f"{feedback['pi']}\n"
            )
            pi_path = os.path.join(reports_dir, f"{base_name}_pi_agent.md")
            with open(pi_path, "w") as f:
                f.write(pi_content)

            # 2. Site Physician Agent
            site_content = (
                f"# Site Physician Agent Review\n\n"
                f"{section_header}"
                f"{feedback['site_physician']}\n"
            )
            site_path = os.path.join(reports_dir, f"{base_name}_site_physician_agent.md")
            with open(site_path, "w") as f:
                f.write(site_content)

            # 3. Health Authority Agent
            ha_content = (
                f"# Health Authority Agent Review\n\n"
                f"{section_header}"
                f"{feedback['health_authority']}\n"
            )
            ha_path = os.path.join(reports_dir, f"{base_name}_health_authority_agent.md")
            with open(ha_path, "w") as f:
                f.write(ha_content)

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
            risk_content = "\n".join(risk_lines)
            risk_path = os.path.join(reports_dir, f"{base_name}_risk_assessment.md")
            with open(risk_path, "w") as f:
                f.write(risk_content)

            # 5. Score
            score_content = (
                f"# Overall Protocol Score\n\n"
                f"{section_header}"
                f"**Score: {score}/100**\n"
            )
            score_path = os.path.join(reports_dir, f"{base_name}_score.md")
            with open(score_path, "w") as f:
                f.write(score_content)

            logger.info("Individual section reports saved to %s", reports_dir)

            # --- Build full combined report ---
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

            report_content = "\n".join(lines)

            # Save full report to the same directory
            full_report_path = os.path.join(reports_dir, filename)
            with open(full_report_path, "w") as f:
                f.write(report_content)
            logger.info("Full markdown report saved to %s", full_report_path)

            st.success(f"Reports saved to `{reports_dir}/`")
            st.caption(
                f"**Files generated:**\n"
                f"- `{filename}` (full report)\n"
                f"- `{base_name}_pi_agent.md`\n"
                f"- `{base_name}_site_physician_agent.md`\n"
                f"- `{base_name}_health_authority_agent.md`\n"
                f"- `{base_name}_risk_assessment.md`\n"
                f"- `{base_name}_score.md`"
            )

            # Offer full report as a download
            st.download_button(
                label="Download Full Report",
                data=report_content,
                file_name=filename,
                mime="text/markdown",
            )
else:
    st.info("Run the multi-agent review first to generate a report.")

# --- Future Enhancements (Mentions) ---
st.sidebar.header("About This System")
st.sidebar.info(
    "This is a prototype for an AI-powered clinical protocol generation and multi-agent review system. "
    "It leverages LangChain for agentic behavior and the Model Context Protocol (MCP) for structured "
    "protocol interaction."
)