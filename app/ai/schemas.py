"""Pydantic schemas for AI tool inputs/outputs — typed validation layer."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateEventInput(BaseModel):
    """Input schema for creating an event."""

    title: str = Field(..., description="Título do evento")
    start_datetime: str = Field(
        ...,
        description=(
            "Data e hora de início no formato ISO 8601 (ex: 2026-03-15T14:00:00). "
            "Se o usuário disser 'amanhã às 14h', converta para data ISO completa."
        ),
    )
    end_datetime: str | None = Field(
        None,
        description="Data e hora de término no formato ISO 8601. Se não informado, será 1 hora após o início.",
    )
    description: str | None = Field(
        None,
        description="Descrição ou notas opcionais para o evento",
    )
    timezone: str = Field(
        default="America/Sao_Paulo",
        description="Timezone do evento (ex: America/Sao_Paulo)",
    )


class ListEventsInput(BaseModel):
    """Input schema for listing events."""

    start_date: str | None = Field(
        None,
        description="Data de início do filtro no formato ISO 8601 (ex: 2026-03-15T00:00:00)",
    )
    end_date: str | None = Field(
        None,
        description="Data de fim do filtro no formato ISO 8601 (ex: 2026-03-31T23:59:59)",
    )
    keyword: str | None = Field(
        None,
        description="Palavra-chave para filtrar eventos por título ou descrição",
    )


class UpdateEventInput(BaseModel):
    """Input schema for updating an event."""

    event_id: str = Field(..., description="ID do evento a ser atualizado (UUID)")
    title: str | None = Field(None, description="Novo título do evento")
    start_datetime: str | None = Field(
        None, description="Nova data/hora de início no formato ISO 8601"
    )
    end_datetime: str | None = Field(
        None, description="Nova data/hora de término no formato ISO 8601"
    )
    description: str | None = Field(None, description="Nova descrição do evento")
    timezone: str | None = Field(None, description="Novo timezone do evento")


class CancelEventInput(BaseModel):
    """Input schema for cancelling an event."""

    event_id: str = Field(..., description="ID do evento a ser cancelado (UUID)")


class EventOutput(BaseModel):
    """Output schema for event data returned to the LLM."""

    id: str
    title: str
    start_datetime: str
    end_datetime: str
    timezone: str
    status: str
    description: str | None = None

    @classmethod
    def from_event(cls, event) -> "EventOutput":
        """Create from an Event model instance."""
        return cls(
            id=event.id,
            title=event.title,
            start_datetime=event.start_datetime.isoformat() if event.start_datetime else "",
            end_datetime=event.end_datetime.isoformat() if event.end_datetime else "",
            timezone=event.timezone,
            status=event.status,
            description=event.description,
        )
