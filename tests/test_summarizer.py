import asyncio
import os
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from pydantic_ai.agent import AgentRunResult

os.environ["GEMINI_API_KEY"] = "mocked_gemini_api_key"

from askademic.summarizer import Category, Summary, SummaryAgent, SummaryResponse

testdata = [
    (
        "get me the latest papers in AI",
        Category(category_id="cs.AI", category_name="Artificial Intelligence"),
        "2025-03-29",
        Summary(summary="Summary of cs.AI articles."),
        SummaryResponse(
            category=Category(
                category_id="cs.AI", category_name="Artificial Intelligence"
            ),
            latest_published_day="2025-03-29",
            summary="Summary of cs.AI articles.",
            recent_papers_url="https://arxiv.org/list/cs.AI/new",
        ),
    ),
    (
        "get me the latest papers in ML",
        Category(category_id="cs.LG", category_name="Machine Learning"),
        "2025-03-30",
        Summary(summary="Summary of cs.LG articles."),
        SummaryResponse(
            category=Category(category_id="cs.LG", category_name="Machine Learning"),
            latest_published_day="2025-03-30",
            summary="Summary of cs.LG articles.",
            recent_papers_url="https://arxiv.org/list/cs.LG/new",
        ),
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_request, category, latest_published_day, summary, summary_response", testdata
)
async def test_summary_agent(
    agent_request, category, latest_published_day, summary, summary_response
):
    """Test the SummaryAgent class."""
    summary_agent = SummaryAgent()
    summary_agent._category_agent = MagicMock()
    summary_agent._summary_agent = MagicMock()

    category_future = asyncio.Future()
    category_future.set_result(
        AgentRunResult(
            data=category, _result_tool_name=None, _state=None, _new_message_index=None
        )
    )
    summary_agent._category_agent.run.return_value = category_future

    summary_future = asyncio.Future()
    summary_future.set_result(
        AgentRunResult(
            data=summary, _result_tool_name=None, _state=None, _new_message_index=None
        )
    )
    summary_agent._summary_agent.run.return_value = summary_future

    summary_agent._identify_latest_day = MagicMock(return_value=latest_published_day)
    summary_agent._retrieve_recent_articles = MagicMock(return_value="")

    response = await summary_agent(agent_request)
    assert response == summary_response
