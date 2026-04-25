from fastapi import APIRouter

from app.routers import auth, bookings, equipment, recommendations, rooms, system, users


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(equipment.router)
api_router.include_router(rooms.router)
api_router.include_router(bookings.router)
api_router.include_router(recommendations.router)
api_router.include_router(system.router)
