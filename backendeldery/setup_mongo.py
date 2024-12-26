from database_nosql import emergency_collection

async def setup_mongo():
    print("Configurando índices no MongoDB...")
    # Índice para buscar emergências por paciente
    await emergency_collection.create_index("patient_id")

    # Índice para melhorar buscas por status
    await emergency_collection.create_index("status")

    print("Configuração concluída!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_mongo())