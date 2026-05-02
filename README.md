# 🤖 Amazon Deals Bot

Sistema automatizado para coleta, processamento e distribuição de promoções de marketplaces, com monetização via links de afiliado e envio inteligente para grupos de WhatsApp.

---

## 📌 Visão Geral

O **Amazon Deals Bot** é um sistema backend desenvolvido em **Java + Spring Boot** que:

- Consome promoções diretamente de APIs de marketplaces
- Gera links de afiliado automaticamente
- Evita duplicidade de envios
- Cria mensagens persuasivas com IA
- Envia ofertas automaticamente para grupos de WhatsApp
- Armazena e rastreia todas as promoções no banco

---

## ⚙️ Como funciona

## A aplicação executa um ciclo automatizado:

```
Scheduler
│
▼
Consumo de APIs (Amazon, Shopee, Magalu)
│
▼
Normalização dos dados
│
▼
Geração de link de afiliado
│
▼
Validação (duplicidade / preço / status)
│
├── Já existe → DESCARTA
│
▼
Persistência no banco (MySQL)
│
▼
Geração de copy com IA
│
▼
Montagem da mensagem
│
▼
Envio via WhatsApp (Evolution API)
│
▼
Atualização de status (ENVIADO)
```

---

## 🏗️ Stack Tecnológica

| Camada          | Tecnologia                                  |
| --------------- | ------------------------------------------- |
| Backend         | Java 17 + Spring Boot                       |
| Scheduler       | Spring Scheduler (`@Scheduled`)             |
| Banco de Dados  | MySQL                                       |
| Containerização | Docker                                      |
| Infraestrutura  | VPS                                         |
| IA              | API de geração de texto (OpenAI ou similar) |
| Mensageria      | Evolution API (WhatsApp)                    |

---

## 🧩 Arquitetura

O projeto segue uma arquitetura modular baseada em separação de responsabilidades:

```
amazon-deals-bot/
├── config/                          ← YAMLs do operador (categorias, grupos)
├── prompts/                         ← Templates de prompt da IA
├── src/
│   └── amazon_deals_bot/
│       ├── clients/                 ← Um arquivo por API externa (I/O puro)
│       ├── config/                  ← settings.py + loader.py
│       ├── db/                      ← session.py + redis.py
│       ├── models/                  ← deal.py + base.py (ORM)
│       ├── repositories/            ← deal_repository.py
│       ├── scheduler/               ← setup.py + jobs.py
│       ├── services/                ← collector, publisher, affiliate, dedup, copywriter
│       ├── utils/                   ← constants, logger, retry
│       └── main.py
├── migrations/
│   └── versions/
├── tests/
│   ├── unit/                        ← services/ · clients/ · utils/
│   └── integration/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

---

## 🗄️ Banco de Dados

## Tabela principal:

```sql
CREATE TABLE deals (
id BIGINT AUTO_INCREMENT PRIMARY KEY,
nome VARCHAR(255) NOT NULL,
preco DECIMAL(10,2),
preco_original DECIMAL(10,2),
link_afiliado TEXT,
imagem TEXT,
origem VARCHAR(50),
hash VARCHAR(255) UNIQUE,
status VARCHAR(50),
data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
data_envio TIMESTAMP
);
```

📌 O campo `hash` garante que a mesma promoção nunca seja enviada duas vezes.

---

## 🐳 Rodando com Docker

### docker-compose.yml

```yaml
version: '3.8'

## services:
## app:
build: .
## ports:
- "8080:8080"
## depends_on:
- mysql

## mysql:
image: mysql:8
## environment:
MYSQL_ROOT_PASSWORD: root
MYSQL_DATABASE: deals_db
## ports:
- "3306:3306"
```

---

## 🔐 Variáveis de Ambiente

```env
DB_HOST=localhost
## DB_PORT=3306
DB_NAME=deals_db
DB_USER=root
DB_PASSWORD=root

## API_AMAZON_KEY=***
## API_SHOPEE_KEY=***
## API_MAGALU_KEY=***

## AFFILIATE_ID=***

## OPENAI_API_KEY=***

## WHATSAPP_API_URL=***
## WHATSAPP_API_TOKEN=***
```

---

## ▶️ Execução Local

### 1. Clonar repositório

```bash
git clone [https://github.com/seu-usuario/amazon-deals-bot.git](https://github.com/seu-usuario/amazon-deals-bot.git)
cd amazon-deals-bot
```

### 2. Subir containers

```bash
docker-compose up -d
```

### 3. Rodar aplicação

```bash
./mvnw spring-boot:run
```

---

## 🚀 Deploy (VPS)

1. Subir código na VPS
2. Instalar Docker + Docker Compose
3. Rodar:

```bash
docker-compose up -d --build
```

4. Configurar variáveis de ambiente no servidor

---

## 📈 Melhorias Futuras

- Fila de processamento (RabbitMQ / Kafka)
- Cache com Redis
- Painel administrativo
- Métricas de conversão (cliques / vendas)
- Suporte a múltiplos grupos
- Rate limiting nas APIs

---

## 💰 Monetização

## O sistema utiliza:

- Links de afiliado por produto
- Distribuição em grupos com alto engajamento
- Copywriting automatizado com IA

---

## 📄 Licença

## MIT

---

## 🤝 Contribuição

1. Crie uma branch: `feature/nova-feature`
2. Commit: `git commit -m "feat: nova feature"`
3. Push: `git push origin feature/nova-feature`
4. Abra um Pull Request