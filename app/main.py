from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(title="Site Feasibility API", version="0.1.0")

# Let the web viewer's Vite dev server (a different origin) call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}