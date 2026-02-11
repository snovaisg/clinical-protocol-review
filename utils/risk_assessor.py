from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json
import logging

logger = logging.getLogger(__name__)

class RiskAssessor:
    def __init__(self, llm_model="gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.3, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_template = PromptTemplate(
            template="""
            Analyze the following agent feedback on a clinical trial protocol.
            Identify potential amendment triggers, categorize their severity (Low, Medium, High),
            provide a concise rationale, and suggest a specific recommendation to address the issue.
            Structure your output as a JSON array of objects.

            Agent Feedback:
            {agent_feedback_json}

            Output JSON format example:
            [
                {{
                    "description": "Risk description",
                    "severity": "Low|Medium|High",
                    "rationale": "Reason for the risk",
                    "recommendation": "Suggested change or action"
                }},
                ...
            ]
            """,
            input_variables=["agent_feedback_json"]
        )
        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def assess_risks(self, all_feedback: dict) -> list[dict]:
        """
        Assesses amendment risks based on consolidated agent feedback.
        """
        agent_feedback_str = json.dumps(all_feedback, indent=2)
        try:
            response = self.chain.invoke({"agent_feedback_json": agent_feedback_str})
            # Strip markdown code fences (```json ... ```) that LLMs often wrap around JSON
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]  # remove opening ```json line
                cleaned = cleaned.rsplit("```", 1)[0]  # remove closing ```
                cleaned = cleaned.strip()
            risks = json.loads(cleaned)
            return risks
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON from LLM response: %s", e)
            logger.error("LLM Response was: %s", response)
            return [{"description": "Error in risk assessment format.", "severity": "High", "rationale": "LLM output not valid JSON.", "recommendation": "Check LLM prompt."}]
        except Exception as e:
            logger.error("An unexpected error occurred during risk assessment: %s", e, exc_info=True)
            return [{"description": "Unexpected error during risk assessment.", "severity": "High", "rationale": str(e), "recommendation": "Review logs."}]
