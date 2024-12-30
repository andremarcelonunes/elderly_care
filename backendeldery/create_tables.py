from database import db_instance
from models import Base

# Cria e dropa as tabelas no banco de dados
def recreate_tables():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=db_instance.engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=db_instance.engine)
    print("Tables recreated successfully!")

if __name__ == "__main__":
    recreate_tables()