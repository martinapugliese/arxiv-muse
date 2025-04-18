import asyncio
import logging
import os
import time
from datetime import datetime
from inspect import cleandoc

from pydantic_ai.usage import UsageLimits
from rich.console import Console
from rich.prompt import Prompt

console = Console()

# check this here because if not set the following imports will fail
if not os.getenv("GEMINI_API_KEY"):
    console.print(
        """
    [bold red]The GEMINI_API_KEY is not set. Please set it in your environment variables.[/bold red]
    [bold red]See the README for instructions.[/bold red]
    """
    )
    exit()

from askademic.allower import allower_agent
from askademic.memory import Memory
from askademic.orchestrator import orchestrator_agent
from askademic.prompts import USER_PROMPT_ALLOWER_TEMPLATE

today = datetime.now().strftime("%Y-%m-%d")

logging.basicConfig(level=logging.INFO, filename=f"{today}_logs.txt")
logger = logging.getLogger(__name__)


async def ask_me():

    console.print(
        cleandoc(
            """
    [bold cyan]Hello, welcome to Askademic![/bold cyan] :smiley:
    [bold cyan]
    You can ask me to:
    - summarize the latest literature (published in the latest available day) in an arXiv category or subcategory,
    - retrieve answers for specific research questions/topics

    Ask me a question with either of these requests.
    For the summary, I will find the best matching arXiv category to your request.
    For the specific topic, I will look for relevant papers and find the answer for you.

    I will write to a logs file filenamed with today's date.
    [/bold cyan]
    """
        )
    )

    memory = Memory(max_request_tokens=1e5)

    while True:

        try:
            user_question = Prompt.ask(
                "[bold yellow]Ask me a question (CTRL+D or type 'exit' to quit)[/bold yellow] :speech_balloon:"
            )

            if user_question.lower() == "exit":
                console.print("[bold cyan]Goodbye![/bold cyan] :wave:")
                break
        except EOFError:
            console.print("[bold cyan]Goodbye![/bold cyan] :wave:")
            break

        attempts = 0
        max_attempts = 10

        console.print(f"[bold cyan]Working for you ...[/bold cyan]")

        while attempts < max_attempts:

            try:

                allower = await allower_agent.run(
                    USER_PROMPT_ALLOWER_TEMPLATE.format(question=user_question),
                    usage_limits=UsageLimits(request_limit=20),  # limit to 20 requests
                    message_history=memory.get_messages()[
                        -2:
                    ],  # only the last 2 messages to keep the context, with 1 it loses it sometimes
                )

                if allower.data.is_scientific:
                    agent_result = await orchestrator_agent.run(
                        user_question,
                        usage_limits=UsageLimits(request_limit=20),  # limit requests
                        message_history=memory.get_messages(),
                    )
                    for k in agent_result.data.__dict__:
                        console.print(f"{k}: {getattr(agent_result.data, k)}")

                    memory.add_message(
                        agent_result.usage().total_tokens,
                        agent_result.new_messages(),
                    )
                else:
                    pun = allower.data.pun
                    console.print(
                        f"""{pun} - Ask me something scientific please! :smiley:
                    """
                    )

                break
            except Exception as e:
                logger.error(f"An error has occurred: {e}, retrying in 60 seconds...")
                time.sleep(60)
                attempts += 1


# TODO: we have to wrap because main can't be async
# this fix is temporary. We should monitor pydantic-ai issues and see when they solve it
# The workaround is described here: https://github.com/pydantic/pydantic-ai/issues/748
def main():

    asyncio.run(ask_me())


if __name__ == "__main__":
    main()
