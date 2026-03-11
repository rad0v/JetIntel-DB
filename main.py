from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.auth import router as auth_router
from routes.jets import router as jets_router
from routes.recommend import router as recommend_router
from routes.admin import router as admin_router

app = FastAPI(
    title="JetIntel API",
    description="Private jet intelligence platform with role-based access",
    version="2.0.0",
)

# Serve static images
app.mount("/images", StaticFiles(directory="static/images"), name="images")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(jets_router)
app.include_router(recommend_router)
app.include_router(admin_router)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "JetIntel API is running", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
