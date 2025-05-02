from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user

app = FastAPI(title="HackUPC API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(user.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to HackUPC API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 