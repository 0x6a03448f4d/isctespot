# Quick Reference Guide - Payment Features

## API Endpoints

### 1. Update User Payment Info
```bash
POST /user/payment-info
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "nib": "PT50 0002 0123 1234 5678 9015 4"
}

Response: {"status": "Ok"} (200)
```

### 2. Update Company Card
```bash
POST /payment-card
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "card_number": "4111111111111111",
  "exp_month": "12",
  "exp_year": "2030"
}

Response: {"status": "Ok"} (200)
```

### 3. Make Immediate Payment
```bash
POST /pay
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "destination_iban": "PT50 0002 0123 1234 5678 9015 4",
  "amount_cents": 10000
}

Response: {
  "status": "Ok",
  "fastpay_response": {
    "id": "pay_123456",
    "status": "completed",
    ...
  }
} (200)
```

### 4. Schedule Payment
```bash
POST /schedule-pay
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "destination_iban": "PT50 0002 0123 1234 5678 9015 4",
  "amount_cents": 10000,
  "schedule_at": "2025-12-31T12:00:00Z"
}

Response: {
  "status": "Ok",
  "fastpay_response": {
    "id": "sched_123456",
    "status": "scheduled",
    ...
  }
} (200)
```

## Error Responses

### 400 Bad Request
```json
{"status": "Bad request"}
```
- Missing required fields
- Invalid data format

### 403 Unauthorized
```json
{"status": "Unauthorised"}
```
- Invalid or expired token
- Insufficient permissions (not admin)

### 500 Error
```json
{
  "status": "Error",
  "message": "FastPay error 400: Invalid IBAN"
}
```
- External service errors
- Database errors

## Code Examples

### Python - Encrypt Sensitive Data
```python
from api.utils.crypto_utils import encrypt_with_public_key, decrypt_with_private_key

# Encrypt NIB before storing
nib = "PT50 0002 0123 1234 5678 9015 4"
encrypted_nib = encrypt_with_public_key(nib)
# Store encrypted_nib in database

# Decrypt when needed for payment
decrypted_nib = decrypt_with_private_key(encrypted_nib)
# Use decrypted_nib for FastPay API
```

### Python - Direct FastPay Client Usage
```python
import os
from services.fastpay_client import FastPayClient

# Set environment variable
os.environ["FASTPAY_API_TOKEN"] = "your_token"

# Create client
client = FastPayClient()

# Make payment
response = client.pay_now(
    source_iban="PT50 0002 0123 1234 5678 9015 4",
    destination_iban="PT50 9999 8888 7777 6666 5555 4",
    amount_cents=10000,  # €100.00
    currency="EUR"
)

print(response)
# {'id': 'pay_xxx', 'status': 'completed', ...}
```

### Python - Using ProcessPayments Service
```python
from services.process_payments import ProcessPayments

# Initialize for company
processor = ProcessPayments(comp_id=123)

# Make payment (automatically retrieves and decrypts company NIB)
response = processor.pay_single(
    destination_iban_encrypted="<encrypted_iban>",
    amount_cents=10000
)

# Schedule payment
response = processor.schedule_payment(
    destination_iban_encrypted="<encrypted_iban>",
    amount_cents=10000,
    schedule_at_iso="2025-12-31T12:00:00Z"
)
```

## Database Queries

### Get Encrypted NIB for Company
```python
from db.db_connector import DBConnector

dbc = DBConnector()
encrypted_nib = dbc.execute_query('get_company_nib_encrypted', args=comp_id)
```

### Update User NIB
```python
dbc.execute_query('update_user_nib', args={
    'user_id': 123,
    'nib_encrypted': encrypted_nib
})
```

### Update Company Card
```python
dbc.execute_query('update_company_card', args={
    'comp_id': 456,
    'card_encrypted': encrypted_card,
    'exp_month': '12',
    'exp_year': '2030'
})
```

### Log Payment History
```python
dbc.execute_query('insert_payment_history', args={
    'comp_id': 456,
    'dest_iban_masked': 'PT50****9015',
    'amount_cents': 10000,
    'status': 'completed',
    'external_id': 'pay_123456'
})
```

## Environment Variables

```bash
# Required for FastPay integration
export FASTPAY_API_TOKEN="sk_live_xxxxxxxxxxxx"

# Optional (defaults to https://api.fastpay.example.com)
export FASTPAY_BASE_URL="https://api.fastpay.production.com"
```

## Testing

```bash
# Run all tests
cd /Users/admin/Documents/GitHub/isctespot/server
FASTPAY_API_TOKEN=test_token python test_new_features.py

# Test specific module
python -c "from api.utils.crypto_utils import *; print('Crypto OK')"
python -c "from services.fastpay_client import *; print('FastPay OK')"
python -c "from services.process_payments import *; print('Payments OK')"
```

## Security Best Practices

1. **Never log decrypted data**
   ```python
   # ❌ BAD
   print(f"NIB: {decrypted_nib}")
   
   # ✅ GOOD
   print(f"NIB: {processor._mask_iban(decrypted_nib)}")
   ```

2. **Always use HTTPS in production**
   ```python
   # ✅ GOOD
   FASTPAY_BASE_URL = "https://api.fastpay.com"
   
   # ❌ BAD
   FASTPAY_BASE_URL = "http://api.fastpay.com"
   ```

3. **Validate tokens before payment operations**
   ```python
   is_valid, payload = validate_token(token)
   if not is_valid or not payload.get('is_admin'):
       return jsonify({'status': 'Unauthorised'}), 403
   ```

4. **Use idempotency keys for safety**
   - FastPay client automatically generates unique keys
   - Safe to retry failed requests

## Troubleshooting

### "FASTPAY_API_TOKEN is not configured"
```bash
export FASTPAY_API_TOKEN="your_token_here"
```

### "No module named 'mariadb'"
```bash
brew install mariadb-connector-c
export MARIADB_CONFIG=/opt/homebrew/opt/mariadb-connector-c/bin/mariadb_config
pip install mariadb
```

### "No NIB configured for this company"
- Ensure company admin has set their NIB via `/user/payment-info`
- Check database: `SELECT NIBEncrypted FROM Users WHERE UserID = ?`

### Keys not generating
- Check `server/keys/` directory exists
- Check write permissions
- Manually create: `mkdir -p server/keys`
