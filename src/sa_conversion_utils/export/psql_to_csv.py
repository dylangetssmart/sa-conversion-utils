import psycopg
import os


def export_all_tables_to_csv(
    host: str, dbname: str, user: str, password: str, output_dir: str = "./exports"
):
    """Connects to a PostgreSQL database and exports all tables to CSV using COPY TO."""
    os.makedirs(output_dir, exist_ok=True)

    conn_str = f"host={host} dbname={dbname} user={user} password={password}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cursor:
            # Fetch all table names in public schema
            cursor.execute(
                """
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname = 'public';
            """
            )
            tables = cursor.fetchall()

            for (table_name,) in tables:
                file_path = os.path.join(output_dir, f"{table_name}.csv")
                print(f"Exporting {table_name} ...")

                with open(file_path, "wb") as f:
                    with cursor.copy(f"COPY {table_name} TO STDOUT") as copy:
                        for data in copy:
                            f.write(data)

    print("All tables exported successfully.")
