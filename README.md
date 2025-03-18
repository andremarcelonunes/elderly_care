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
Muitas IDE tem suporte para clonar o repositório, então você pode clonar diretamente da sua IDE.



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

O arquivo docker-compose.yml deve estar configurado para utilizar as variáveis do arquivo .env:
Tá tudo pronto, acho que você não precisar se preocupar com isso, mas se quiser dar uma olhada, segue o exemplo:
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

### 4. Para executar o Docker Compose, utilize o comando (se for Mac ou Linux deve rodar sem problemas):

```bash
docker-compose up --build
```
Isso fará com que:
	•	O container do Postgres seja iniciado, criando o banco de dados conforme definido e executando os scripts de inicialização (por exemplo, o init.sql que pode criar o schema necessário).
	•	O container da aplicação FastAPI seja construído e iniciado.

A aplicação ficará acessível em http://localhost:8000.

<span style="color: red; font-size: larger;">**Atenção para usuários windows!!!**</span>
Para rodar esse projeto no windows via  docker. Você vai precisar
1. Executar o powershell como administrador e rodar o comando abaixo para instalara o chocolate:
```bash
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))  

```
2 - Instalar dos2unix pelo powershell como administrador:
```bash
install dos2unix -y
```
3 - Já no terminal de sua IDE (feche e abra novamente, prefiro executar como administrador), Rodar na raiz do projeto o comando abaixo:
```bash
dos2unix backendeldery/start.sh
```
5 - Rodar o comando abaixo para subir o container:	
```bash
docker-compose up --build
```


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

![Diagrama UML](http://www.plantuml.com/plantuml/png/RLJ1Rjim3BtxAuXUjc5BFs27ebs70JqC6vRc730I4mkJPKEKCNXR_xsGcLXMcLEizqJgyJqfzvmmfh7ppJluYUOtdWYEVOJK4XoG2Hv_xRusmvcvoQilo7G3_ne0uv4PBjWC0MoWwotv-ViZc4YOwFs7y_94QVaU1tkXNfgNves0xxa9bvDblJvtnnIB2Eyef6Nva185YojaEv1nwDEq8C-4tRBuDWQJN1zq1rLOgDn1b6SFX2K65rgABhbmWcFikyMWflYLjUTHQeUAFyMTtB_KoPZhIhL5rAdcIqjr4XD6qxvjSnxR_IMhnEvvFB29xa2nwg7mVCf-P8hxFowrUvFLrmCAYy4Mifw6sN6gJqVctgmEm7cFigeF2KrTQMQiQc39as8ar2V94OCXYEGntmzktS3D4k7c_rs9jmIaSKb5uSfcNIW6A5p6g_2i-I4Fu6QfaF3WYUVNr66ODgdVvDzw5d5iNVSiPMASfBB7GgzXSQscrKlUcfOwN3rb0THRVfmpgg2dSEmhO3VOzPxjSj-aM1FIGhtSZ8hI7UD9nLlylRszk-BDPnYP-6g0kK06BDjAZ9hD6duCkJTwFts2gH_1O00Nh3EO25ABwOe4nxdSmc62JlugBrTletStMTfrvfw27Jl_2W00)
