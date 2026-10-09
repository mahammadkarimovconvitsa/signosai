from fastapi import APIRouter

from app.api.v1.endpoints import (
    actions,
    admin,
    alarms,
    analysis,
    audit,
    auth,
    config,
    contracts,
    explain,
    health,
    incidents,
    market,
    network,
    portfolio,
    stream,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(network.router)
api_router.include_router(contracts.router)
api_router.include_router(market.router)
api_router.include_router(config.router)
api_router.include_router(users.router)
api_router.include_router(alarms.router)
api_router.include_router(incidents.router)
api_router.include_router(analysis.router)
api_router.include_router(portfolio.router)
api_router.include_router(actions.router)
api_router.include_router(audit.router)
api_router.include_router(explain.router)
api_router.include_router(admin.router)
api_router.include_router(stream.router)
