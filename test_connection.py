from infra.db.connection import postgres_connection

try:
    with postgres_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT current_database();")

        banco = cursor.fetchone()

        print("Conexão OK!")
        print("Banco:", banco)

except Exception as e:
    print("Erro:")
    print(e)