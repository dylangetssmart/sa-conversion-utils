from sqlalchemy import create_engine
import pyodbc

dyl = r'mssql+pyodbc://dylans\mssqlserver2022/VanceLawFirm_SA?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
tan = r'mssql+pyodbc://sa:SAsuper11050@72.52.250.51/testTanya?driver=ODBC+Driver+17+for+SQL+Server'

eng = create_engine(tan)

try:
    with eng.connect() as connection:
        print("connection success")
except Exception as e:
    print(f"fail: {e}")