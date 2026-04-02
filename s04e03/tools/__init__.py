from tools.api import TOOL_DEF, call_api, reset_game

CODE_INTERPRETER = {"type": "code_interpreter", "container": {"type": "auto"}}

TOOLS = [CODE_INTERPRETER, TOOL_DEF]
TOOL_MAP = {"call_api": call_api}
