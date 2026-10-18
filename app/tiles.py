# app/tiles.py
from fastapi import FastAPI
from titiler.core.factory import TilerFactory

cog_tiler = TilerFactory()


def mount_tiles(app: FastAPI):
    """Mount titiler's COG tile routes onto the main FastAPI app."""
    app.include_router(cog_tiler.router, prefix="/cog", tags=["tiles"])