"""Chat routes — AI chat interface and message API."""

import logging

from flask import render_template, request, jsonify, session, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from datetime import datetime
from sqlalchemy import func

from app.blueprints.chat import chat_bp
from app.ai.orchestrator import get_orchestrator
from app.models.chat_message import ChatMessage
from app.extensions import db

logger = logging.getLogger(__name__)


@chat_bp.route("/")
@login_required
def index():
    """Render chat page with today's message history."""
    # Get messages from today for the current user
    today = datetime.now().date()
    messages = (
        ChatMessage.query.filter(
            ChatMessage.user_id == current_user.id,
            func.date(ChatMessage.created_at) == today
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    
    return render_template("chat/chat.html", initial_messages=messages)


@chat_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    """Process a chat message through the AI orchestrator.

    Expects JSON: {"message": "user text"}
    Returns JSON: {"reply": "AI response"} or {"error": "..."}
    """
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Mensagem vazia"}), 400

    user_message = data["message"].strip()
    logger.info("Chat message from %s: %s", current_user.email, user_message[:100])

    try:
        # Load conversation history for the orchestrator (last 20 messages for context)
        history = (
            ChatMessage.query.filter(ChatMessage.user_id == current_user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
            .all()
        )
        # Reverse to get chronological order for the orchestrator
        history_list = [m.to_dict() for m in reversed(history)]

        orchestrator = get_orchestrator()
        reply = orchestrator.process_message(
            user_message=user_message,
            user_name=current_user.display_name or current_user.email,
            user_timezone=current_user.timezone or "America/Sao_Paulo",
            conversation_history=history_list,
        )

        # Save both messages to database
        user_msg = ChatMessage(user_id=current_user.id, role="user", content=user_message)
        ai_msg = ChatMessage(user_id=current_user.id, role="assistant", content=reply)
        db.session.add(user_msg)
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({"reply": reply})

    except Exception as e:
        logger.error("Chat error: %s", str(e), exc_info=True)
        return jsonify({
            "error": "Ocorreu um erro ao processar sua mensagem.",
            "reply": "❌ Desculpe, ocorreu um erro interno. Tente novamente.",
        }), 500


@chat_bp.route("/audio", methods=["POST"])
@login_required
def process_audio():
    """Receive audio file, transcribe with Whisper, and process with orchestrator."""
    if "audio" not in request.files:
        return jsonify({"error": "Nenhum arquivo de áudio enviado"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "Arquivo inválido"}), 400

    import tempfile
    import os
    from openai import OpenAI

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # 1. Transcribe with Whisper
        client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        user_message = transcription.strip()
        if not user_message:
            return jsonify({"error": "Não foi possível transcrever o áudio."}), 400

        logger.info("Audio transcribed for %s: %s", current_user.email, user_message)

        # 2. Process with orchestrator
        # Load conversation history for context
        history = (
            ChatMessage.query.filter(ChatMessage.user_id == current_user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
            .all()
        )
        history_list = [m.to_dict() for m in reversed(history)]

        orchestrator = get_orchestrator()
        reply = orchestrator.process_message(
            user_message=user_message,
            user_name=current_user.display_name or current_user.email,
            user_timezone=current_user.timezone or "America/Sao_Paulo",
            conversation_history=history_list,
        )

        # Save both messages to database
        user_msg = ChatMessage(user_id=current_user.id, role="user", content=f"🎤 (Áudio): {user_message}")
        ai_msg = ChatMessage(user_id=current_user.id, role="assistant", content=reply)
        db.session.add(user_msg)
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({"reply": reply, "transcription": user_message})

    except Exception as e:
        logger.error("Audio processing error: %s", str(e), exc_info=True)
        return jsonify({
            "error": "Erro ao processar áudio.",
            "reply": "❌ Não consegui entender seu áudio. Tente falar mais claro ou digite sua mensagem."
        }), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@chat_bp.route("/history", methods=["GET"])
@login_required
def get_history_days():
    """Get list of days that have chat messages, formatted for the sidebar."""
    from sqlalchemy import func
    
    # Group messages by date
    days = (
        db.session.query(func.date(ChatMessage.created_at))
        .filter(ChatMessage.user_id == current_user.id)
        .group_by(func.date(ChatMessage.created_at))
        .order_by(func.date(ChatMessage.created_at).desc())
        .all()
    )
    
    # Format dates as strings
    result = []
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    for (day,) in days:
        if day == today:
            label = "Hoje"
        elif day == yesterday:
            label = "Ontem"
        else:
            label = day.strftime("%d/%m/%Y")
            
        result.append({
            "date": day.isoformat(),
            "label": label
        })
        
    return jsonify(result)


@chat_bp.route("/history/<date_str>", methods=["GET"])
@login_required
def get_history_messages(date_str):
    """Get all messages for a specific date."""
    try:
        # Validate date format
        target_date = datetime.fromisoformat(date_str).date()
        
        messages = (
            ChatMessage.query.filter(
                ChatMessage.user_id == current_user.id,
                func.date(ChatMessage.created_at) == target_date
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        
        return jsonify([m.to_dict() for m in messages])
    except ValueError:
        return jsonify({"error": "Formato de data inválido"}), 400
    except Exception as e:
        logger.error("Error fetching history: %s", str(e))
        return jsonify({"error": "Erro ao carregar histórico"}), 500
