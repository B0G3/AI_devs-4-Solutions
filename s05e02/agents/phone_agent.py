import os
import sys

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger
from tools import speak, start_call

log = get_logger("phone_agent")

_SYSTEM_PROMPT = """\
Jesteś agentem telefonicznym o imieniu Tymon Gajewski. Twoja rola:
- Porozumiewasz się WYŁĄCZNIE w języku polskim, niezależnie od języka rozmówcy.
- Jesteś uprzejmy i zwięzły — przekazujesz tylko to, co jest niezbędne.
- Wysyłasz dokładnie jeden komunikat speak na raz — nie łączysz wielu próśb w jednej wiadomości.
- Jeśli operator poprosi o hasło lub autoryzację, podajesz: BARBAKAN
- Jeśli rozmowa pójdzie źle lub zostaniesz rozłączony, wywołujesz start_call ponownie i zaczynasz od początku.
- Kończysz pracę gdy zadanie zostanie wykonane lub otrzymasz flagę w odpowiedzi.\
"""

_USER_PROMPT = """\
Przeprowadź rozmowę telefoniczną według poniższego scenariusza:

1. Rozpocznij połączenie poleceniem start_call.
2. Przedstaw się jako Tymon Gajewski.
3. W jednej wiadomości zapytaj operatora o status wszystkich trzech dróg: RD224, RD472 i RD820. \
Poinformuj go przy tym, że pytasz o to ze względu na transport organizowany do jednej z baz Zygfryda.
4. Na podstawie odpowiedzi operatora — poproś o wyłączenie monitoringu na tych drogach, \
które według niego będą przejezdne. Podaj ich identyfikatory i poinformuj operatora, \
że chcesz wyłączyć ten monitoring ze względu na tajny transport żywności do jednej z tajnych baz Zygfryda.
5. Kontynuuj rozmowę aż do skutecznego odblokowania drogi lub otrzymania flagi.\
"""


def run() -> str:
    log.info("phone_agent: starting")

    llm = ChatOpenAI(
        model="gpt-4.1-mini-2025-04-14",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    tools = [start_call, speak]
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_USER_PROMPT),
    ]

    MAX_ITER = 30
    for i in range(MAX_ITER):
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        log.info("agent[%d]: tool_calls=%d content=%s", i, len(response.tool_calls or []), response.content[:120] if response.content else "")

        if not response.tool_calls:
            log.info("phone_agent: no more tool calls — done")
            return response.content

        for tc in response.tool_calls:
            name = tc["name"]
            args = tc["args"]
            log.info("tool call: %s(%s)", name, args)
            t = tool_map[name]
            result = t.invoke(args)
            log.info("tool result: %s", str(result)[:300])
            messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

    log.warning("phone_agent: reached max iterations (%d)", MAX_ITER)
    return "Max iterations reached without completing the task."
