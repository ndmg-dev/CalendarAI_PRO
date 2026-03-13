"""LangChain tool — Cancel Event."""

import logging

from langchain_core.tools import tool

from app.ai.schemas import CancelEventInput
from app.services.scheduling_service import SchedulingService, SchedulingError

logger = logging.getLogger(__name__)


@tool(args_schema=CancelEventInput)
def cancel_event_tool(event_id: str) -> str:
    """Cancela um evento da agenda do usuário.

    Use esta ferramenta quando o usuário quiser cancelar, remover, deletar
    ou desmarcar um compromisso ou evento existente.
    O event_id deve ser obtido previamente pela ferramenta de listagem.
    """
    from flask_login import current_user

    try:
        event = SchedulingService.cancel_event(
            user_id=current_user.id,
            event_id=event_id,
        )

        return (
            f"✅ Evento cancelado com sucesso!\n"
            f"❌ **{event.title}** — "
            f"{event.start_datetime.strftime('%d/%m/%Y às %H:%M')}"
        )

    except SchedulingError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error("Error cancelling event: %s", str(e), exc_info=True)
        return "❌ Ocorreu um erro ao cancelar o evento. Tente novamente."
