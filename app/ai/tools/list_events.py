"""LangChain tool — List Events."""

import logging

from langchain_core.tools import tool

from app.ai.schemas import ListEventsInput, EventOutput
from app.services.scheduling_service import SchedulingService, SchedulingError

logger = logging.getLogger(__name__)


@tool(args_schema=ListEventsInput)
def list_events_tool(
    start_date: str | None = None,
    end_date: str | None = None,
    keyword: str | None = None,
) -> str:
    """Lista os eventos da agenda do usuário.

    Use esta ferramenta quando o usuário quiser ver, listar, consultar
    ou verificar seus compromissos, reuniões ou eventos.
    Pode filtrar por período de datas ou por palavra-chave.
    """
    from flask_login import current_user

    try:
        # Parse date filters
        start_dt = None
        end_dt = None
        user_tz = current_user.timezone or "America/Sao_Paulo"

        if start_date:
            start_dt = SchedulingService.parse_datetime_safe(start_date, user_tz)
        if end_date:
            end_dt = SchedulingService.parse_datetime_safe(end_date, user_tz)

        events = SchedulingService.list_events(
            user_id=current_user.id,
            start=start_dt,
            end=end_dt,
            keyword=keyword,
        )

        if not events:
            if keyword:
                return f"📋 Nenhum evento encontrado com '{keyword}'."
            return "📋 Nenhum evento encontrado no período solicitado."

        lines = [f"📋 **{len(events)} evento(s) encontrado(s):**\n"]
        for event in events:
            start_str = event.start_datetime.strftime("%d/%m/%Y às %H:%M")
            end_str = event.end_datetime.strftime("%H:%M")
            desc = f" — {event.description}" if event.description else ""
            lines.append(
                f"- 📅 **{event.title}** | {start_str}–{end_str}{desc}\n"
                f"  ID: `{event.id}`"
            )

        return "\n".join(lines)

    except SchedulingError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error("Error listing events: %s", str(e), exc_info=True)
        return "❌ Ocorreu um erro ao listar os eventos. Tente novamente."
