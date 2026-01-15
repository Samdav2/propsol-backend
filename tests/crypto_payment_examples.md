# NOWPayments Quick Start - USD Payments

## Create Invoice (Simple Example)

All payments are automatically configured to use **USD** as the price currency.

### Minimal Request

```bash
curl -X POST http://localhost:8000/api/v1/crypto-payments/invoice \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_amount": 100,
    "pay_currency": "btc"
  }'
```

### With Additional Details

```bash
curl -X POST http://localhost:8000/api/v1/crypto-payments/invoice \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_amount": 250.50,
    "pay_currency": "btc",
    "order_id": "ORDER-12345",
    "order_description": "Premium subscription - 1 year",
    "ipn_callback_url": "https://yourdomain.com/api/v1/crypto-payments/ipn-callback"
  }'
```

## Create Direct Payment

```bash
curl -X POST http://localhost:8000/api/v1/crypto-payments/payment \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_amount": 50,
    "pay_currency": "eth",
    "order_id": "ORDER-67890",
    "order_description": "Monthly plan"
  }'
```

## Python Example

```python
import requests

# Your JWT token (from login)
TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create invoice - price_currency defaults to "usd"
invoice_data = {
    "price_amount": 100,  # $100 USD
    "pay_currency": "btc",  # User pays with Bitcoin
    "order_id": "ORDER-001",
    "order_description": "Test product"
}

response = requests.post(
    "http://localhost:8000/api/v1/crypto-payments/invoice",
    json=invoice_data,
    headers=headers
)

result = response.json()
print(f"Invoice URL: {result['invoice_url']}")
print(f"Payment ID: {result['id']}")
```

## Available Crypto Currencies

```bash
curl http://localhost:8000/api/v1/crypto-payments/currencies
```

Popular options:
- `btc` - Bitcoin
- `eth` - Ethereum
- `trx` - Tron
- `usdt` - Tether (multiple networks)
- `bnb` - Binance Coin
- `ltc` - Litecoin
- `doge` - Dogecoin

## Check Minimum Amount

```bash
# Get minimum BTC amount for $1 USD
curl "http://localhost:8000/api/v1/crypto-payments/min-amount?currency_from=btc&currency_to=usd"
```

## Get Price Estimate

```bash
# How much BTC for $100 USD?
curl "http://localhost:8000/api/v1/crypto-payments/estimate?amount=100&currency_from=usd&currency_to=btc"
```

## Default Configuration

✅ All payments use **USD** by default
✅ `price_currency` is automatically set to `"usd"`
✅ Users only need to specify:
  - `price_amount` (amount in USD)
  - `pay_currency` (cryptocurrency type)

## Response Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "invoice_id": "4522625843",
  "price_amount": 100.0,
  "price_currency": "usd",
  "pay_currency": "btc",
  "invoice_url": "https://nowpayments.io/payment/?iid=4522625843",
  "payment_status": "waiting",
  "is_fixed_rate": false,
  "is_fee_paid_by_user": false,
  "created_at": "2026-01-14T21:30:00Z",
  "updated_at": "2026-01-14T21:30:00Z"
}
```
