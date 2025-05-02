import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

# 1. Initialize the shared model
model = GeminiModel('gemini-2.5-pro-exp-03-25', provider='google-gla')  # you can swap in any supported model :contentReference[oaicite:4]{index=4}

# 2. Define each agent (summarizer, analyst, etc.)
# research_summarizer = Agent(
#     model=model,
#     deps_type=str,
#     output_type=str,
#     system_prompt=(
#         "Summarize the research paper text"
#         "focusing on context, innovation, results, and key metrics."
#     ),
# )


innovation_analyst = Agent(
    model=model,
    output_type=str,
    system_prompt=(
        "Analyze the summary in Identify the core innovation "
        "and evaluate if it offers an order-of-magnitude (10×) improvement."
    ),
)



idea_generator = Agent(
    model=model,
    deps_type=dict,   # {'summary': str, 'innovation': str}
    output_type=str,
    system_prompt=(
        "Generate 3–5 startup ideas based on summary and innovation."
    ),
)



market_scout = Agent(
    model=model,
    deps_type=dict,
    output_type=str,
    system_prompt=(
        "Research market sizes, trends, and needs for the technology described "
        "in summary and innovation."
    ),
)

idea_evaluator = Agent(
    model=model,
    deps_type=dict,   # {'ideas': str, 'market': str, 'innovation': str}
    output_type=str,
    system_prompt=(
        "Evaluate each idea in ideas against the market data "
        "in market and the 10× factors in innovation. "
        "Select and refine the top concept(s)."
    ),
)

competition_analyst = Agent(
    model=model,
    deps_type=str,    # chosen-idea description
    output_type=str,
    system_prompt=(
        "Find and compare direct/indirect competitors for the idea in dependencies."
    ),
)

business_model_designer = Agent(
    model=model,
    deps_type=dict,   # {'idea': str, 'market': str, 'competition': str}
    output_type=str,
    system_prompt=(
        "Outline a business model (customers, value prop, revenue, channels) "
        "based on dependencies."
    ),
)

risk_assessor = Agent(
    model=model,
    deps_type=dict,   # {'idea': str, 'business_model': str}
    output_type=str,
    system_prompt=(
        "List major technical, market, and operational risks for the venture "
        "in dependencies and suggest mitigations."
    ),
)

venture_brief_compiler = Agent(
    model=model,
    deps_type=dict,   # aggregates all prior outputs
    output_type=str,
    system_prompt=(
        "Compile an investor-ready brief with sections: Overview, Technology, Market, "
        "Competition, Business Model, Risks, and Conclusion, using dependencies."
    ),
)




async def  main(md_path: str):
    # 3. Load the paper text
    md_content = open(md_path, 'r', encoding='utf-8').read()  # replace with your loader :contentReference[oaicite:5]{index=5}

    # 4. Stage 1 & 2
    innovation = (await innovation_analyst.run("Analyze the following: \n " + md_content)).output

    print(f"========INNOVATION:============\n{innovation}")

    # 5. Parallel stages: ideas & market
    idea_f = idea_generator.run(
        f"Ideas:\nSummary: {md_content}\n---\nInnovation: {innovation}",
    )

    market_f =  market_scout.run(
        f"Market:\nSummary: {md_content}\n---\nInnovation: {innovation}",
    )

    ideas = (await idea_f).output
    market = (await market_f).output

    # print(f"=======IDEAS")
    print(f"========IDEAS:============\n{ideas}")
    print(f"========MARKET:============\n{market}")


    # 6. Sequential stages
    evaluation = (await idea_evaluator.run(
        f"Evaluate:\nIdeas: {ideas}\n---\nInnovation: {innovation}",
    )).output

    print(f"========EVALUATION============\n{evaluation}")



    competition = (await competition_analyst.run(f"Competition:\nCompetition: {evaluation}")).output

    print(f"========COMPETITION============\n{competition}")


    business_model = (await business_model_designer.run(
        f"Business Model:\nEvaluation: {evaluation}\n---\nMarket: {market}\nCompetion: {competition}",
    )).output

    print(f"========BUSINESS MODEL============\n{business_model}")


    risks = (await risk_assessor.run(
        f"Risks:\nIdea: {evaluation}\n---\nBusiness Model: {business_model}",
    )).output

    print(f"========RISKS============\n{risks}")


    # # 7. Final compilation
    brief = (await venture_brief_compiler.run(
        f"""Compile Brief and award a final score from 1-5 based on the following information
        {{
            'summary': {md_content},
            'innovation': {innovation},
            'market': {market},
            'ideas': {evaluation},
            'competition': {competition},
            'business_model': {business_model},
            'risks': {risks},
        }}
        """
    )).output

    print(f"========BRIEF============\n{brief}")


if __name__ == "__main__":
    import sys
    asyncio.run(main(sys.argv[1]))
    # main(sys.argv[1])
