# 🤖 Deals Bot (Multi-Marketplace)

Sistema automatizado para coleta, processamento e distribuição de promoções de múltiplos marketplaces (Amazon, Shopee, Magalu), com geração de copy via IA e envio automatizado.

---

## 📌 Visão Geral

O **Deals Bot** é um sistema backend em **Python (async)** que:

- Coleta ofertas de APIs externas
- Remove duplicatas automaticamente
- Gera copy persuasiva com IA
- Envia mensagens para WhatsApp e Telegram
- Controla status e retries
- Roda de forma contínua via scheduler

---

## ⚙️ Pipeline da Aplicação

Scheduler │ ├── Phase 1 (Coleta) │ ├── APIs (Amazon, Shopee, Magalu) │ ├── Normalização │ ├── Deduplicação (hash) │ └── Persistência (status: **PENDING**) │ ├── Phase 2 (Copy) │ ├── Geração de texto (IA) │ └── status → **READY** │ └── Phase 3 (Envio) ├── WhatsApp (Evolution **API**) ├── Telegram └── status → **SENT** / **FAILED**

---

## 🏗️ Stack Tecnológica

| Camada         | Tecnologia |
|----------------|----------|
| Backend        | Python 3.13 |
| ORM            | SQLAlchemy (async) |
| Banco          | PostgreSQL |
| Cache          | Redis |
| IA             | OpenAI |
| Mensageria     | Evolution API (WhatsApp) |
| Scheduler      | Async jobs |
| Container      | Docker |

---

## 🧩 Arquitetura

src/ └── amazon_deals_bot/ ├── config/ ├── db/ ├── models/ ├── repositories/ ├── services/ │ ├── collector.py │ ├── deduplicator.py │ ├── affiliate.py │ ├── copywriter.py │ ├── publisher.py ├── scheduler/ └── main.py

---

## 🗄️ Modelo de Dados (Deal)

```python Deal ├── id (hash) ├── name ├── price ├── original_price ├── discount_pct ├── url ├── affiliate_url ├── image_url ├── source ├── status (**PENDING** | **READY** | **SENT** | **FAILED**) ├── retry_count ├── created_at ├── updated_at ├── sent_at ├── copy 🐳 Rodando com Docker docker compose up -d --build ⚙️ Variáveis de Ambiente

Crie um .env baseado no .env.example

Principais:

DATABASE_URL= DATABASE_SYNC_URL= REDIS_URL=

OPENAI_API_KEY=

EVOLUTION_API_URL= EVOLUTION_API_KEY= EVOLUTION_INSTANCE_NAME= ▶️ Rodando Local (sem Docker) set **PYTHONPATH**=src python -m amazon_deals_bot.main 🔁 Scheduler Phase 1: coleta (15 min) Phase 2: envio (60s)

Configurável via .env

📤 Exemplo de Saída 🔥 **OFERTA** **IMPERD**Í**VEL**!

Notebook Dell i7

💰 De: R$**5000** 💸 Por: R$**3500**

🚨 Desconto: 30%

👉 [https://...](https://...) 🚀 Roadmap Integração real com APIs (Amazon / Shopee / Magalu) Integração real com OpenAI Envio real via WhatsApp (Evolution **API**) Rate limit inteligente Painel admin Métricas de conversão 🔐 Segurança .env nunca versionado Sem hardcode de credenciais Controle de rate limit (anti-ban) Separação de camadas (services / repo) 💰 Monetização Links de afiliado Distribuição automatizada em grupos Copy otimizada para conversão 📄 Licença

**MIT**
