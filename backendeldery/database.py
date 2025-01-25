import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backendeldery.config import settings
import logging


logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)

class Database:
    def __init__(self, database_url):
        # Configura o SQLAlchemy
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    def get_db(self):
        """
        Retorna uma sessão do banco de dados.
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def execute(self, sql):
        """
        Executa uma query SQL diretamente no banco.
        """
        with self.engine.connect() as connection:
            connection.execute(sql)

db_instance = Database(settings.DATABASE_URL)

# Alias para Base e SessionLocal, se necessário
Base = db_instance.Base
SessionLocal = db_instance.SessionLocal


# Configuração do SQLAlchemy
engine = create_engine(settings.DATABASE_URL)


function_sql = text("""
CREATE OR REPLACE FUNCTION elderly_care.log_audit()
RETURNS TRIGGER AS $$
DECLARE
    record_id_value INTEGER;
BEGIN
    -- Tenta buscar o valor do campo "id", caso exista
    BEGIN
        record_id_value := COALESCE(NEW.id, OLD.id);
    EXCEPTION WHEN undefined_column THEN
        record_id_value := NULL; -- Caso o campo "id" não exista, define como NULL
    END;

    -- Insere os dados na tabela temporária de auditoria
    INSERT INTO elderly_care.temp_audit_logs (
        table_name,
        action,
        record_id,
        user_id,
        old_data,
        new_data,
        timestamp,
        user_ip
    )
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        record_id_value,
        COALESCE(NEW.created_by, OLD.updated_by), -- Obtém user_id do registro
        row_to_json(OLD),
        row_to_json(NEW),
        now(),
        COALESCE(NEW.user_ip, OLD.user_ip)       -- Obtém user_ip do registro
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

# SQL para remover a trigger (se existir)
drop_trigger_sql = text("""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE t.tgname = 'audit_users' AND n.nspname = 'elderly_care'
    ) THEN
        EXECUTE 'DROP TRIGGER audit_users ON elderly_care.users';
    END IF;
END;
$$;
""")

drop_function_sql = text("""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'log_audit' AND n.nspname = 'elderly_care'
    ) THEN
        EXECUTE 'DROP FUNCTION elderly_care.log_audit();';
    END IF;
END;
$$;
""")


trigger_sql = text("""
CREATE TRIGGER audit_users
AFTER INSERT OR UPDATE OR DELETE ON elderly_care.users
FOR EACH ROW EXECUTE FUNCTION elderly_care.log_audit();
""")

def apply_audit_triggers_to_all_tables(connection, schema_name="elderly_care", exclude_tables=None, pause_between=0.5):
    """
    Aplica triggers de auditoria a todas as tabelas do esquema especificado, excluindo tabelas específicas.

    Args:
        connection: Conexão ativa ao banco de dados.
        schema_name (str): Nome do esquema onde as tabelas estão localizadas.
        exclude_tables (list): Lista de nomes de tabelas a serem ignoradas.
        pause_between (float): Tempo em segundos para pausar entre a criação de triggers.
    """
    exclude_tables = exclude_tables or ["temp_audit_logs", "audit_logs"]

    try:
        print(f"Fetching tables from schema '{schema_name}'...")
        result = connection.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema_name
        """), {"schema_name": schema_name})
        tables = result.fetchall()

        if not tables:
            print(f"No tables found in schema '{schema_name}'.")
            return

        print(f"Found {len(tables)} tables. Applying audit triggers (excluding {exclude_tables})...")

        for table in tables:
            table_name = table[0]

            # Ignorar tabelas específicas
            if table_name in exclude_tables:
                print(f"Skipping table '{table_name}' as it is excluded.")
                continue

            trigger_name = f"audit_{table_name}"

            try:
                print(f"Creating audit trigger for table '{table_name}'...")

                # Drop trigger se já existir
                connection.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM pg_trigger t
                        JOIN pg_class c ON t.tgrelid = c.oid
                        JOIN pg_namespace n ON c.relnamespace = n.oid
                        WHERE t.tgname = :trigger_name
                        AND n.nspname = :schema_name
                    ) THEN
                        EXECUTE format('DROP TRIGGER %I ON %I.%I', :trigger_name, :schema_name, :table_name);
                    END IF;
                END;
                $$;
                """), {
                    "trigger_name": trigger_name,
                    "schema_name": schema_name,
                    "table_name": table_name
                })

                # Criar a trigger
                connection.execute(text("""
                CREATE TRIGGER {trigger_name}
                AFTER INSERT OR UPDATE OR DELETE ON {schema_name}.{table_name}
                FOR EACH ROW EXECUTE FUNCTION {schema_name}.log_audit();
                """.format(
                    trigger_name=trigger_name,
                    schema_name=schema_name,
                    table_name=table_name
                )))

                print(f"Audit trigger for table '{table_name}' created successfully.")

            except Exception as table_error:
                print(f"Error while creating trigger for table '{table_name}': {str(table_error)}")

            # Pausa opcional para evitar sobrecarga
            if pause_between:
                time.sleep(pause_between)

    except Exception as e:
        print(f"An error occurred while applying audit triggers: {str(e)}")


def drop_triggers_and_function(connection, schema_name="elderly_care", function_name="log_audit"):
    """
    Remove todas as triggers que dependem da função especificada e, em seguida, exclui a função.

    Args:
        connection: Conexão ativa ao banco de dados.
        schema_name (str): Nome do esquema onde a função e as triggers estão localizadas.
        function_name (str): Nome da função de auditoria.
    """
    try:
        print("Fetching dependent triggers...")

        # Query para buscar todas as triggers dependentes da função
        dependent_triggers = connection.execute(text(f"""
        SELECT t.tgname AS trigger_name, c.relname AS table_name
        FROM pg_trigger t
        JOIN pg_proc p ON t.tgfoid = p.oid
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE p.proname = :function_name AND n.nspname = :schema_name;
        """), {"function_name": function_name, "schema_name": schema_name}).fetchall()

        # Drop cada trigger dependente
        for trigger in dependent_triggers:
            trigger_name = trigger[0]  # Primeiro elemento: nome da trigger
            table_name = trigger[1]  # Segundo elemento: nome da tabela
            print(f"Dropping trigger '{trigger_name}' on table '{table_name}'...")
            connection.execute(text(f"""
            DROP TRIGGER IF EXISTS {trigger_name} ON {schema_name}.{table_name};
            """))

        print(f"All triggers depending on function '{function_name}' dropped successfully.")

        # Drop a função com CASCADE
        print(f"Dropping function '{function_name}' with CASCADE...")
        connection.execute(text(f"""
        DROP FUNCTION IF EXISTS {schema_name}.{function_name} CASCADE;
        """))
        print(f"Function '{function_name}' dropped successfully.")

    except Exception as e:
        print(f"An error occurred while dropping triggers and function: {str(e)}")


def initialize_database():
    from models import Base  # Importa os modelos para registrar as tabelas
    with engine.begin() as connection:
        try:

            print("Dropping tables...")
            Base.metadata.drop_all(engine)
            print("Tables dropped successfully.")

            print("Creating tables...")
            Base.metadata.create_all(bind=engine)
            print("Tables created successfully.")

            print("Dropping existing trigger (if exists)...")
            drop_triggers_and_function(connection)
            print("Trigger dropped successfully.")

            print("Dropping existing function (if exists)...")
            connection.execute(drop_function_sql)
            print("Function dropped successfully.")

            print("Recreating audit function...")
            connection.execute(function_sql)
            print("Audit function recreated successfully.")

            print("Applying audit triggers to all tables...")
            apply_audit_triggers_to_all_tables(
                connection,
                schema_name="elderly_care",
                exclude_tables=["temp_audit_logs", "audit_logs"]
            )
            print("Audit triggers applied successfully.")


        except Exception as e:
            print("An error occurred during schema or table creation:", str(e))
            return

# Configuração para rodar o script diretamente
if __name__ == "__main__":
    initialize_database()