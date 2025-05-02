from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search

# Initialize shared Gemini LLM
# GEMINI_MODEL = GeminiModel('gemini-2.5-pro-exp-03-25', provider='google-gla')
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"

# GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"
session_service = InMemorySessionService()

# 1. Define sub-agents
innovation_analyst = LlmAgent(
    name='InnovationAnalyst',
    model=GEMINI_MODEL,
    instruction="""
You are an AI analyst. Analyze the following research content and identify the core innovation, evaluating if it offers an order-of-magnitude (10×) improvement.
""",
    description='Identifies the core innovation from provided content.',
    output_key='innovation'
)

idea_generator = LlmAgent(
    name='IdeaGenerator',
    model=GEMINI_MODEL,
    instruction="""
You are a startup idea generator.
Generate 3-5 startup ideas based on the research summary and identified innovation.
Use the search tool to figure out the market environment

**Innovation:**
{innovation}
""",
    description='Generates startup ideas based on summary and innovation.',
    output_key='ideas',
    tools=[google_search]
)


market_scout = LlmAgent(
    name='MarketScout',
    model=GEMINI_MODEL,
    instruction="""
You are a market researcher.
Research market size, trends, and needs for the technology described.
Use the search tool to perform basic market analysis

**Innovation:**
{innovation}
""",
    description='Researches market data for the technology.',
    output_key='market',
    tools=[google_search]
)

# 2. Parallel stage: Idea generation and market research
idea_and_market_parallel = ParallelAgent(
    name='IdeaAndMarketParallel',
    sub_agents=[idea_generator, market_scout],
    description='Runs idea generation and market research concurrently.'
)

# 3. Sequential evaluation and compilation sub-agents
idea_evaluator = LlmAgent(
    name='IdeaEvaluator',
    model=GEMINI_MODEL,
    instruction="""
You are an idea evaluator.
Evaluate each startup idea against the market data and innovation factors.
Select and refine the top concept(s).
Use the search tool to evaluate the idea based on the above information.

**Ideas:**
{ideas}

**Market:**
{market}

**Innovation:**
{innovation}
""",
    description='Evaluates ideas against market and innovation factors.',
    output_key='evaluation',
    tools=[google_search]
)

competition_analyst = LlmAgent(
    name='CompetitionAnalyst',
    model=GEMINI_MODEL,
    instruction="""
You are a competition analyst.
Find and compare direct and indirect competitors for the selected idea.
Use Google Search tool to perform your Competitive Analysis

**Chosen Idea:**
{evaluation}
""",
    description='Analyzes competitors for the chosen idea.',
    output_key='competition',
    tools=[google_search]
)

business_model_designer = LlmAgent(
    name='BusinessModelDesigner',
    model=GEMINI_MODEL,
    instruction="""
You are a business model designer.
Outline a business model (customers, value proposition, revenue streams, channels) based on the chosen idea, market data, and competition.
Use the Google Search tool to look up Business Model related information

**Idea:**
{evaluation}

**Market:**
{market}

**Competition:**
{competition}
""",
    description='Designs a business model for the venture.',
    output_key='business_model',
    tools=[google_search]
)




risk_assessor = LlmAgent(
    name='RiskAssessor',
    model=GEMINI_MODEL,
    instruction="""
You are a risk assessor.
List major technical, market, and operational risks for the venture and suggest mitigations.
Use Google Search to find out potential risks

**Idea Evaluation:**
{evaluation}

**Business Model:**
{business_model}
""",
    description='Assesses risks and suggests mitigations.',
    output_key='risks',
    tools=[google_search]
)





venture_brief_compiler = LlmAgent(
    name='VentureBriefCompiler',
    model=GEMINI_MODEL,
    instruction="""
You are an investor brief compiler.
Compile an investor-ready brief with these sections: Overview, Technology, Market, Competition, Business Model, Risks, and Conclusion.
Include a final score from 1-5.
Use only the provided inputs.

**Innovation:**
{innovation}

**Ideas:**
{evaluation}

**Competition:**
{competition}

**Business Model:**
{business_model}

**Risks:**
{risks}
""",
    description='Compiles the final investor brief.'
)

# 4. Overall pipeline: innovation -> (ideas + market) -> evaluation -> competition -> business model -> risks -> brief
venture_pipeline = SequentialAgent(
    name='VenturePipelineAgent',
    sub_agents=[
        innovation_analyst,
        idea_and_market_parallel,
        idea_evaluator,
        competition_analyst,
        business_model_designer,
        risk_assessor,
        venture_brief_compiler
    ],
    description='Coordinates innovation analysis, parallel idea/market research, evaluation, and brief compilation.'
)

# Set the root agent
root_agent = venture_pipeline
