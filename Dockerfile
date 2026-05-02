# Imagem base leve
FROM python:3.12-slim

# Evita criação de arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Logs sem buffer (importante para Docker)
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema (psycopg2 precisa disso)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas dependências primeiro (cache otimizado)
COPY pyproject.toml ./

# Instala dependências
RUN pip install --upgrade pip && pip install .

# Copia o restante do código
COPY . .

# Define PYTHONPATH (importante por causa do src/)
ENV PYTHONPATH=/app/src

# Comando de execução
CMD ["python", "-m", "amazon_deals_bot.main"]