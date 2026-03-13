# CalendAI PRO

Aplicacao web de agendamentos inteligentes com IA, construida com Python, Flask, LangChain, Supabase e sincronizacao com Google Calendar.

## Stack Tecnologica

| Camada | Tecnologia |
|---|---|
| Web / UI | Flask + Jinja2 + Javascript |
| IA | LangChain (tool-calling) + OpenAI |
| Banco de dados | Supabase PostgreSQL (via SQLAlchemy + Alembic) |
| Autenticacao | Google OAuth (Authlib + Flask-Login) |
| Sync externo | Google Calendar API |
| Deploy | Docker + Docker Compose |

## Pre-requisitos

- Python 3.11+
- Docker e Docker Compose
- Projeto no Google Cloud Console com OAuth configurado
- Projeto no Supabase (tier gratuito)
- Chave da API OpenAI
- Chave da API Brevo (para disparos de e-mail)

## Setup Local

### 1. Clonar o repositorio
```bash
git clone https://github.com/ndmg-dev/CalendarAI_PRO.git
cd CalendarAI_PRO
```

### 2. Configurar variaveis de ambiente
```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

### 3. Setup com Docker
```bash
docker compose up --build
```
A aplicacao estara disponivel em `http://localhost:5000`.

### 4. Setup sem Docker
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -e ".[dev]"
alembic upgrade head
python wsgi.py
```

## Configuracao do Google OAuth

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto ou selecione um existente
3. Navegue ate APIs & Services > Credentials
4. Crie um OAuth 2.0 Client ID (tipo: Web Application)
5. Adicione o redirect URI correspondente ao seu ambiente (ex: http://localhost:5000/auth/callback)
6. Copie o Client ID e Client Secret para o arquivo .env
7. Em OAuth consent screen, adicione os escopos necessarios:
   - openid
   - email
   - profile
   - https://www.googleapis.com/auth/calendar (para sincronizacao)

## Testes

```bash
pip install -e ".[dev]"
pytest
```

## Estrutura do Projeto

```
CalendAI_PRO/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuracoes por ambiente
│   ├── extensions.py        # Extensoes Flask
│   ├── blueprints/          # Blueprints (auth, chat, agenda)
│   ├── models/              # Modelos SQLAlchemy
│   ├── services/            # Logica de negocio
│   ├── ai/                  # Orquestrador LangChain
│   ├── repositories/        # Camada de acesso a dados
│   ├── templates/           # Templates Jinja2
│   └── static/              # Ativos estaticos (CSS, JS)
├── prompts/                 # Prompts de sistema
├── migrations/              # Migracoes Alembic
├── tests/                   # Testes automatizados
├── docker/                  # Arquivos de suporte Docker
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Licenca

Este projeto esta licenciado sob a Licenca MIT - consulte o arquivo [LICENSE](LICENSE) para obter detalhes.
