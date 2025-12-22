import mariadb
import sys
import os
import random
import uuid

# Permitir importar serviços do servidor para encriptação
sys.path.append('/app')

try:
    from services.security_service import security_service
except ImportError:
    print("Warning: Could not import security_service. Running without encryption (Data might be invalid).")
    security_service = None

from fakes.fake_users import data as fake_users
from fakes.fake_companies import data as fake_companies
from fakes.fake_clients import data as fake_clients
from fakes.fake_products import data as fake_products
from fakes.fake_sales import data as fake_sales
from fakes.fake_tickets import data as fake_tickets

# Database connection
try:
    db = mariadb.connect(
        host="mariadb",
        user="root",
        password="teste123",
        port=3306,
        database="iscte_spot"
    )
    cursor = db.cursor()
except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    sys.exit(1)

def get_fake_iban():
    return f"PT50{random.randint(100000000000000000000, 999999999999999999999)}"

def encrypt_helper(data):
    if security_service:
        return security_service.encrypt_sensitive_data(data)
    return f"PLAIN_{data}" # Fallback apenas se import falhar

# --- INSERTS ATUALIZADOS ---

def insert_users():
    print("Inserting Users with IBANs...")
    fake_users_tuples = []
    for user in fake_users:
        # Simular que alguns users têm IBAN configurado (para receberem comissão)
        iban = encrypt_helper(get_fake_iban()) if user['IsAdmin'] == 0 else None
        
        fake_users_tuples.append((
            user.get("Username"),
            user.get("PasswordHash"),
            user.get("Email"),
            user.get("CreatedAt"),
            user.get("LastLogin"),
            user.get("CompanyID"),
            user.get("ResetPassword", 0),
            user.get("CommissionPercentage", 5),
            user.get("LastLogout"),
            user.get("isActive", 0),
            user.get("IsAdmin", 0),
            user.get("IsAgent", 0),
            iban # EncryptedIBAN
        ))

    cursor.executemany("""
    INSERT INTO Users (Username, PasswordHash, Email, CreatedAt, LastLogin, CompanyID, ResetPassword, CommissionPercentage, LastLogout, isActive, IsAdmin, IsAgent, EncryptedIBAN)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, fake_users_tuples)
    db.commit()

def insert_companies():
    print("Inserting Companies with Tokens...")
    fake_companies_tuples = []
    for company in fake_companies:
        # Simular token de cartão já associado
        token = f"tok_company_{company['CompanyID']}_setup"
        
        fake_companies_tuples.append((
            company["CompanyID"],
            company["AdminUserID"],
            company["NumberOfEmployees"],
            company["Revenue"],
            company["CreatedAt"],
            company["CompanyName"],
            token, # FastPayCardToken
            "Manual" # PaymentSchedule
        ))

    cursor.executemany("""
    INSERT INTO Companies (CompanyID, AdminUserID, NumberOfEmployees, Revenue, CreatedAt, CompanyName, FastPayCardToken, PaymentSchedule)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, fake_companies_tuples)
    db.commit()

# ... (Manter insert_clients, insert_products, insert_sales, insert_tickets IGUAIS) ...
def insert_clients():
    print("Inserting Clients...")
    client_tuples = []
    for client in fake_clients:
        iban = encrypt_helper(get_fake_iban())
        client_tuples.append((
            client["FirstName"], client["LastName"], client["Email"], client["PhoneNumber"],
            client["Address"], client["City"], client["Country"], client["CreatedAt"],
            client["CompanyID"], iban
        ))
    cursor.executemany("""
    INSERT INTO Clients (FirstName, LastName, Email, PhoneNumber, Address, City, Country, CreatedAt, CompanyID, EncryptedIBAN)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, client_tuples)
    db.commit()

def insert_products():
    print("Inserting Products...")
    tuples = [(p["ProductID"], p["CompanyID"], p["ProductName"], p["FactoryPrice"], p["SellingPrice"], p["CreatedAt"]) for p in fake_products]
    cursor.executemany("INSERT INTO Products (ProductID, CompanyID, ProductName, FactoryPrice, SellingPrice, CreatedAt) VALUES (%s, %s, %s, %s, %s, %s)", tuples)
    db.commit()

def insert_sales():
    print("Inserting Sales...")
    tuples = [(s["UserID"], s["ClientID"], s["ProductID"], s['Quantity'], s["SaleDate"]) for s in fake_sales]
    cursor.executemany("INSERT INTO Sales (UserID, ClientID, ProductID, Quantity, SaleDate) VALUES (%s, %s, %s, %s, %s)", tuples)
    db.commit()

def insert_tickets():
    print("Inserting Tickets...")
    tuples = [(t["UserID"], t["Status"], t["Category"], t['Description'], t["Messages"], t["CreatedAt"], t["UpdatedAt"]) for t in fake_tickets]
    cursor.executemany("INSERT INTO SupportTickets (UserID, Status, Category, Description, Messages, CreatedAt, UpdatedAt) VALUES (%s, %s, %s, %s, %s, %s, %s)", tuples)
    db.commit()

# Ordem de execução
insert_users()
insert_companies()
insert_clients()
insert_products()
insert_sales()
insert_tickets()

cursor.close()
db.close()
print("Data populated successfully with encrypted fields.")
