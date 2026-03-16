/**
 * CalendAI PRO — Calendar page interactivity
 * Initializes FullCalendar and handles view toggling.
 */

document.addEventListener('DOMContentLoaded', () => {
    const calendarEl = document.getElementById('fullcalendar');
    const calendarView = document.getElementById('calendar-view');
    const listView = document.getElementById('list-view');
    const btnCalendar = document.getElementById('btn-calendar-view');
    const btnList = document.getElementById('btn-list-view');
    const eventsList = document.getElementById('events-list');
    const btnResync = document.getElementById('btn-resync');

    let calendar = null;

    // ── Initialize FullCalendar ───────────────────────────
    if (calendarEl) {
        calendar = new FullCalendar.Calendar(calendarEl, {
            locale: 'pt-br',
            initialView: 'dayGridMonth',
            headerToolbar: window.innerWidth < 768 ? {
                left: 'prev,next',
                center: 'title',
                right: 'dayGridMonth,listWeek'
            } : {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay',
            },
            height: 'auto',
            events: '/agenda/events',
            eventColor: '#6c63ff',
            eventDisplay: 'block',
            dayMaxEvents: 3,
            nowIndicator: true,
            editable: false,
            selectable: false,
        });
        calendar.render();
    }

    // ── View toggle ──────────────────────────────────────
    if (btnCalendar && btnList) {
        btnCalendar.addEventListener('click', () => {
            calendarView.classList.remove('hidden');
            listView.classList.add('hidden');
            btnCalendar.classList.add('active');
            btnList.classList.remove('active');
            if (calendar) calendar.updateSize();
        });

        btnList.addEventListener('click', () => {
            calendarView.classList.add('hidden');
            listView.classList.remove('hidden');
            btnList.classList.add('active');
            btnCalendar.classList.remove('active');
            loadEventsList();
        });
    }

    // ── Load events list ─────────────────────────────────
    async function loadEventsList() {
        if (!eventsList) return;

        try {
            const response = await fetch('/agenda/events');
            const events = await response.json();

            if (!events.length) {
                eventsList.innerHTML = '<p class="events-list-empty">Nenhum evento agendado.</p>';
                return;
            }

            // Sort by start date
            events.sort((a, b) => new Date(a.start) - new Date(b.start));

            eventsList.innerHTML = events.map(event => {
                const start = new Date(event.start);
                const end = event.end ? new Date(event.end) : null;
                const day = start.getDate();
                const month = start.toLocaleDateString('pt-BR', { month: 'short' });
                const timeStr = start.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                const endTimeStr = end ? ` - ${end.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}` : '';

                const syncBadge = event.extendedProps?.syncStatus
                    ? `<span class="sync-badge sync-badge-${event.extendedProps.syncStatus}">${event.extendedProps.syncStatus}</span>`
                    : '';

                return `
                    <div class="event-card">
                        <div class="event-date-badge">
                            <span class="day">${day}</span>
                            <span class="month">${month}</span>
                        </div>
                        <div class="event-info">
                            <div class="event-title">${escapeHtml(event.title)} ${syncBadge}</div>
                            <div class="event-time">🕐 ${timeStr}${endTimeStr}</div>
                            ${event.extendedProps?.description ? `<div class="event-description">${escapeHtml(event.extendedProps.description)}</div>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } catch (err) {
            eventsList.innerHTML = '<p class="events-list-empty">Erro ao carregar eventos.</p>';
        }
    }

    // ── Resync button ────────────────────────────────────
    if (btnResync) {
        btnResync.addEventListener('click', async () => {
            btnResync.classList.add('syncing');
            btnResync.disabled = true;

            try {
                const response = await fetch('/agenda/sync', { method: 'POST' });
                const data = await response.json();

                if (data.success) {
                    // Refresh calendar
                    if (calendar) calendar.refetchEvents();
                    loadEventsList();
                }
            } catch (err) {
                console.error('Sync error:', err);
            } finally {
                btnResync.classList.remove('syncing');
                btnResync.disabled = false;
            }
        });
    }

    // ── Helpers ──────────────────────────────────────────
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
