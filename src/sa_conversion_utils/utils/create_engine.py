from sqlalchemy.engine import create_engine, URL

# URL 
# dialect+driver://username:password@host:port/database
# https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
# Special characters can be passed to URL.create() without any modification

# pyodbc
# https://github.com/mkleehammer/pyodbc/wiki/Connecting-to-SQL-Server-from-Windows

def main(
        server,
        username=None,
        password=None,
        port=None,
        database="master"
):

	# If username and password are omitted, use windows authentication (trusted connection)
	windows_auth = not (username and password)

	if windows_auth:
		connection_url = URL.create(
			"mssql+pyodbc",
			host=server,
			port=port,
			database=database,
			query={
				"driver": "ODBC Driver 17 for SQL Server",
				"trusted_connection": "yes"
			}
		)
	else:
		# Use username/password authentication
		connection_url = URL.create(
			"mssql+pyodbc",
			username=username,
			password=password,
			host=server,
			port=port,
			database=database,
			query={
				"driver": "ODBC Driver 17 for SQL Server",
			}
		)

    # conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    # connection_string = f"mssql+pyodbc://sa:SAsuper@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
	engine = create_engine(
		connection_url,
		pool_pre_ping=True
	)

	return engine

if __name__ == "__main__":
    # Example usage
    engine = main(
        server="your_server",
        username="your_username",
        password="your_password",
        database="your_database",
        windows_auth=False
    )
    print(engine)