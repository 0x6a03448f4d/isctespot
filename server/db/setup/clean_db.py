import mariadb

# Establish a connection to the MariaDB database
db = mariadb.connect(
    host="mariadb",
    user="root",
    password="teste123",
    database="iscte_spot",
    port=3306
)

cursor = db.cursor()

def drop_all_tables():
    # A ordem é CRÍTICA devido às Foreign Keys
    tables = [
        'AuditLogs',      # <-- NOVO
        'Payments',       # <-- NOVO
        'Sales', 
        'SupportTickets', 
        'Products', 
        'Clients', 
        'Companies', 
        'Users'
    ]
    # Drop each table
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Table {table} dropped.")

    db.commit()

# Run the drop tables function
drop_all_tables()

# Close the connection
cursor.close()
db.close()
