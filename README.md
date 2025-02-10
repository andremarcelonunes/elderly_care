# Projeto Cuidar

Projeto que visa criar uma plataforma para conectar pessoas que precisam de cuidados com pessoas que podem oferecer cuidados.

## Índice

- [Sobre](#sobre)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Execução com Docker](#instalação-e-execução-com-docker)
- [Documentação da API](#documentação-da-api)
- [Considerações Finais](#considerações-finais)

---

## Sobre

Projeto desenvolvido por um grupo de amigos para ajudar a conectar pessoas que precisam de cuidados com aquelas que podem oferecê-los. A ideia é criar uma plataforma que facilite essa conexão, permitindo o cadastro, a avaliação e o histórico dos cuidados prestados.

## Funcionalidades Principais

- Cadastro de pessoas que **precisam de cuidados**.
- Cadastro de pessoas que **podem oferecer cuidados**.
- Conexão entre as pessoas que necessitam de cuidados e aquelas que podem oferecê-los.
- Avaliação dos prestadores de cuidados.
- Histórico de atendimentos e cuidados.
- Solicitações de ajuda.

## Tecnologias Utilizadas

- Python
- FastAPI
- PostgreSQL
- MongoDB

---

## Pré-requisitos

### Software Necessário

- **Python 3.12.8** (para execução local)
- **PostgreSQL** (recomendado na versão 17.2 ou conforme sua necessidade)
- **Docker Desktop**  
  - [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/)  
  - [Docker Desktop para Mac](https://www.docker.com/products/docker-desktop/)
- **Poetry** (gerenciador de dependências do Python)

### Dependências do Projeto

As dependências estão listadas no arquivo `pyproject.toml`. Algumas das principais são:

- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary
- pydantic-settings
- passlib
- bcrypt
- pydantic (com extra "email")

---

## Instalação e Execução com Docker

Utilize o Docker para obter um ambiente isolado e consistente.

### 1. Clone o Repositório

Abra o terminal (ou PowerShell, no Windows) e execute:

```bash
git clone https://seu-repositorio.git
cd nome-do-repositorio
```

### 2. Crie o Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis de ambiente:

```
POSTGRES_USER=elderydb
POSTGRES_PASSWORD=teste123
POSTGRES_DB=elderly_care
DB_HOST_PORT=15432
DATABASE_URL=postgresql://elderydb:teste123@db:5432/elderly_care
MONGO_URI=mongodb://localhost:27017
MONGO_DB=elderly_care
```

### 3. Execute o Docker Compose

O arquivo docker-compose.yml deve estar configurado para utilizar as variáveis do arquivo .env. Exemplo:

```yaml

version: '3.8'

services:
  db:
    image: postgres:14-alpine
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${DB_HOST_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  web:
    build:
      context: .
      dockerfile: backendeldery/Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: ${DATABASE_URL}
      MONGO_URI: ${MONGO_URI}
      MONGO_DB: ${MONGO_DB}
    volumes:
      - .:/app

volumes:
  postgres_data:
```

### 4. Para executar o Docker Compose, utilize o comando:

```bash
docker-compose up --build
```
Isso fará com que:
	•	O container do Postgres seja iniciado, criando o banco de dados conforme definido e executando os scripts de inicialização (por exemplo, o init.sql que pode criar o schema necessário).
	•	O container da aplicação FastAPI seja construído e iniciado.

A aplicação ficará acessível em http://localhost:8000.

### 5. Documentação da API
```
http://localhost:8000/docs.
```
### 6. Considerações Finais

Para Usuários Windows
	•	Docker:
Instale o Docker Desktop para Windows.
	•	Execução Local:
Certifique-se de que o Python 3.12 e o Poetry estejam instalados. Utilize o PowerShell ou Prompt de Comando para executar os comandos descritos.

Para Usuários Mac/Linux
	•	Docker:
Instale o Docker Desktop para Mac ou utilize o Docker Engine.
	•	Execução Local:
Certifique-se de que o Python 3.12 e o Poetry estejam instalados e utilize o terminal para os comandos.


