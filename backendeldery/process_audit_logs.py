import time
from sqlalchemy import create_engine, text
from config import settings

# Configuração do SQLAlchemy
engine = create_engine(settings.DATABASE_URL)

def process_temp_audit_logs():
    """Processa logs da tabela temporária e os insere na tabela definitiva."""
    with engine.connect() as connection:
        while True:
            try:
                print("Fetching audit logs from temporary table...")
                result = connection.execute(text("""
                DELETE FROM elderly_care.temp_audit_logs
                RETURNING table_name, action, record_id, user_id, old_data, new_data, timestamp, user_ip;
                """))
                rows = result.fetchall()

                if not rows:
                    print("No logs to process. Sleeping for 5 seconds...")
                    time.sleep(5)  # Aguarda antes de verificar novamente
                    continue

                print(f"Processing {len(rows)} audit logs...")
                for row in rows:
                    connection.execute(text("""
                    INSERT INTO elderly_care.audit_logs (
                        table_name, action, record_id, user_id, old_data, new_data, timestamp, user_ip
                    ) VALUES (:table_name, :action, :record_id, :user_id, :old_data, :new_data, :timestamp, :user_ip);
                    """), row._asdict())

                print("Audit logs processed successfully.")
            except Exception as e:
                print(f"Error processing audit logs: {str(e)}")
                time.sleep(5)  # Evita loops rápidos em caso de erro

if __name__ == "__main__":
    print("Starting audit log processor...")
    process_temp_audit_logs()