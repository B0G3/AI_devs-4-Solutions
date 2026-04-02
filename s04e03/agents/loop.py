"""Shared agent loop using the OpenAI Responses API."""

import json

from openai import OpenAI

client = OpenAI()


def run_loop(model: str, system_prompt: str, task: str, tools: list, tool_map: dict) -> str:
    input_items: list[dict] = [{"role": "user", "content": task}]

    while True:
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=input_items,
            tools=tools,
        )

        input_items += [item.model_dump() for item in response.output]

        function_calls = [item for item in response.output if item.type == "function_call"]

        if not function_calls:
            break

        for fc in function_calls:
            args = json.loads(fc.arguments)
            fn = tool_map.get(fc.name)
            if fn is None:
                result = json.dumps({"error": f"unknown tool: {fc.name}"})
            else:
                action = args.pop("action")
                result = fn(action=action, **args)
            input_items.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": result,
            })

    text_items = [item for item in response.output if item.type == "message"]
    return text_items[-1].content[0].text if text_items else "(no text output)"
