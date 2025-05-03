from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from app.models.plan import Plan, PlanCreate, PlanUser
from app.services.auth import get_current_user_from_request, get_user_or_raise_401
from app.db.mongodb import get_plans_collection
from bson import ObjectId
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/plan",
    tags=["plan"],
    responses={404: {"description": "Not found"}},
)

# Helper function to convert MongoDB plan document to Plan model
def plan_doc_to_model(plan_doc):
    if not plan_doc:
        return None
    
    # Convert ObjectId to string
    if "_id" in plan_doc:
        plan_doc["id"] = str(plan_doc["_id"])
        del plan_doc["_id"]
    
    # Ensure dates are datetime objects
    if isinstance(plan_doc.get("startDate"), str):
        plan_doc["startDate"] = datetime.fromisoformat(plan_doc["startDate"].replace("Z", "+00:00"))
    
    if isinstance(plan_doc.get("endDate"), str):
        plan_doc["endDate"] = datetime.fromisoformat(plan_doc["endDate"].replace("Z", "+00:00"))
    
    return Plan(**plan_doc)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_plan(plan_data: PlanCreate, request: Request):
    """
    Create a new travel plan
    """
    # Get the current user
    user = await get_user_or_raise_401(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate a unique code for the plan
    code = str(uuid.uuid4())[:6].upper()
    
    # Parse the date strings (format: YYYY-MM-DD)
    try:
        start_date = datetime.strptime(plan_data.startDate, "%Y-%m-%d")
        end_date = datetime.strptime(plan_data.endDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Create a PlanUser from the current user
    plan_user = PlanUser(
        name=user.name,
        email=user.email
    )
    
    # Create plan object
    plan = Plan(
        name=plan_data.name,
        description=plan_data.description,
        startDate=start_date,
        endDate=end_date,
        code=code,
        users=[plan_user],
        creator=plan_user
    )
    
    # Convert plan to dict for MongoDB
    plan_dict = json.loads(plan.model_dump_json())
    
    # Store in MongoDB
    plans_collection = get_plans_collection()
    result = await plans_collection.insert_one(plan_dict)
    
    # Add the MongoDB id to the plan
    plan_dict["id"] = str(result.inserted_id)
    if "_id" in plan_dict:
        del plan_dict["_id"]
    
    # Return the created plan
    return plan_dict
    

@router.get("/", response_model=List)
async def get_all_plans(request: Request):
    """
    Get all plans for the current user
    """
    # Get the current user (optional - return empty list if not authenticated)
    user = await get_current_user_from_request(request)
    if not user:
        return []
    
    # Get plans from MongoDB where the user is a member
    plans_collection = get_plans_collection()
    cursor = plans_collection.find({
        "users.email": user.email
    })
    
    # Convert MongoDB documents to list of dicts
    plans = []
    async for plan_doc in cursor:
        plan_doc["id"] = str(plan_doc["_id"])
        del plan_doc["_id"]
        plans.append(plan_doc)
    
    return plans

@router.get("/{code}")
async def get_plan(code: str, request: Request):
    """
    Get a plan by code
    """
    user = await get_user_or_raise_401(request)

    # Find plan in MongoDB
    plans_collection = get_plans_collection()
    plan_doc = await plans_collection.find_one({"code": code})
    
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plan not found")

    if user.email not in [user["email"] for user in plan_doc["users"]]:
        plan_user = PlanUser(
            name=user.name,
            email=user.email
        )
        plan_user_dict = json.loads(plan_user.model_dump_json())
        plan_doc["users"].append(plan_user_dict)
        await plans_collection.update_one(
            {"code": code},
            {"$set": {"users": plan_doc["users"]}}
        )

    # Convert to dict for response
    plan_doc["id"] = str(plan_doc["_id"])
    del plan_doc["_id"]
    
    return plan_doc
