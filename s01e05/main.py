import os
import re

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from tools import ALL_TOOLS

FLAG_PATTERN = re.compile(r"\{FLG:[^}]+\}")

load_dotenv()

SYSTEM_PROMPT = """Jesteś asystentem odpowiedzialnym za zarządzanie trasami kolejowymi.

Masz dostęp do zestawu narzędzi — używaj ich zgodnie z ich dokumentacją: przekazuj wymagane parametry, nie pomijaj żadnych kroków wymaganych przez API.

Zasady działania:
- Przed wykonaniem operacji zweryfikuj dostępność zasobu (trasy, tory, stacje), jeśli API to umożliwia.
- Gdy operacja się nie powiedzie, zgłoś błąd użytkownikowi zamiast próbować obejść ograniczenie.
- Odpowiadaj zwięźle, skupiaj się na wyniku operacji."""

AGENT_CONFIG = {"recursion_limit": 10}


def main():
    llm = ChatOpenAI(model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))
    agent = create_agent(llm, ALL_TOOLS, system_prompt=SYSTEM_PROMPT)

    result = agent.invoke(
        {"messages": [HumanMessage(content="Aktywuj trasę kolejową o nazwie X-01")]},
        config=AGENT_CONFIG,
    )

    final_message = result["messages"][-1].content

    flags = FLAG_PATTERN.findall(final_message)
    if flags:
        for flag in flags:
            print(f"Flag found: {flag}")
            resp = requests.post(
                f"{os.getenv('HUB_URL')}/verify",
                json={"apikey": os.getenv("AGENT_API_KEY"), "task": "railway", "answer": flag},
            )
            print(f"Flag submission: {resp.status_code} {resp.json()}")
        return

    print(final_message)


if __name__ == "__main__":
    main()
