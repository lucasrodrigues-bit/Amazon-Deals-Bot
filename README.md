# 🤖 Amazon Deals Bot

Bot Python que monitora promoções de grandes marketplaces brasileiros, filtra as melhores ofertas e envia mensagens geradas por IA automaticamente para um grupo no WhatsApp.

---

## Como funciona

A cada 30 minutos o bot executa o seguinte ciclo:

1. **Busca** promoções via RSS de um agregador público
2. **Filtra** por categorias configuradas e desconto mínimo
3. **Deduplica** — nunca envia a mesma promoção duas vezes
4. **Gera** uma mensagem de venda em português com IA
5. **Envia** para o grupo WhatsApp configurado
6. **Registra** o envio no banco de dados

```
Scheduler (30 min)
     │
     ▼
Busca RSS ──► Filtra categorias ──► Desconto ≥ 20%?
                                          │
                                    NÃO ──► Descarta
                                          │
                                    SIM ──► Já enviado?
                                                │
                                          SIM ──► Pula
                                                │
                                          NÃO ──► Gera mensagem (IA)
                                                       │
                                                       ▼
                                                Envia WhatsApp
                                                       │
                                                       ▼
                                                Salva no banco
```

---

## Categorias monitoradas

- 🏠 Casa e Eletrodomésticos
- 👗 Moda e Vestuário
- 📚 Livros
- 🏋️ Esportes e Fitness

---

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Scheduler | APScheduler |
| Banco de dados | PostgreSQL (Supabase) |
| IA | GPT-4o mini |
| Mensageria | WhatsApp via API |
| Hospedagem | Railway |
| CI/CD | GitHub Actions |

---

## Arquitetura

O projeto segue **Clean Architecture** com separação clara entre camadas:

```
amazon-deals-bot/
├── domain/              # Entidades e interfaces (sem dependências externas)
│   ├── entities/
│   │   └── deal.py      # Entidade Deal + enum Category
│   └── interfaces/
│       └── __init__.py  # IDealsFetcher, IDealRepository, IMessageGenerator, INotifier
├── use_cases/
│   └── process_deals.py # Lógica de negócio central
├── adapters/            # Implementações concretas das interfaces
│   ├── pelando_fetcher.py
│   ├── supabase_repository.py
│   ├── openai_generator.py
│   └── zapi_notifier.py
├── infrastructure/      # Config, scheduler, injeção de dependências
│   ├── config.py
│   ├── container.py
│   └── scheduler.py
├── tests/
│   ├── unit/            # Testes sem dependências externas
│   └── integration/     # Testes contra serviços reais (CI only)
└── scripts/
    └── health_check.py  # Smoke test pós-deploy
```

**Regra de dependência:**
```
infrastructure → adapters → use_cases → domain
```

Nenhuma camada interna conhece os detalhes das camadas externas. O `ProcessDealsUseCase` só depende de interfaces abstratas — nunca de implementações concretas.

---

## Pré-requisitos

- Python 3.12+
- Conta no [Supabase](https://supabase.com) (plano gratuito)
- Chave de API da [OpenAI](https://platform.openai.com)
- Conta na API de mensageria WhatsApp escolhida
- Conta no [Railway](https://railway.app)

---

## Configuração local

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/amazon-deals-bot.git
cd amazon-deals-bot
```

### 2. Instale as dependências

```bash
pip install ".[dev]"
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env` com seus dados. Consulte `.env.example` para ver quais variáveis são necessárias.

### 4. Execute localmente

```bash
python -m infrastructure.scheduler
```

O bot roda imediatamente ao iniciar e depois repete no intervalo configurado.

---

## Variáveis de ambiente

Todas as variáveis estão documentadas em `.env.example`. As principais são:

| Variável | Descrição | Padrão |
|---|---|---|
| `SUPABASE_DB_URL` | Connection string do PostgreSQL | — |
| `OPENAI_API_KEY` | Chave da API OpenAI | — |
| `MIN_DISCOUNT_PCT` | Desconto mínimo para aprovação | `20` |
| `SCHEDULE_INTERVAL_MINUTES` | Intervalo entre execuções | `30` |
| `OPENAI_MODEL` | Modelo da OpenAI utilizado | `gpt-4o-mini` |

> ⚠️ Nunca commite o arquivo `.env`. Ele já está no `.gitignore`.

---

## Testes

### Unitários (sem dependências externas)

```bash
python -m pytest tests/unit/ -v
```

### Com cobertura

```bash
python -m pytest tests/unit/ --cov=. --cov-report=term-missing
```

### Integração (requer credenciais reais)

```bash
python -m pytest -m integration -v
```

Os testes de integração requerem variáveis de ambiente preenchidas e são executados apenas no CI (branch `main`).

### Resultado esperado

```
30 passed in 1.26s
```

---

## Deploy no Railway

### 1. Crie um novo projeto no Railway

Conecte ao repositório GitHub. O Railway detecta o `Dockerfile` automaticamente.

### 2. Configure as variáveis de ambiente

No painel do Railway, adicione todas as variáveis listadas em `.env.example`.

### 3. Deploy

```bash
git push origin main
```

O Railway faz o build, executa o `health_check.py` e sobe o serviço. Em caso de falha, reverte automaticamente para a versão anterior.

### railway.toml

```toml
[build]
builder = "dockerfile"

[deploy]
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

---

## CI/CD

O GitHub Actions executa dois jobs:

| Job | Quando roda | O que faz |
|---|---|---|
| `unit-tests` | Todo PR e push | Roda `pytest -m "not integration"` |
| `integration-tests` | Push em `main` | Roda `pytest -m integration` com secrets |

Configure os secrets no repositório GitHub antes do primeiro deploy em produção.

---

## Banco de dados

O schema é criado automaticamente na primeira execução:

```sql
CREATE TABLE IF NOT EXISTS deals_sent (
    id           TEXT PRIMARY KEY,
    title        TEXT        NOT NULL,
    category     TEXT        NOT NULL,
    store        TEXT        NOT NULL,
    price        NUMERIC(10,2),
    discount_pct INTEGER,
    url          TEXT,
    sent_at      TIMESTAMPTZ DEFAULT NOW()
);
```

O campo `id` é um hash do URL da promoção — garante idempotência nas inserções.

---

## Como estender

### Adicionar nova categoria

1. Adicione o valor no enum `Category` em `domain/entities/deal.py`
2. Adicione as keywords em `CATEGORY_KEYWORDS` em `adapters/pelando_fetcher.py`
3. Adicione testes em `tests/unit/test_pelando_fetcher.py`

### Adicionar nova fonte de promoções

1. Crie `adapters/nova_fonte_fetcher.py` implementando `IDealsFetcher`
2. Crie um `CompositeFetcher` em `adapters/` que agrega múltiplos fetchers
3. Atualize `infrastructure/container.py`

O `ProcessDealsUseCase` não precisa de nenhuma alteração.

### Adicionar segundo grupo de WhatsApp

1. Crie `adapters/composite_notifier.py` implementando `INotifier`
2. Delegue para múltiplas instâncias de notifier internamente
3. Atualize `infrastructure/container.py`

---

## Custo estimado

| Serviço | Plano | Custo mensal |
|---|---|---|
| Hospedagem (Railway) | Hobby | R$15–20 |
| Banco de dados (Supabase) | Free tier | Grátis |
| Geração de texto (OpenAI) | Pay-as-you-go | R$5–10 |
| API WhatsApp | Plano básico | R$49 |
| **Total** | | **~R$69–79** |

---

## Licença

MIT

---

## Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/minha-feature`
3. Garanta que os testes passam: `python -m pytest tests/unit/`
4. Abra um Pull Request
