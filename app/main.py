import sys
import time
import traceback
from fastapi import FastAPI, Request, Response
import uvicorn
from contextlib import asynccontextmanager

# Setup logging first to capture any startup errors
try:
    from app.core.logging_config import logger
except ImportError as e:
    print(f"Failed to import logging config: {e}")
    sys.exit(1)

try:
    from app.db.session import init_db
    import app.models
    from app.api.v1.endpoints import auth, users, admin, payments, transactions, prop_firm, discounts, notification, support, crypto_payments, wallet
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
except Exception as e:
    logger.critical(f"Failed to start application: {e}")
    logger.critical(traceback.format_exc())
    sys.exit(1)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    await init_db()
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="PROPSOL",
    lifespan=lifespan,
)

# Security Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"]) # In production, replace with specific hosts
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.2f}ms")
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Request failed: {request.method} {request.url.path} - Duration: {process_time:.2f}ms - Error: {str(e)}")
        logger.error(traceback.format_exc())
        return Response("Internal Server Error", status_code=500)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(prop_firm.router, prefix="/api/v1/prop-firm", tags=["prop-firm"])
app.include_router(discounts.router, prefix="/api/v1/discounts", tags=["discounts"])
app.include_router(notification.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(support.router, prefix="/api/v1/support", tags=["support"])
app.include_router(crypto_payments.router, prefix="/api/v1/crypto-payments", tags=["crypto-payments"])
app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["wallet"])


@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
