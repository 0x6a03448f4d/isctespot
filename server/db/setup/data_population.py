import mariadb
import sys
import os
import random

# Adicionar a diretoria /app ao path para conseguir importar os serviços do servidor
sys.path.append('/app')

try:
    from services.security_service import security_service
except ImportError:
    print("Warning: Could not import security_service. IBANs might not be encrypted correctly.")
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
        host="mariadb",  # <--- ALTERADO DE 'localhost' PARA 'mariadb'
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
    """Gera um IBAN fictício para testes"""
    digits = ''.join([str(random.randint(0, 9)) for _ in range(21)])
    return f"PT50{digits}"

def insert_users():
    print("Inserting Users...")
    fake_users_tuples = [
        (
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
            user.get("IsAgent", 0)
        )
        for user in fake_users
    ]
    cursor.executemany("""
    INSERT INTO Users (Username, PasswordHash, Email, CreatedAt, LastLogin, CompanyID, ResetPassword, CommissionPercentage, LastLogout, isActive, IsAdmin, IsAgent)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, fake_users_tuples)
    db.commit()

def insert_companies():
    print("Inserting Companies...")
    fake_companies_tuples = [
        (
            company["CompanyID"],
            company["AdminUserID"],
            company["NumberOfEmployees"],
            company["Revenue"],
            company["CreatedAt"],
            company["CompanyName"]
        )
        for company in fake_companies
    ]
    cursor.executemany("""
    INSERT INTO Companies (CompanyID, AdminUserID, NumberOfEmployees, Revenue, CreatedAt, CompanyName)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, fake_companies_tuples)
    db.commit()

def insert_clients():
    print("Inserting Clients with Encrypted IBANs...")
    client_tuples = []
    
    for client in fake_clients:
        plain_iban = get_fake_iban()
        encrypted_iban = None
        if security_service:
            try:
                encrypted_iban = security_service.encrypt_sensitive_data(plain_iban)
            except Exception as e:
                print(f"Error encrypting IBAN for client {client.get('FirstName')}: {e}")

        client_tuples.append((
            client["FirstName"],
            client["LastName"],
            client["Email"],
            client["PhoneNumber"],
            client["Address"],
            client["City"],
            client["Country"],
            client["CreatedAt"],
            client["CompanyID"],
            encrypted_iban
        ))

    cursor.executemany("""
    INSERT INTO Clients (FirstName, LastName, Email, PhoneNumber, Address, City, Country, CreatedAt, CompanyID, EncryptedIBAN)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, client_tuples)
    db.commit()

def insert_products():
    print("Inserting Products...")
    fake_products_tuples = [
        (
            product["ProductID"],
            product["CompanyID"],
            product["ProductName"],
            product["FactoryPrice"],
            product["SellingPrice"],
            product["CreatedAt"]
        )
        for product in fake_products
    ]
    cursor.executemany("""
    INSERT INTO Products (ProductID, CompanyID, ProductName, FactoryPrice, SellingPrice, CreatedAt)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, fake_products_tuples)
    db.commit()

def insert_sales():
    print("Inserting Sales...")
    fake_sales_tuples = [
        (
            sale["UserID"],
            sale["ClientID"],
            sale["ProductID"],
            sale['Quantity'],
            sale["SaleDate"]
        )
        for sale in fake_sales
    ]
    cursor.executemany("""
    INSERT INTO Sales (UserID, ClientID, ProductID, Quantity, SaleDate)
    VALUES (%s, %s, %s, %s, %s)
    """, fake_sales_tuples)
    db.commit()

def insert_tickets():
    print("Inserting Tickets...")
    fake_tickets_tuples = [
        (
            ticket["UserID"],
            ticket["Status"],
            ticket["Category"],
            ticket['Description'],
            ticket["Messages"],
            ticket["CreatedAt"],
            ticket["UpdatedAt"]
        )
        for ticket in fake_tickets
    ]
    cursor.executemany("""
    INSERT INTO SupportTickets (UserID, Status, Category, Description, Messages, CreatedAt, UpdatedAt)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, fake_tickets_tuples)
    db.commit()

insert_users()
insert_companies()
insert_clients()
insert_products()
insert_sales()
insert_tickets()

cursor.close()
db.close()

print("Data inserted successfully!")
