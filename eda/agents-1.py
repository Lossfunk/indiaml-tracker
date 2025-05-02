# main_pydantic_ai.py
from __future__ import annotations as _annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict, Tuple

# Third-party libraries
import logfire # Optional, for enhanced logging/tracing
from devtools import debug # For printing results clearly
from httpx import AsyncClient
from dotenv import load_dotenv

# Pydantic and Pydantic-AI
from pydantic import BaseModel, Field, HttpUrl
from pydantic_ai import Agent, RunContext # Or other providers

# Load environment variables (e.g., for API keys)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Configure Logfire (optional)
# logfire.configure(send_to_logfire='if-token-present') # Or configure as needed

# --- Shared Pydantic Models (Inputs/Outputs for Stages) ---
# (These models remain largely the same as in the previous version)

class ResearchInput(BaseModel):
    """Input data for the workflow."""
    research_paper_location: str = Field(description="Path or URL to the research paper (e.g., PDF link).")
    domain_constraints: Optional[List[str]] = Field(default=None, description="Any specific domain constraints or areas of focus.")

class SummaryOutput(BaseModel):
    """Output of the Summariser stage."""
    bullet_points: List[str] = Field(..., description="<=20 bullet points covering claim, method, results, limitations, reproducibility.")

class Hypothesis(BaseModel):
    """Represents a single commercial hypothesis."""
    id: int
    target_user: str = Field(..., description="Specific user segment targeted.")
    current_workflow: str = Field(..., description="The existing, demonstrated behaviour/workflow.")
    pain_metric: str = Field(..., description="How the pain/inefficiency is measured.")
    envisioned_solution: str = Field(..., description="The proposed new solution.")
    form_factor: str = Field(..., description="How the solution is delivered (e.g., SaaS, mobile app, API).")

class IdeaOutput(BaseModel):
    """Output of the Idea-Generator stage."""
    hypotheses: List[Hypothesis] = Field(..., description="8-12 distinct commercial hypotheses.")

class MarketData(BaseModel):
    """Market data gathered for a specific hypothesis."""
    hypothesis_id: int
    existing_incumbents: List[str] = Field(default_factory=list, description="List of existing companies or solutions.")
    substitutes: List[str] = Field(default_factory=list, description="Alternative ways users solve the problem.")
    pricing_benchmarks: Optional[str] = Field(default=None, description="Public pricing or cost info.")
    adoption_evidence: Optional[str] = Field(default=None, description="Signs of current user adoption of existing solutions.")
    tam_sam_figures: Optional[str] = Field(default=None, description="Rough Total Addressable Market / Serviceable Available Market figures.")
    search_queries_used: List[str] = Field(default_factory=list, description="Queries used to find this data.") # Added for traceability

class MarketScoutOutput(BaseModel):
    """Output of the Market-Scout stage."""
    market_data_list: List[MarketData]

class ScoredHypothesis(BaseModel):
    """A hypothesis scored according to the 10x rubric."""
    hypothesis: Hypothesis
    market_data: Optional[MarketData] # Market data might not always be found
    behaviour_verified: bool = Field(..., description="Is the target behaviour demonstrably in use?")
    potential_efficiency_gain: int = Field(..., ge=1, le=5, description="Estimated gain (1-5 scale, 5 ≈ ≥10×).")
    technical_defensibility: int = Field(..., ge=1, le=5, description="Score for technical difficulty to replicate.")
    g_t_m_accessibility: int = Field(..., ge=1, le=5, description="Score for ease of reaching target users.")
    overall_attractiveness: int = Field(..., ge=1, le=5, description="Normalized score (1-5).")
    justification: str = Field(..., description="Reasoning behind the scores.")

class ImpactScoreOutput(BaseModel):
    """Output of the Impact-Scorer stage."""
    scored_hypotheses: List[ScoredHypothesis]

class CritiquedHypothesis(BaseModel):
    """A scored hypothesis after critical review."""
    scored_hypothesis: ScoredHypothesis
    identified_risks: List[str] = Field(..., description="Specific risks identified (regulatory, legal, supply-chain, CapEx, incumbent unbundling).")
    revised_attractiveness: int = Field(..., ge=1, le=5, description="Revised overall score after considering risks.")
    critique_summary: str = Field(..., description="Summary of the critical review.")

class RedTeamOutput(BaseModel):
    """Output of the Red-Teamer stage."""
    critiqued_hypotheses: List[CritiquedHypothesis]

class CaseStudy(BaseModel):
    """Information about an analogous real-world company."""
    company_name: str
    link: Optional[HttpUrl] = None
    analogy_reason: str = Field(..., description="Why this company/situation is analogous (1 sentence).")
    scale_status_exit: str = Field(..., description="Current scale, funding status, or exit information.")
    search_queries_used: List[str] = Field(default_factory=list, description="Queries used to find this data.") # Added for traceability

class CaseStudyOutput(BaseModel):
    """Output of the Case-Study Identifier stage for one hypothesis."""
    hypothesis_id: int
    case_studies: List[CaseStudy]

class AllCaseStudiesOutput(BaseModel):
    """Container for all case studies found."""
    identified_case_studies: List[CaseStudyOutput]

class StrategicInsights(BaseModel):
    """Strategic lessons and founder fit for a hypothesis."""
    hypothesis_id: int
    strategic_lessons: List[str] = Field(..., description="3 key strategic lessons learned from case studies.")
    founder_fit_traits: List[str] = Field(..., description="3 founder traits or unfair advantages needed.")

class StrategicAnalysisOutput(BaseModel):
    """Output of the Strategic-Analyst stage."""
    all_insights: List[StrategicInsights]

class VentureBrief(BaseModel):
    """A polished venture brief for a single hypothesis."""
    hypothesis_id: int
    elevator_pitch: str = Field(..., description="One-line pitch for the venture.")
    day_1_switcher_profile: str = Field(..., description="Profile of the ideal early adopter.")
    why_they_convert: str = Field(..., description="The compelling reason for immediate adoption.")
    milestone_roadmap_12_months: Dict[str, str] = Field(..., description="Key tech and commercial milestones for the first year.")
    killer_risks: List[str] = Field(..., description="The most critical risks identified.")
    de_risking_experiments: List[str] = Field(..., description="Rapid experiments to address killer risks.")
    founder_playbook: List[str] = Field(..., description="Actionable playbook aligned to strategic lessons.")

class VentureEditorOutput(BaseModel):
    """Output of the Venture-Editor stage - the final venture briefs."""
    venture_briefs: List[VentureBrief]


# --- Dependencies ---
@dataclass
class Deps:
    """Dependencies needed by the agents and tools."""
    http_client: AsyncClient = field(default_factory=AsyncClient)
    # Add other potential dependencies: e.g., database connections, specific API keys
    # google_api_key: str | None = os.getenv("GOOGLE_API_KEY") # pydantic-ai handles this internally if configured

# --- Agent Definitions ---

# Configure the LLM model (replace with your desired model)
# Ensure GOOGLE_API_KEY environment variable is set if using Google
LLM_MODEL = "google-gla:gemini-2.5-flash-preview-04-17" # Replace with your preferred model like "gpt-4o" etc.

# Agent 1: Summariser
summarizer_agent = Agent(
    model=LLM_MODEL,
    output_model=SummaryOutput,
    system_prompt=(
        "You are an expert academic paper summarizer. "
        "Read the provided text content of a research paper. "
        "Identify and extract the main claim, methodology, key results, significant limitations, and any notes on reproducibility. "
        "Format the output as a list of concise bullet points (maximum 20). "
        "Focus only on the core aspects requested."
    ),
    deps_type=Deps,
    retries=2,
    instrument=True, # Enable logfire instrumentation if configured
)

@summarizer_agent.tool
async def extract_summary_points(ctx: RunContext[Deps], paper_content: str) -> SummaryOutput:
    """
    Processes the paper content to extract summary points based on the system prompt.
    This tool primarily relies on the LLM's capability guided by the system prompt
    and the output model definition.

    Args:
        ctx: The run context.
        paper_content: The full text content of the research paper.

    Returns:
        A SummaryOutput object containing the structured bullet points.
    """
    # The actual extraction is handled by the agent's LLM call based on the prompt
    # and the paper_content provided. pydantic-ai will automatically try to
    # structure the LLM response into the SummaryOutput model.
    # This tool function acts as the entry point for the agent's core task.
    logging.info("LLM processing paper content for summary...")
    # No explicit LLM call needed here; pydantic-ai handles it.
    # We just need to ensure the input 'paper_content' is passed correctly.
    # The return type hint `-> SummaryOutput` guides pydantic-ai.
    # If the LLM fails to produce the correct structure, pydantic-ai raises an error.
    pass # Placeholder: Actual logic is implicit in the agent's run method

# Agent 2: Idea Generator
idea_generator_agent = Agent(
    model="google-gla:gemini-2.5-flash-preview-04-17",
    output_model=IdeaOutput,
    system_prompt=(
        "You are a creative technologist and entrepreneur specializing in commercializing research. "
        "Based on the provided research paper summary and domain constraints, brainstorm 8-12 distinct commercial hypotheses. "
        "For each hypothesis, clearly define: the target user, their current demonstrated workflow/behavior related to the research, "
        "the primary pain metric (e.g., time saved, cost reduced), the envisioned solution derived from the research, "
        "and the likely form-factor (e.g., SaaS, API, library, hardware). "
        "Ensure hypotheses are grounded in the research summary."
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
)

@idea_generator_agent.tool
async def generate_hypotheses_from_summary(
    ctx: RunContext[Deps],
    summary: SummaryOutput,
    domain_constraints: Optional[List[str]]
) -> IdeaOutput:
    """
    Generates commercial hypotheses based on the paper summary and constraints.

    Args:
        ctx: The run context.
        summary: The structured summary of the research paper.
        domain_constraints: Optional constraints for idea generation.

    Returns:
        An IdeaOutput object containing a list of generated hypotheses.
    """
    logging.info("LLM generating commercial hypotheses...")
    # Again, the core logic is handled by the agent's LLM call.
    # We structure the input for the LLM.
    prompt_input = f"Research Summary:\n{chr(10).join(summary.bullet_points)}"
    if domain_constraints:
        prompt_input += f"\n\nDomain Constraints: {', '.join(domain_constraints)}"

    # pydantic-ai uses the function arguments and the agent's prompt
    # This tool function mainly serves to structure how data is passed implicitly.
    pass # Placeholder

# --- Stages Implemented as Async Functions (Potentially using Tools/APIs) ---

async def run_market_scout_async(ideas: IdeaOutput, deps: Deps) -> MarketScoutOutput:
    """
    Placeholder for Market Scout stage. Finds market data for each hypothesis.
    This would involve formulating search queries and using search APIs/tools.
    """
    logging.info("Scouting market data for hypotheses...")
    market_data_collected = []
    # Example: Use httpx client from deps for a hypothetical search API
    # Or potentially use a dedicated Search Tool/Agent if available
    for hypo in ideas.hypotheses:
        logging.info(f"  Scouting for Hypothesis {hypo.id}: {hypo.envisioned_solution}")
        # --- Placeholder Logic ---
        # 1. Formulate search queries (e.g., "{hypo.envisioned_solution} competitors", "{hypo.target_user} market size")
        queries = [
            f"{hypo.envisioned_solution} competitors",
            f"{hypo.target_user} {hypo.pain_metric} existing solutions",
            f"{hypo.envisioned_solution} pricing",
            f"{hypo.target_user} market size estimate"
        ]
        # 2. Use search APIs (e.g., Google Search tool, SerpAPI, etc.) via deps.http_client or specific tools
        #    (Simulating search results here)
        simulated_results = {
            "incumbents": ["Competitor A", "Incumbent B Tool"],
            "substitutes": ["Manual process", "In-house scripts"],
            "pricing": "$50/user/month (Competitor A)",
            "adoption": "High usage of forums discussing the manual process pain",
            "market_size": "TAM: $1B, SAM: $100M (estimated)"
        }
        # 3. Synthesize findings into the MarketData model.
        data = MarketData(
            hypothesis_id=hypo.id,
            existing_incumbents=simulated_results["incumbents"],
            substitutes=simulated_results["substitutes"],
            pricing_benchmarks=simulated_results["pricing"],
            adoption_evidence=simulated_results["adoption"],
            tam_sam_figures=simulated_results["market_size"],
            search_queries_used=queries
        )
        await asyncio.sleep(0.1) # Simulate async work
        market_data_collected.append(data)

    logging.info("Market scouting complete.")
    return MarketScoutOutput(market_data_list=market_data_collected)

# --- Placeholder Agents/Functions for Remaining Stages ---
# (These would follow similar patterns, defining Agents for LLM-heavy tasks
# and potentially async functions for data gathering/processing)

# Agent 3: Impact Scorer (Example Structure)
impact_scorer_agent = Agent(
    model=LLM_MODEL,
    output_model=ImpactScoreOutput,
    system_prompt=(
        "You are a venture capital analyst applying the '10x Better Litmus Test'. "
        "For each hypothesis provided, analyze the idea, its context (target user, current workflow), and market data. "
        "Score the hypothesis based on: "
        "1. Behaviour Verified: Is the 'current_workflow' a real, demonstrated user behaviour (True/False)? Use market data adoption evidence. "
        "2. Potential Efficiency Gain (1-5): Estimate the potential improvement over the status quo (5 = 10x or more). "
        "3. Technical Defensibility (1-5): How hard is the tech to replicate? "
        "4. GTM Accessibility (1-5): How easy is it to reach the target user? "
        "5. Overall Attractiveness (1-5): Your normalized judgment based on the above. "
        "Provide a concise justification for your scores."
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
)

@impact_scorer_agent.tool
async def score_hypotheses_tool(
    ctx: RunContext[Deps],
    hypotheses_with_market_data: List[Tuple[Hypothesis, Optional[MarketData]]]
) -> ImpactScoreOutput:
    """
    Scores hypotheses based on the 10x rubric, using provided market data.

    Args:
        ctx: The run context.
        hypotheses_with_market_data: A list of tuples, each containing a hypothesis
                                     and its corresponding market data (or None).

    Returns:
        An ImpactScoreOutput object with scored hypotheses.
    """
    logging.info("LLM scoring hypotheses...")
    # The agent will process the list and generate scores based on the prompt.
    # The input needs to be formatted clearly for the LLM.
    # pydantic-ai will handle structuring the output.
    pass # Placeholder

# --- (Define RedTeamerAgent, CaseStudyIdentifier (async func?), StrategicAnalystAgent, VentureEditorAgent similarly) ---

# Example Placeholder for Case Study Identifier (as async function)
async def run_case_study_identifier_async(critiqued_output: RedTeamOutput, deps: Deps) -> AllCaseStudiesOutput:
    logging.info("Identifying case studies for top hypotheses...")
    all_studies = []
     # Similar logic to market scout: formulate queries, use search tools/APIs
    for critiqued_hypo in critiqued_output.critiqued_hypotheses:
        hypo_id = critiqued_hypo.scored_hypothesis.hypothesis.id
        logging.info(f"  Finding case studies for Hypothesis {hypo_id}")
        # --- Placeholder Logic ---
        queries = [
             f"startup similar to {critiqued_hypo.scored_hypothesis.hypothesis.envisioned_solution}",
             f"{critiqued_hypo.scored_hypothesis.hypothesis.target_user} market challengers",
             f"competitors {critiqued_hypo.scored_hypothesis.market_data.existing_incumbents[0]} acquisition" # Example query
        ]
        # Simulate search & extraction
        studies = [
            CaseStudy(
                company_name="Analogous Startup X",
                link=HttpUrl("https://example.com/startupX"),
                analogy_reason="Also targeted researchers with an AI summarization tool.",
                scale_status_exit="Acquired by Publisher Y for $20M after reaching 50k users.",
                search_queries_used=[queries[0]]
            ),
        ]
        await asyncio.sleep(0.1) # Simulate async work
        all_studies.append(CaseStudyOutput(hypothesis_id=hypo_id, case_studies=studies))

    logging.info("Case study identification complete.")
    return AllCaseStudiesOutput(identified_case_studies=all_studies)


# --- Main Workflow Orchestration (Async) ---

async def fetch_paper_content(location: str, client: AsyncClient) -> str:
    """Fetches paper content from URL or local path."""
    if location.startswith("http"):
        try:
            response = await client.get(location)
            response.raise_for_status()
            # Basic PDF text extraction (replace with a robust library like PyPDF2 or pdfminer.six)
            if ".pdf" in location.lower():
                 logging.warning("Basic PDF parsing. Consider using a dedicated library.")
                 # This is a placeholder - real PDF parsing is complex.
                 # For now, returning a dummy string. Replace with actual parsing.
                 # Example using PyPDF2 (install it first: pip install pypdf2)
                 # import io
                 # from PyPDF2 import PdfReader
                 # try:
                 #     pdf_file = io.BytesIO(response.content)
                 #     reader = PdfReader(pdf_file)
                 #     text = ""
                 #     for page in reader.pages:
                 #         text += page.extract_text() or ""
                 #     if not text:
                 #        return "Dummy Paper Content: Could not extract text from PDF."
                 #     return text[:10000] # Limit length for LLM context
                 # except Exception as e:
                 #     logging.error(f"PDF parsing failed: {e}")
                 #     return "Dummy Paper Content: Error parsing PDF."
                 return "Dummy Paper Content: Placeholder for PDF text." # Placeholder
            else:
                return response.text # Assume text format
        except Exception as e:
            logging.error(f"Failed to fetch paper from URL {location}: {e}")
            raise
    elif os.path.exists(location):
        try:
            with open(location, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Failed to read paper from path {location}: {e}")
            raise
    else:
        raise FileNotFoundError(f"Paper location not found: {location}")


async def process_research_paper_pipeline(paper_input: ResearchInput, deps: Deps) -> Optional[VentureEditorOutput]:
    """
    Orchestrates the asynchronous nine-stage workflow using pydantic-ai Agents.
    """
    logging.info("Starting async research-to-startup workflow...")
    all_results = {} # Dictionary to store results from each stage

    try:
        # --- Stage 0: Fetch Paper Content ---
        paper_content = await fetch_paper_content(paper_input.research_paper_location, deps.http_client)
        if not paper_content:
             logging.error("Workflow failed: Could not retrieve paper content.")
             return None
        logging.info(f"Paper content fetched (length: {len(paper_content)} chars).")
        # Limit content length if necessary for LLM context window
        max_len = 20000
        if len(paper_content) > max_len:
            logging.warning(f"Truncating paper content to {max_len} characters.")
            paper_content = paper_content[:max_len]


        # --- Stage 1: Summariser ---
        logging.info("Running Summarizer Agent...")
        # Pass paper content directly to the tool via agent's run method arguments
        summary_result = await summarizer_agent.run(
            # The names here must match the parameter names in the tool function
            {'paper_content': paper_content},
            deps=deps
        )
        summary: SummaryOutput = summary_result.output
        all_results['summary'] = summary
        debug(summary)
        if not summary or not summary.bullet_points:
            logging.error("Workflow failed: Summarisation produced no output.")
            return None

        # --- Stage 2: Idea-Generator ---
        logging.info("Running Idea Generator Agent...")
        idea_result = await idea_generator_agent.run(
             # Pass summary and constraints to the tool
            {'summary': summary, 'domain_constraints': paper_input.domain_constraints},
            deps=deps
        )
        ideas: IdeaOutput = idea_result.output
        all_results['ideas'] = ideas
        debug(ideas)
        if not ideas or not ideas.hypotheses:
            logging.error("Workflow failed: Idea generation produced no output.")
            return None

        # --- Stage 3: Market-Scout ---
        logging.info("Running Market Scout...")
        market_data = await run_market_scout_async(ideas, deps)
        all_results['market_data'] = market_data
        debug(market_data)
        if not market_data.market_data_list:
            logging.warning("Market scouting yielded no results, proceeding with caution.")
            # Create an empty list if needed by downstream steps
            market_data_map = {}
        else:
             market_data_map = {md.hypothesis_id: md for md in market_data.market_data_list}


        # --- Stage 4: Impact-Scorer ---
        logging.info("Running Impact Scorer Agent...")
        # Prepare input for the scorer tool
        hypotheses_to_score = [
            (hypo, market_data_map.get(hypo.id)) for hypo in ideas.hypotheses
        ]
        # Need to serialize Pydantic models for the LLM if passing complex objects
        # Or adjust the tool to accept simpler structures / rely on LLM parsing text
        # For simplicity here, we assume the agent handles the input structure
        scored_result = await impact_scorer_agent.run(
             {'hypotheses_with_market_data': hypotheses_to_score}, # This might need adjustment based on LLM/tool capability
             deps=deps
        )
        scored_output: ImpactScoreOutput = scored_result.output
        all_results['scored_output'] = scored_output
        debug(scored_output)
        if not scored_output or not scored_output.scored_hypotheses:
             logging.error("Workflow failed: Impact scoring produced no output.")
             return None
        # Sort by attractiveness
        scored_output.scored_hypotheses.sort(key=lambda x: x.overall_attractiveness, reverse=True)


        # --- Stage 5: Red-Teamer / Critic ---
        logging.info("Running Red Teamer Agent...")
        # (Define and run RedTeamerAgent similar to others)
        # Placeholder: Simulate critique
        critiqued_hypotheses = []
        top_n_critique = 5
        for scored_hypo in scored_output.scored_hypotheses[:top_n_critique]:
             critiqued_hypotheses.append(CritiquedHypothesis(
                  scored_hypothesis=scored_hypo,
                  identified_risks=["Simulated Risk 1: Incumbent reaction", "Simulated Risk 2: Scalability challenge"],
                  revised_attractiveness=max(1, scored_hypo.overall_attractiveness - 1),
                  critique_summary="Simulated critique reducing score due to risks."
             ))
        critiqued_output = RedTeamOutput(critiqued_hypotheses=critiqued_hypotheses)
        critiqued_output.critiqued_hypotheses.sort(key=lambda x: x.revised_attractiveness, reverse=True)
        all_results['critiqued_output'] = critiqued_output
        debug(critiqued_output)
        if not critiqued_output or not critiqued_output.critiqued_hypotheses:
             logging.error("Workflow failed: Red-teaming produced no output.")
             return None


        # --- Stage 6: Case-Study Identifier ---
        logging.info("Running Case Study Identifier...")
        case_studies_output = await run_case_study_identifier_async(critiqued_output, deps)
        all_results['case_studies'] = case_studies_output
        debug(case_studies_output)
        # It's okay if some hypotheses don't have case studies


        # --- Stage 7: Strategic-Analyst ---
        logging.info("Running Strategic Analyst Agent...")
        # (Define and run StrategicAnalystAgent)
        # Placeholder: Simulate analysis
        strategic_insights_list = []
        insights_map = {cs.hypothesis_id: cs.case_studies for cs in case_studies_output.identified_case_studies}
        critiqued_map = {c.scored_hypothesis.hypothesis.id: c for c in critiqued_output.critiqued_hypotheses}

        for hypo_id, studies in insights_map.items():
            if studies and hypo_id in critiqued_map: # Only analyze if we have studies and the hypothesis survived critique
                 strategic_insights_list.append(StrategicInsights(
                      hypothesis_id=hypo_id,
                      strategic_lessons=["Simulated Lesson 1: Go freemium", "Simulated Lesson 2: Build community", "Simulated Lesson 3: Focus on UX"],
                      founder_fit_traits=["Simulated Trait 1: Domain expert", "Simulated Trait 2: Sales experience", "Simulated Trait 3: Technical lead"]
                 ))
        strategic_output = StrategicAnalysisOutput(all_insights=strategic_insights_list)
        all_results['strategic_output'] = strategic_output
        debug(strategic_output)


        # --- Stage 8: Venture-Editor ---
        logging.info("Running Venture Editor Agent...")
        # (Define and run VentureEditorAgent)
        # Placeholder: Simulate brief generation
        venture_briefs = []
        top_n_briefs = 3
        final_hypo_ids = [c.scored_hypothesis.hypothesis.id for c in critiqued_output.critiqued_hypotheses][:top_n_briefs]
        strategic_insights_map = {s.hypothesis_id: s for s in strategic_output.all_insights}

        for hypo_id in final_hypo_ids:
             critique = critiqued_map.get(hypo_id)
             insights = strategic_insights_map.get(hypo_id)
             if critique and insights: # Need both critique and insights
                  brief = VentureBrief(
                        hypothesis_id=hypo_id,
                        elevator_pitch=f"Simulated Pitch for {critique.scored_hypothesis.hypothesis.envisioned_solution}",
                        day_1_switcher_profile=f"Simulated Profile for {critique.scored_hypothesis.hypothesis.target_user}",
                        why_they_convert="Simulated strong value proposition.",
                        milestone_roadmap_12_months={"M3": "MVP", "M6": "Pilots", "M12": "Growth"},
                        killer_risks=critique.identified_risks,
                        de_risking_experiments=["Simulated Experiment 1", "Simulated Experiment 2"],
                        founder_playbook=insights.strategic_lessons # Use lessons as playbook items
                  )
                  venture_briefs.append(brief)

        final_output = VentureEditorOutput(venture_briefs=venture_briefs)
        all_results['final_output'] = final_output
        debug(final_output)

        if not final_output.venture_briefs:
            logging.warning("Workflow completed, but no final venture briefs were generated.")
            # Return None or an empty output object depending on desired behavior
            return None

        logging.info("Workflow completed successfully.")
        # Optionally return all intermediate results: return all_results
        return final_output

    except Exception as e:
        logging.exception(f"An error occurred during the async workflow: {e}")
        # Optionally return partial results if needed: return all_results
        return None
    finally:
        # Ensure the HTTP client is closed if it was created here
        # If passed in, the caller should manage its lifecycle
        # await deps.http_client.aclose() # Close if created within this function
        pass


# --- Example Usage ---
async def main():
    # Use the HTTP client context manager for proper cleanup
    async with AsyncClient() as client:
        deps = Deps(http_client=client)

        # Example input - replace with actual paper link/path
        # Using a known accessible text page for demonstration as PDF parsing is complex
        input_data = ResearchInput(
            research_paper_location="https://arxiv.org/pdf/2305.10601.pdf", # Requires robust PDF parsing
            # research_paper_location="https://example.com", # Simple HTML page for testing flow
            domain_constraints=["Focus on B2B SaaS applications", "Avoid hardware components"]
        )

        final_output = await process_research_paper_pipeline(input_data, deps)

        print("\n--- Workflow Execution Summary ---")
        if final_output:
            print(f"Successfully generated {len(final_output.venture_briefs)} venture brief(s).")
            # Full output was printed using debug() during execution
            # You can add more detailed printing here if needed
            print("\n--- Top Venture Brief ---")
            if final_output.venture_briefs:
                 brief = final_output.venture_briefs[0]
                 print(f"  Hypothesis ID: {brief.hypothesis_id}")
                 print(f"  Pitch: {brief.elevator_pitch}")
                 print(f"  Switcher: {brief.day_1_switcher_profile}")
                 print(f"  Risks: {', '.join(brief.killer_risks)}")
            else:
                 print("  No briefs generated.")

        else:
            print("Workflow did not complete successfully or produced no briefs.")

if __name__ == "__main__":
    # To run with logfire tracing (if configured):
    # logfire.instrument_async()
    asyncio.run(main())
