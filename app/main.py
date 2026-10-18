# app/main.py
import shutil
import uuid
from pathlib import Path
from app.tiles import mount_tiles
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app.convert import convert_to_cog
from app.db import (
    init_db, create_layer, mark_layer_done, mark_layer_failed,
    get_layer, list_layers,
)

UPLOAD_DIR = Path("uploads")
COG_DIR = Path("cogs")
UPLOAD_DIR.mkdir(exist_ok=True)
COG_DIR.mkdir(exist_ok=True)

app = FastAPI(title="GeoTIFF to COG Converter")
mount_tiles(app)

app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for this project; restrict in a real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


def _run_conversion(layer_id: str, input_path: Path, output_path: Path):
    try:
        result = convert_to_cog(str(input_path), str(output_path))
        mark_layer_done(
            layer_id,
            bounds=result["bounds"],
            original_size_mb=result["original_size_mb"],
            cog_size_mb=result["cog_size_mb"],
            compression_ratio=result["compression_ratio"],
        )
    except Exception as e:
        mark_layer_failed(layer_id, str(e))


@app.post("/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(400, "Only GeoTIFF files (.tif/.tiff) are accepted")

    layer_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{layer_id}.tif"
    output_path = COG_DIR / f"{layer_id}_cog.tif"

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    create_layer(layer_id, file.filename)
    background_tasks.add_task(_run_conversion, layer_id, input_path, output_path)

    return {"layer_id": layer_id, "status": "pending"}


@app.get("/status/{layer_id}")
def status(layer_id: str):
    layer = get_layer(layer_id)
    if not layer:
        raise HTTPException(404, "Layer not found")
    return layer


@app.get("/layers")
def layers():
    return list_layers()


@app.get("/")
def root():
    return {"status": "ok", "service": "geotiff-cog-service"}