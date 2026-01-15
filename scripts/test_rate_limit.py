import httpx
import asyncio
import time

URL = "http://localhost:8000/"

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        print("Testing rate limit on root endpoint (limit: 5/minute)...")

        # Send 5 requests (should succeed)
        for i in range(5):
            response = await client.get(URL)
            print(f"Request {i+1}: Status {response.status_code}")
            if response.status_code != 200:
                print("Error: Expected 200 OK")
                return

        # Send 6th request (should fail with 429)
        print("Sending 6th request (should fail)...")
        response = await client.get(URL)
        print(f"Request 6: Status {response.status_code}")

        if response.status_code == 429:
            print("SUCCESS: Rate limit enforced (429 Too Many Requests).")
        else:
            print(f"FAILURE: Expected 429, got {response.status_code}")

if __name__ == "__main__":
    try:
        asyncio.run(test_rate_limit())
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure the server is running on port 8000.")
