import httpx
import asyncio
import time
from pathlib import Path

URL = "http://localhost:8000"
LOG_FILE = Path("logs/app.log")

async def test_logging():
    # Clear existing log file for clean test
    if LOG_FILE.exists():
        with open(LOG_FILE, "w") as f:
            f.write("")

    async with httpx.AsyncClient() as client:
        print("1. Testing normal request...")
        response = await client.get(f"{URL}/")
        print(f"Status: {response.status_code}")

        print("\n2. Testing error request...")
        response = await client.get(f"{URL}/test-error")
        print(f"Status: {response.status_code}")

    print("\n3. Verifying log file content...")
    if not LOG_FILE.exists():
        print("FAILURE: Log file not found!")
        return

    with open(LOG_FILE, "r") as f:
        content = f.read()
        print("--- Log Content Start ---")
        print(content)
        print("--- Log Content End ---")

        if "Request: GET / - Status: 200" in content:
            print("\nSUCCESS: Normal request logged.")
        else:
            print("\nFAILURE: Normal request NOT logged.")

        if "Request failed: GET /test-error" in content and "ValueError: This is a test error" in content:
            print("SUCCESS: Error request and traceback logged.")
        else:
            print("FAILURE: Error request or traceback NOT logged.")

if __name__ == "__main__":
    try:
        asyncio.run(test_logging())
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure the server is running on port 8000.")
