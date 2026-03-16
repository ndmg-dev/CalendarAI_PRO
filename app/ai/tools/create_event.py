"""LangChain tool — Create Event."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.ai.schemas import CreateEventInput, EventOutput
from app.services.scheduling_service import SchedulingService, SchedulingError

logger = logging.getLogger(__name__)


@tool(args_schema=CreateEventInput)
def create_event_tool(
    title: str,
    start_datetime: str,
    end_datetime: str | None = None,
    description: str | None = None,
    timezone: str = "America/Sao_Paulo",
) -> str:
    """Cria um NOVO evento na agenda do usuário.

    ATENÇÃO: NÃO use esta ferramenta se o usuário quiser alterar, remarcar ou modificar
    um evento já existente. Nesses casos, use `atualizar_evento`.
    """
    from flask_login import current_user

    try:
        tz = ZoneInfo(timezone)

        # Parse start datetime
        start_dt = SchedulingService.parse_datetime_safe(start_datetime, timezone)

        # Parse end datetime
        end_dt = None
        if end_datetime:
            end_dt = SchedulingService.parse_datetime_safe(end_datetime, timezone)

        event = SchedulingService.create_event(
            user_id=current_user.id,
            title=title,
            start_datetime=start_dt,
            end_datetime=end_dt,
            timezone=timezone,
            description=description,
        )

        output = EventOutput.from_event(event)
        return (
            f"✅ Evento criado com sucesso!\n"
            f"📅 **{output.title}**\n"
            f"🕐 Início: {start_dt.strftime('%d/%m/%Y às %H:%M')}\n"
            f"🕐 Término: {event.end_datetime.strftime('%d/%m/%Y às %H:%M')}\n"
            f"📝 ID: {output.id}"
        )

    except SchedulingError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error("Error creating event: %s", str(e), exc_info=True)
        return "❌ Ocorreu um erro ao criar o evento. Tente novamente."
