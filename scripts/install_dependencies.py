import subprocess
import sys

# === List of required packages with versions ===
packages = [
    "aiosqlite==0.22.0",
    "alembic",  # Required for migrations
    "annotated-doc==0.0.4",
    "annotated-types==0.7.0",
    "anyio==4.12.0",
    "asyncpg==0.31.0",
    "bcrypt==5.0.0",
    "click==8.3.1",
    "dnspython==2.8.0",
    "dotenv==0.9.9",
    "ecdsa==0.19.1",
    "email-validator==2.3.0",
    "fastapi==0.124.4",
    "greenlet==3.3.0",
    "h11==0.16.0",
    "httpx", # Required for HTTP requests
    "idna==3.11",
    "jinja2", # Required for templating
    "mailjet==1.4.1",
    "passlib==1.7.4",
    "pyasn1==0.6.1",
    "pydantic==2.12.5",
    "pydantic-settings==2.12.0",
    "pydantic_core==2.41.5",
    "python-dotenv==1.2.1",
    "python-jose==3.5.0",
    "python-multipart==0.0.20",
    "requests", # Standard synchronous HTTP library
    "rsa==4.9.1",
    "selenium", # Required for automation
    "six==1.17.0",
    "slowapi", # Rate limiting
    "SQLAlchemy==2.0.45",
    "sqlmodel==0.0.27",
    "starlette==0.50.0",
    "typing-inspection==0.4.2",
    "typing_extensions==4.15.0",
    "uvicorn==0.38.0",
    "webdriver-manager", # For managing selenium drivers
]

def install(package):
    """Install a Python package using pip."""
    try:
        print(f"📦 Installing {package} ...")
        # Use sys.executable to ensure pip is from the correct virtual env
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}\n")

if __name__ == "__main__":
    print("--- Starting package installation ---")
    for pkg in packages:
        install(pkg)
    print("--- All packages processed ---")
