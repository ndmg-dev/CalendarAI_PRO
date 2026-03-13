"""LangChain orchestrator — AI agent with tool-calling for scheduling."""

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.ai.tools.create_event import create_event_tool
from app.ai.tools.list_events import list_events_tool
from app.ai.tools.update_event import update_event_tool
from app.ai.tools.cancel_event import cancel_event_tool

logger = logging.getLogger(__name__)

# All available scheduling tools
SCHEDULING_TOOLS = [
    create_event_tool,
    list_events_tool,
    update_event_tool,
    cancel_event_tool,
]

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / "system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    logger.warning("System prompt file not found at %s, using fallback", prompt_path)
    return (
        "Você é a assistente de agendamentos do CalendAI PRO. "
        "Ajude o usuário a gerenciar seus eventos usando as ferramentas disponíveis. "
        "Responda em português brasileiro."
    )


def _get_context_header(user_name: str, user_timezone: str) -> str:
    """Generate dynamic context for the current request."""
    tz = ZoneInfo(user_timezone)
    now = datetime.now(tz)
    return (
        f"\n## Contexto Atual\n"
        f"- Usuário: {user_name}\n"
        f"- Data/hora atual: {now.strftime('%A, %d de %B de %Y, %H:%M')} ({user_timezone})\n"
        f"- Timezone do usuário: {user_timezone}\n"
    )


class Orchestrator:
    """LangChain orchestrator for scheduling operations.

    Uses tool-calling to convert natural language into structured
    scheduling actions via SchedulingService.
    """

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self.model_name = model_name or os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

        if not self.api_key:
            logger.error("OPENAI_API_KEY is not configured")

        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.3,
            max_retries=2,
            request_timeout=30,
        )

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(SCHEDULING_TOOLS)

        self.system_prompt = _load_system_prompt()
        logger.info("Orchestrator initialized with model: %s", self.model_name)

    def process_message(
        self,
        user_message: str,
        user_name: str,
        user_timezone: str = "America/Sao_Paulo",
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Process a user message through the LangChain agent.

        Args:
            user_message: The user's natural language input.
            user_name: Display name for context.
            user_timezone: User's timezone for date interpretation.
            conversation_history: Previous messages [{role, content}, ...].

        Returns:
            The AI's response text.
        """
        try:
            # Build system message with dynamic context
            context_header = _get_context_header(user_name, user_timezone)
            full_system = self.system_prompt + context_header

            # Build message history
            messages = [SystemMessage(content=full_system)]

            if conversation_history:
                for msg in conversation_history[-10:]:  # Keep last 10 messages
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_message))

            # Limit iterations to avoid infinite loops
            max_iterations = 5
            for i in range(max_iterations):
                # Invoke the LLM with tools
                response = self.llm_with_tools.invoke(messages)
                
                # Check for tool calls
                if not response.tool_calls:
                    # No tool calls — return the direct text response
                    return response.content if response.content else "Comando processado com sucesso!"

                # Execute tool calls
                tool_map = {t.name: t for t in SCHEDULING_TOOLS}
                messages.append(response)
                
                from langchain_core.messages import ToolMessage
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    if tool_name in tool_map:
                        logger.info("Executing tool: %s with args: %s", tool_name, tool_args)
                        try:
                            result = tool_map[tool_name].invoke(tool_args)
                        except Exception as e:
                            logger.error("Tool %s failed: %s", tool_name, str(e))
                            result = f"❌ Erro ao executar a ação: {str(e)}"
                    else:
                        logger.warning("Unknown tool called: %s", tool_name)
                        result = "❌ Ferramenta não reconhecida."
                    
                    messages.append(
                        ToolMessage(
                            content=result,
                            tool_call_id=tool_call["id"],
                        )
                    )
            
            # If we reached max iterations
            return "A operação está demorando muitas etapas. Poderia ser mais específico?"

        except Exception as e:
            logger.error("Orchestrator error: %s", str(e), exc_info=True)
            return (
                "Desculpe, ocorreu um erro ao processar sua mensagem. "
                "Por favor, tente novamente."
            )


# Singleton-like instance (created per app context)
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Get or create the Orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
