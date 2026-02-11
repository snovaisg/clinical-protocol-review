from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from mcp_interface.protocol_server import ProtocolServer
import os

class PIAgent:
    def __init__(self, llm_model="gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.5, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_template = PromptTemplate(
            template="""
            You are a Principal Investigator reviewing a clinical trial protocol.
            Your focus is on the feasibility of the study, the scientific rigor, and patient safety from a research leadership perspective.
            Identify any potential issues that could lead to amendments, suggest improvements, and provide a clear rationale.

            Review the following protocol content:
            {protocol_content}

            Provide your feedback in a structured format, highlighting concerns and recommendations.
            Focus on:
            - Overall scientific soundness and relevance.
            - Feasibility of patient recruitment and retention.
            - Adequacy of safety monitoring and adverse event reporting.
            - Clarity and completeness of study objectives and endpoints.
            - Potential for bias or ethical concerns.
            - Any sections that are unclear or contradictory.
            """,
            input_variables=["protocol_content"]
        )
        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def review_protocol(self, protocol_server: ProtocolServer) -> str:
        full_protocol = protocol_server.get_all_content()
        response = self.chain.invoke({"protocol_content": full_protocol})
        return response
