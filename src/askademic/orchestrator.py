from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from askademic.constants import GEMINI_2_FLASH_MODEL_ID
from askademic.prompts import SYSTEM_PROMPT_ORCHESTRATOR, USER_PROMPT_QUESTION_TEMPLATE
from askademic.question import QuestionAnswerResponse, question_agent
from askademic.summarizer import SummaryResponse, summary_agent


class Context(BaseModel):
    pass


orchestrator_agent = Agent(
    GEMINI_2_FLASH_MODEL_ID,
    system_prompt=SYSTEM_PROMPT_ORCHESTRATOR,
    result_type=SummaryResponse | QuestionAnswerResponse,
    model_settings={"max_tokens": 1000, "temperature": 0},
)


@orchestrator_agent.tool
async def summarise_latest_articles(
    ctx: RunContext[Context], request: str
) -> list[str]:
    """
    Make a request to an agent about the most recent paper in a specific field.
    Args:
        ctx: the context
        request: the request
    """
    r = await summary_agent(request=request)
    return r


@orchestrator_agent.tool
async def answer_question(ctx: RunContext[Context], question: str) -> list[str]:
    """
    Ask an agent to search on arXiv and access articles to answer a question.
    Args:
        ctx: the context
        question: the question
    """

    prompt = USER_PROMPT_QUESTION_TEMPLATE.format(question=question)
    r = await question_agent.run(prompt)
    return r
