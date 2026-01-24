import httpx
from typing import Optional, List, Dict, Any
from app.config import settings

class NOWPaymentsService:
    def __init__(self):
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.api_url = settings.NOWPAYMENTS_API_URL
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/{endpoint}",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                try:
                    return response.json()
                except Exception:
                    # If response is not JSON (e.g. 200 OK but empty or HTML), return empty dict or raise error
                    # For validation, 200 OK is enough, but let's be safe
                    if not response.content or response.text.strip() == "OK":
                        return {}
                    raise Exception(f"Invalid JSON response from NOWPayments: {response.text}")
            except httpx.TimeoutException:
                raise Exception("NOWPayments API timeout")
            except httpx.HTTPStatusError as e:
                raise Exception(f"NOWPayments API error: {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"NOWPayments API connection error: {str(e)}")

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.api_url}/{endpoint}",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                try:
                    return response.json()
                except Exception:
                    if not response.content:
                        return {}
                    raise Exception(f"Invalid JSON response from NOWPayments: {response.text}")
            except httpx.TimeoutException:
                raise Exception("NOWPayments API timeout")
            except httpx.HTTPStatusError as e:
                raise Exception(f"NOWPayments API error: {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"NOWPayments API connection error: {str(e)}")

    async def validate_address(self, address: str, currency: str, extra_id: Optional[str] = None) -> bool:
        """
        Validate a crypto address.
        """
        payload = {
            "address": address,
            "currency": currency,
            "extra_id": extra_id
        }
        try:
            # The API returns 200 OK for valid addresses, but we should check the response body if needed.
            # However, the documentation says "400 Bad Request" for invalid.
            # Let's assume 200 is valid.
            await self._post("payout/validate-address", payload)
            return True
        except httpx.HTTPStatusError:
            return False

    async def create_payout(self, withdrawals: List[Dict[str, Any]], ipn_callback_url: Optional[str] = None, payout_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a payout batch.
        """
        payload = {
            "withdrawals": withdrawals,
            "ipn_callback_url": ipn_callback_url,
            "payout_description": payout_description
        }
        return await self._post("payout", payload)

    async def verify_payout(self, batch_withdrawal_id: str, verification_code: str) -> bool:
        """
        Verify a payout batch with 2FA code.
        """
        payload = {
            "verification_code": verification_code
        }
        try:
            await self._post(f"payout/{batch_withdrawal_id}/verify", payload)
            return True
        except httpx.HTTPStatusError:
            return False

    async def get_payout_status(self, payout_id: str) -> Dict[str, Any]:
        """
        Get status of a single payout.
        """
        return await self._get(f"payout/{payout_id}")

    async def get_payouts(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List payouts.
        """
        return await self._get("payout", params)
