"""Email service — Brevo API integration for notifications."""

import logging
import httpx
from flask import current_app

logger = logging.getLogger(__name__)

class EmailService:
    """Service to send emails via Brevo (formerly Sendinblue)."""

    @staticmethod
    def send_event_reminder(user_email, user_name, event_title, event_start_str):
        """Send a premium HTML reminder for an upcoming event."""
        api_key = current_app.config.get("BREVO_API_KEY")
        if not api_key:
            raise ValueError("BREVO_API_KEY não está configurada no ambiente.")

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": api_key
        }

        # ... (rest of the code remains same, but we will catch the exception)
        # Premium HTML Template matching app colors
        html_content = f"""
        <html>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0a1a; color: #ffffff;">
            <div style="max-width: 600px; margin: 40px auto; background: rgba(15, 15, 35, 0.8); border: 1px solid rgba(138, 43, 226, 0.3); border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #8a2be2;">CalendAI PRO</div>
                <div style="font-size: 18px; margin-bottom: 30px; color: #b0b0cc;">Olá, {user_name}! 👋</div>
                <div style="font-size: 20px; margin-bottom: 20px;">Seu compromisso está chegando:</div>
                <div style="background: rgba(138, 43, 226, 0.1); border-radius: 12px; padding: 20px; margin-bottom: 30px; border: 1px solid rgba(138, 43, 226, 0.2);">
                    <div style="font-size: 24px; font-weight: bold; color: #ffffff;">{event_title}</div>
                    <div style="font-size: 16px; color: #a0a0ff; margin-top: 10px;">📅 {event_start_str}</div>
                </div>
                <p style="color: #8888aa; font-size: 14px;">Este é um lembrete automático do seu assistente de agenda inteligente.</p>
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); color: #555577; font-size: 12px;">
                    &copy; 2026 CalendAI PRO. Todos os direitos reservados.
                </div>
            </div>
        </body>
        </html>
        """

        payload = {
            "sender": {"name": "CalendAI PRO", "email": "calendaipro@gmail.com"},
            "to": [{"email": user_email, "name": user_name}],
            "subject": f"Lembrete: {event_title}",
            "htmlContent": html_content
        }

        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        if response.status_code != 201:
            raise Exception(f"Erro na API do Brevo ({response.status_code}): {response.text}")
        
        logger.info("Email sent to %s for event '%s'", user_email, event_title)
        return True
