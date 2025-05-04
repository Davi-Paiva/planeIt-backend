from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from app.models.plan import Plan, PlanCreate, PlanUser
from app.services.auth import get_current_user_from_request, get_user_or_raise_401
from app.db.mongodb import get_plans_collection, get_destinations_collection
from bson import ObjectId
import logging
import json
from app.services.pexels_service import PexelsService
from app.data.destinations import destinations
from app.services.amadeus_service import AmadeusService
from app.models.destination import DestinationSuggestion
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
    user = await get_current_user_from_request(request)
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
        email=user.email,
        is_quiz_completed=False
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
            email=user.email,
            is_quiz_completed=False
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


@router.post("/{code}/vote/{airport_code}")
async def vote_destination(code: str, airport_code: str, request: Request):
    """
    Vote for a destination
    """
    logger.info(f"Voting for destination {airport_code} in plan {code}")
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    plans_collection = get_plans_collection()
    plan = await plans_collection.find_one({"code": code})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Find the destination in the plan
    destination = next((d for d in plan["suggested_destinations"] if d["airport_code"] == airport_code), None)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    
    # Update the destination with the new vote
    destination["likes"] += 1

    
    # Update the plan with the new destination
    await plans_collection.update_one(
        {"code": code},
        {
            "$set": {
                "suggested_destinations": plan["suggested_destinations"],
                "users.$[user].has_voted": True
            }
        },
        array_filters=[{"user.email": user.email}]
    )

    return

@router.get("/{code}/suggestions")
async def get_plan_suggestions(code: str, request: Request):
    """
    Get suggestions for a plan
    """
    plans_collection = get_plans_collection()
    plan = await plans_collection.find_one({"code": code})
    plan_data = plan_doc_to_model(plan)
    
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if the plan already has suggestions
    if len(plan_data.suggested_destinations) > 0:
        return await get_suggestions_with_prices(plan_data, request)
    else:
        return await generate_new_suggestions(plan_data, code, request)

async def get_suggestions_with_prices(plan_data, request):
    """
    Get existing suggestions and add prices locally (not stored in DB)
    """
    logger.info(f"Getting existing suggestions with live prices")
    user = await get_current_user_from_request(request)
    
    suggestions_with_prices = []
    
    for destination in plan_data.suggested_destinations:
        # Create a copy of the destination
        destination_dict = destination.model_dump()
        
        # Handle missing image field (might be referenced as photo_url in some places)
        if "image" not in destination_dict or destination_dict["image"] is None:
            if "photo_url" in destination_dict and destination_dict["photo_url"]:
                destination_dict["image"] = destination_dict["photo_url"]
            else:
                destination_dict["image"] = None
        
        # Only fetch price if we have user location
        if user and user.location:
            try:
                price = await AmadeusService.get_cheapest_quotes(
                    origin=user.location,
                    destination=destination.airport_code,
                    outbound_date=plan_data.startDate.strftime("%Y-%m-%d"),
                    inbound_date=plan_data.endDate.strftime("%Y-%m-%d"),
                    participants=len(plan_data.users),
                )
                # Make sure price is a float or explicitly None
                destination_dict["price"] = float(price) if price is not None else None
            except Exception as e:
                logger.error(f"Error getting price for {destination.airport_code}: {str(e)}")
                destination_dict["price"] = None
        else:
            destination_dict["price"] = None
            
        # Create a validated object with all fields properly handled
        try:
            validated_suggestion = DestinationSuggestion(**destination_dict)
            suggestions_with_prices.append(validated_suggestion)
        except Exception as e:
            logger.error(f"Validation error for destination {destination.airport_code}: {str(e)}")
            # Include a minimal valid suggestion if validation fails
            fallback_suggestion = DestinationSuggestion(
                name=destination_dict.get("name", "Unknown"),
                country=destination_dict.get("country", ""),
                city=destination_dict.get("city", ""),
                airport_code=destination_dict.get("airport_code", ""),
                description=destination_dict.get("description", ""),
                price=None,
                image=None
            )
            suggestions_with_prices.append(fallback_suggestion)
    
    return suggestions_with_prices

async def generate_new_suggestions(plan_data, code, request):
    """
    Generate new suggestions for a plan (without storing prices in DB)
    """
    logger.info(f"Generating new suggestions for plan: {code}")
    user = await get_current_user_from_request(request)
    
    # Get intersection of top destinations from all users
    all_top_destinations = [set(u.top_destinations) for u in plan_data.users if hasattr(u, 'top_destinations')]
    
    if all_top_destinations:
        suggestions = list(set.intersection(*all_top_destinations))[:10]
    else:
        suggestions = []
    
    if not suggestions:
        logger.info("No common destinations found, using default suggestions")
        # You could add fallback logic here for when there are no common destinations
        return []
    
    destinations_intersection = []
    destinations_collection = get_destinations_collection()
    
    for destination in suggestions:
        try:
            destination_doc = await destinations_collection.find_one({"airport_code": destination}, {"embedding": 0})
            if not destination_doc:
                logger.warning(f"Destination not found: {destination}")
                continue
                
            destination_doc["id"] = str(destination_doc["_id"])
            del destination_doc["_id"]
            
            # Get destination image if not already available
            if not destination_doc.get("photo_url"):
                try:
                    photo_url = await PexelsService.get_destination_photo(
                        destination_doc.get("city", ""), 
                        destination_doc.get("country", "")
                    )
                    destination_doc["photo_url"] = photo_url
                except Exception as e:
                    logger.error(f"Error getting photo for {destination}: {str(e)}")
                    destination_doc["photo_url"] = None
                    
            destinations_intersection.append(destination_doc)
        except Exception as e:
            logger.error(f"Error processing destination {destination}: {str(e)}")
    
    # Create suggestion objects (without prices) to store in DB
    destination_suggestions_for_db = []
    for destination_doc in destinations_intersection:
        try:
            suggestion = DestinationSuggestion(
                country=destination_doc.get("country", ""),
                city=destination_doc.get("city", ""),
                airport_code=destination_doc.get("airport_code", ""),
                description=destination_doc.get("description", ""),
                photo_url=destination_doc.get("photo_url"),
                image=destination_doc.get("photo_url"),
                likes=destination_doc.get("likes", 0)
            )
            destination_suggestions_for_db.append(suggestion)
        except Exception as e:
            logger.error(f"Error creating suggestion: {str(e)}")
    
    # Update plan with new suggestions (no prices stored)
    plans_collection = get_plans_collection()
    await plans_collection.update_one(
        {"code": code},
        {"$set": {"suggested_destinations": [dest.model_dump() for dest in destination_suggestions_for_db]}}
    )
    
    # Now add prices for the response (not stored in DB)
    destination_suggestions_with_prices = []
    
    if user and user.location:
        for suggestion in destination_suggestions_for_db:
            suggestion_dict = suggestion.model_dump()
            try:
                price = await AmadeusService.get_cheapest_quotes(
                    origin=user.location,
                    destination=suggestion.airport_code,
                    outbound_date=plan_data.startDate.strftime("%Y-%m-%d"),
                    inbound_date=plan_data.endDate.strftime("%Y-%m-%d"),
                    participants=len(plan_data.users),
                )
                # Make sure price is a float or explicitly None
                suggestion_dict["price"] = float(price) if price is not None else None
            except Exception as e:
                logger.error(f"Error getting price for {suggestion.airport_code}: {str(e)}")
                suggestion_dict["price"] = None
                
            destination_suggestions_with_prices.append(DestinationSuggestion(**suggestion_dict))
    else:
        # If no user location, just add None for prices
        for suggestion in destination_suggestions_for_db:
            suggestion_dict = suggestion.model_dump()
            suggestion_dict["price"] = None
            destination_suggestions_with_prices.append(DestinationSuggestion(**suggestion_dict))
    
    return destination_suggestions_with_prices


@router.get("/{code}/podium")
async def finalize_plan(code: str, request: Request):
    """
    Finalize the plan
    """
    plans_collection = get_plans_collection()
    plan_doc = await plans_collection.find_one({"code": code})
    
    # Get the top 3 destinations
    top_destinations = sorted(plan_doc["suggested_destinations"], key=lambda x: x["likes"], reverse=True)[:3]
    
    return top_destinations
    
    
    

