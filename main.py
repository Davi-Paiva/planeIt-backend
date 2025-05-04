from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user, auth, plan, utils
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_destinations_collection
from app.services.openai_service import OpenAIService
from app.models.destination import seed_destinations
from app.data.destinations import destinations

app = FastAPI(title="HackUPC API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True, 
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Database events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    await seed_destinations()
    await OpenAIService.generate_destination_embeddings()
    destinations_collection = get_destinations_collection()
    for destination in destinations:
        tmp = await destinations_collection.find_one({"airport_code": destination['airport_code']})
        destination['embedding'] = tmp['embedding']


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(plan.router)
app.include_router(utils.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to HackUPC API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 