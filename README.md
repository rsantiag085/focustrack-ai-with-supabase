# FocusTrack AI

Aplicação web para registro e análise de sessões de foco. O usuário registra suas atividades do dia com categoria, descrição, horário e nível de foco, visualiza métricas consolidadas e solicita um feedback de produtividade gerado pelo **Jarbis** — um mentor de IA alimentado pelo Google Gemini.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | HTML + CSS + JavaScript (Vanilla) |
| Servidor de frontend | Nginx (via Docker) |
| Autenticação | Supabase Auth (JWT RS256) |
| Backend | FastAPI (Python) |
| Banco de dados | PostgreSQL via Supabase Cloud |
| ORM | SQLAlchemy |
| IA | Google Gemini 2.5 Flash (`google-genai`) |
| Infraestrutura | Docker Compose / Terraform |

## Arquitetura

```
Browser
  │
  ├─── Supabase Auth ──────────────────────────────► Supabase Cloud
  │        (login / signup / JWT)
  │
  └─── Nginx (porta 8080) ── serve ──► frontend/
           │
           └─── apiFetch (Bearer JWT) ──► FastAPI (porta 8000)
                                               │
                                         valida JWT (RS256)
                                               │
                                    ┌──────────┴──────────┐
                                    │                     │
                              Supabase DB           Google Gemini
                           (atividades,             (análise diária
                           daily_reports)            via "Jarbis")
```

O backend valida o JWT emitido pelo Supabase usando a chave pública RS256 antes de qualquer operação. Cada registro no banco é isolado por `user_id`, garantindo que um usuário nunca acesse dados de outro.

## Pré-requisitos

- Docker e Docker Compose
- Conta no [Supabase](https://supabase.com) com um projeto criado
- Chave de API do [Google AI Studio](https://aistudio.google.com)

## Configuração

Crie o arquivo `.env` na raiz do projeto com as variáveis abaixo:

```env
# Supabase — conexão direta com o banco (Settings > Database > Connection String)
DATABASE_URL=postgresql://postgres.[ref]:[senha]@aws-0-[região].pooler.supabase.com:5432/postgres

# Supabase — chave pública JWT para validação RS256 (Settings > API > JWT Settings)
SUPABASE_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w...
-----END PUBLIC KEY-----"

# Google Gemini
GOOGLE_API_KEY=AIza...
```

> O arquivo `.env` está no `.gitignore` e nunca deve ser commitado.

### Tabelas no Supabase

Execute no SQL Editor do Supabase para criar as tabelas:

```sql
CREATE TABLE atividades (
    id         SERIAL PRIMARY KEY,
    user_id    UUID NOT NULL,
    categoria  TEXT,
    descricao  TEXT,
    data       DATE,
    inicio     TIMESTAMP,
    fim        TIMESTAMP,
    nivel_foco INTEGER
);

CREATE TABLE daily_reports (
    id        SERIAL PRIMARY KEY,
    user_id   UUID NOT NULL,
    data      DATE,
    resumo_ia TEXT
);
```

## Como rodar

### Com Docker Compose (recomendado)

```bash
docker compose up --build
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:8080 |
| Backend (API) | http://localhost:8000 |
| Docs da API | http://localhost:8000/docs |

### Desenvolvimento local (sem Docker)

**Backend:**
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**

Abra `frontend/index.html` diretamente no navegador ou sirva com qualquer servidor estático (ex: extensão Live Server do VS Code).

> Em desenvolvimento local, o frontend se comunica com o backend em `http://localhost:8000`. Esta URL está definida na constante `BACKEND_URL` em `frontend/app.js`.

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/atividade` | Lista atividades do usuário autenticado |
| `POST` | `/api/atividade` | Registra uma nova atividade |
| `DELETE` | `/api/atividade/{id}` | Remove uma atividade (verifica ownership) |
| `POST` | `/api/analisar?target_date=YYYY-MM-DD` | Gera análise diária com Gemini e persiste o relatório |

Todos os endpoints exigem o header `Authorization: Bearer <token>` com o JWT do Supabase.

## Estrutura do projeto

```
focustrack-ia-with-supabase/
├── backend/
│   ├── auth.py         # Validação do JWT Supabase (RS256)
│   ├── database.py     # Conexão SQLAlchemy com Supabase
│   ├── main.py         # Rotas FastAPI e integração Gemini
│   └── models.py       # Modelos ORM (Atividade, DailyReport)
├── frontend/
│   ├── index.html      # UI completa (auth, dashboard, timeline, formulário)
│   └── app.js          # Cliente Supabase, auth handlers e wrappers de API
├── terraform/          # Infraestrutura como código (provisionamento cloud)
├── docker-compose.yml  # Orquestração backend (FastAPI) + frontend (Nginx)
├── Dockerfile          # Imagem do backend Python
├── requirements.txt    # Dependências Python
├── CHANGELOG.md        # Histórico de alterações por versão
└── .env                # Variáveis de ambiente (não commitado)
```

## Variáveis de ambiente — referência completa

| Variável | Onde obter |
|---|---|
| `DATABASE_URL` | Supabase → Settings → Database → Connection String (modo `Session`) |
| `SUPABASE_JWT_PUBLIC_KEY` | Supabase → Settings → API → JWT Settings → JWT Public Key |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) → Get API Key |

## Versões

Consulte o [CHANGELOG.md](./CHANGELOG.md) para o histórico detalhado de alterações.
