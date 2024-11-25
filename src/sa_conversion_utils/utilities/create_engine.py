from sqlalchemy.engine import create_engine, URL

# URL 
# dialect+driver://username:password@host:port/database
# https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
# Special characters can be passed to URL.create() without any modification

def main(server,username,password, database,post,windows_auth = False):

    connection_url = URL.create(
        "mssql+pyodbc",
        username=username,
        password=password,  # can include unescaped special characters
        host=server,
        port=1433,
        database=database,
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "TrustServerCertificate": "yes",
            "authentication": "ActiveDirectoryIntegrated",
        },
    )
    # conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    # connection_string = f"mssql+pyodbc://sa:SAsuper@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    engine = create_engine(connection_url)

    return engine