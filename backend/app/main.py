from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.carts import router as carts_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.merchant_policy import router as merchant_policy_router
from app.api.merchants import router as merchants_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.products import router as products_router
from app.api.relationships import router as relationships_router
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
)
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT})")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-oriented AI-native commerce platform backend designed to make "
        "merchants transactable by AI buyers.\n\n"
        "### Key Capabilities & Governance:\n"
        "- **Authentication**: JWT access tokens with merchant user role isolation (`merchant_admin`, `merchant_staff`).\n"
        "- **Policy Engine**: Deterministic evaluation of transaction limits, discount thresholds, approval requirements, and buyer limits.\n"
        "- **Cart & Order Foundation**: Server-side pricing enforcement, immutable product snapshots, and scoped idempotency handling.\n"
        "- **Approvals & Audit**: Order review workflow (`AWAITING_APPROVAL`, `APPROVED`, `CANCELLED`) and comprehensive event audit logging.\n"
        "- **AI Commerce Agent**: Autonomous structured tool execution, catalog search, recommendation links, and policy-governed checkout.\n"
        "- **Razorpay Test Mode Payments**: Server-side order creation in paise, HMAC-SHA256 signature verification, webhook processing, replay protection, and retries."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Routers
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")

# Commerce & Payment Routers
app.include_router(auth_router, prefix="/api")
app.include_router(merchant_policy_router, prefix="/api")
app.include_router(carts_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")

app.include_router(merchants_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(relationships_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
