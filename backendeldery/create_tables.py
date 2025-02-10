from database import initialize_database


# Recria tabelas e triggers
def recreate_tables():
    print("Recreating DB...")
    initialize_database()
    print("DB was recreated successfully!")


if __name__ == "__main__":
    recreate_tables()
