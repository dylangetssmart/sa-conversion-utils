def initialize(options):
    server = options.get('server')
    database = options.get('database')
    # initialize(options)
    # server = args.srv or SERVER
    # database = args.db or SOURCE_DB
    # init_dir = os.path.join(BASE_DIR, 'sql-scripts', 'initialize-needles')
    # sql_pattern = re.compile(r'^.*\.sql$', re.I)

    # print(f'Initializing Needles database {server}.{database}...')
    # try:
    #     # List all files in the initialization directory
    #     all_files = os.listdir(init_dir)
    #     # Filter files that match the SQL pattern
    #     files = [file for file in all_files if sql_pattern.match(file)]

    #     if not files:
    #         print(f'No scripts found in {init_dir}.')
    #     else:
    #         for file in files:
    #             sql_file_path = os.path.join(init_dir, file)
    #             # print(f'Executing script: {sql_file_path}')
    #             sql_runner(sql_file_path, server, database)
    # except Exception as e:
    #     print(f'Error reading directory {init_dir}\n{str(e)}')