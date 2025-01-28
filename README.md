# Projeto Cuidar

Projeto que visa criar uma plataforma para conectar pessoas que precisam de cuidados com pessoas que podem oferecer cuidados.

## Índice

- [Sobre](#sobre)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso](#uso)


## Sobre

Nasceu de uma ideia de um grupo de amigos que queriam ajudar pessoas que precisam de cuidados e pessoas que podem oferecer cuidados. A ideia é criar uma plataforma que conecte essas pessoas.

# Funcionalidades principais:
- Cadastrar pessoas quee precisam de cuidados
- Cadastrar pessoas quee podem oferecer cuidados
- Conectar pessoas que precisam de cuidados com pessoas que podem oferecer cuidados
- Avaliar pessoas que oferecem cuidados
- Manter um histórico de cuidados
- Pedidos de ajuda
    

# Tecnologias utilizadas:
- Python 
- FastAPI
- Postgres


## Pré-requisitos

1. [x] Versões de software:
  - Python 3.12.8
  - Postgres 17.2
2. [x] Dependências:

* python = "^3.12"
* fastapi = "^0.115.6"
* starlette = ">=0.40.0,<0.42.0"
* uvicorn = "^0.34.0"
* sqlalchemy = "^2.0.36"
* psycopg2-binary = "^2.9.10"
* pymongo = ">=4.9,<4.10"
* motor = "^3.6.0"
* pydantic-settings = "^2.7.0"
* passlib = "^1.7.4"
* bcrypt = "==3.2.0"
* pydantic = {extras = ["email"], version = "^2.10.4"}


## Instalação
```bash
poetry install
```
Criar schema no banco de dados, exemplo: elderydb


Criar o arquivo config.py dentro da pasta /backendeldery e configurar para o banco de dados postgresql

```bash
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://elderydb:teste123@localhost/elderly_care"
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "elderly_care"

settings = Settings()
```


Executar o comando para criar as tabelas no banco de dados
```bash
python create_tables.py   
```

## Executar o Servidor Local

```bash
poetry shell


uvicorn main:app --reload   

```

Acessar a documentação da API
```bash
http://127.0.0.1:8000/docs
```