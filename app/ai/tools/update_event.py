"""LangChain tool — Update Event."""

import logging

from langchain_core.tools import tool

from app.ai.schemas import UpdateEventInput, EventOutput
from app.services.scheduling_service import SchedulingService, SchedulingError

logger = logging.getLogger(__name__)


@tool(args_schema=UpdateEventInput)
def update_event_tool(
    event_id: str,
    title: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    description: str | None = None,
    timezone: str | None = None,
) -> str:
    """Atualiza um evento existente na agenda do usuário.

    Use esta ferramenta quando o usuário quiser alterar, modificar, reagendar
    ou atualizar dados de um compromisso ou evento existente.
    O event_id deve ser obtido previamente pela ferramenta de listagem.
    """
    from flask_login import current_user

    try:
        user_tz = timezone or current_user.timezone or "America/Sao_Paulo"

        start_dt = None
        end_dt = None

        if start_datetime:
            start_dt = SchedulingService.parse_datetime_safe(start_datetime, user_tz)
        if end_datetime:
            end_dt = SchedulingService.parse_datetime_safe(end_datetime, user_tz)

        event = SchedulingService.update_event(
            user_id=current_user.id,
            event_id=event_id,
            title=title,
            description=description,
            start_datetime=start_dt,
            end_datetime=end_dt,
            timezone=timezone,
        )

        output = EventOutput.from_event(event)
        return (
            f"✅ Evento atualizado com sucesso!\n"
            f"📅 **{output.title}**\n"
            f"🕐 Início: {event.start_datetime.strftime('%d/%m/%Y às %H:%M')}\n"
            f"🕐 Término: {event.end_datetime.strftime('%d/%m/%Y às %H:%M')}"
        )

    except SchedulingError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error("Error updating event: %s", str(e), exc_info=True)
        return "❌ Ocorreu um erro ao atualizar o evento. Tente novamente."
