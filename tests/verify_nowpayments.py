import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.append(os.getcwd())

from app.service.nowpayments_service import NOWPaymentsService

async def test_nowpayments_service():
    print("Testing NOWPaymentsService...")

    # Create a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    # Patch httpx.AsyncClient.post
    with patch("httpx.AsyncClient.post", new_callable=MagicMock) as mock_post:
        # Make the mock awaitable (return the response when awaited)
        async def async_return(*args, **kwargs):
            return mock_response

        mock_post.side_effect = async_return

        service = NOWPaymentsService()

        # Test validate_address
        mock_response.json.return_value = {"status": "OK"}

        is_valid = await service.validate_address("valid_address", "btc")
        print(f"validate_address (valid): {is_valid}")
        assert is_valid == True

        # Test create_payout
        mock_response.json.return_value = {
            "id": "batch_123",
            "withdrawals": [{"id": "payout_123", "status": "WAITING"}]
        }

        response = await service.create_payout([{"address": "addr", "currency": "btc", "amount": 100}])
        print(f"create_payout: {response}")
        assert response["id"] == "batch_123"

        # Test verify_payout
        mock_response.json.return_value = {"status": "OK"}
        is_verified = await service.verify_payout("batch_123", "123456")
        print(f"verify_payout: {is_verified}")
        assert is_verified == True

async def main():
    await test_nowpayments_service()
    print("\nAll tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
