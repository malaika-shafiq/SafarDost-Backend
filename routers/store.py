import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

from database import get_db
from utils.auth_utils import get_current_user
from models.store import GearItem, GearOrder
from schemas.store_schemas import GearItemCreate, GearItemResponse, GearOrderCreate, GearOrderResponse

logger = logging.getLogger("safardost.store")

router = APIRouter(prefix="/store", tags=["Travel Gear Marketplace Store Engine"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# ========================================================
# MARKETPLACE CATALOG OPERATIONS (ADMIN CONTROL WRITES)
# ========================================================

@router.post("/items", response_model=GearItemResponse, status_code=status.HTTP_201_CREATED)
def add_marketplace_item(payload: GearItemCreate, db: db_dependency, current_user: user_dependency):
    """
    Administrative Onboarding Endpoint: Restricts catalog item insertions exclusively to admin tokens.
    Processes structured JSON bodies cleanly under minimalist design rules.
    """
    user_id = current_user.get("id")
    user_role = current_user.get("role", "traveler")

    # 🔒 Strict Single-Vendor Administrative perimeter check
    if user_role != "admin":
        logger.warning(f"Unauthorized store manipulation attempt by User ID {user_id} with role '{user_role}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only administrator profiles possess structural capabilities to mutate the store catalog."
        )

    db_item = GearItem(
        name=payload.name.strip(),
        description=payload.description.strip(),
        price_pkr=payload.price_pkr,
        stock_quantity=payload.stock_quantity
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    logger.info(
        f"Admin User {user_id} successfully onboarded new equipment: '{db_item.name}' (Stock: {db_item.stock_quantity})")
    return db_item


@router.get("/items", response_model=List[GearItemResponse], status_code=status.HTTP_200_OK)
def list_available_gear(db: db_dependency, query: Optional[str] = None):
    """
    Public Browsing Endpoint: Streams the retail catalog out to the client screen.
    Supports case-insensitive partial keyword wildcard searching natively via database indexes.
    """
    base_query = db.query(GearItem)
    if query:
        # High-speed SQL case-insensitive search loop
        base_query = base_query.filter(GearItem.name.ilike(f"%{query.strip()}%"))
    return base_query.all()


# ========================================================
# REVENUE TRANSACTION BUY OPERATIONS (TRAVELERS ACCESS CHECKOUT)
# ========================================================

@router.post("/buy", response_model=GearOrderResponse, status_code=status.HTTP_201_CREATED)
def purchase_gear_item(payload: GearOrderCreate, db: db_dependency, current_user: user_dependency):
    """
    Secure Traveler Checkout Pipeline: Processes clean JSON payloads, verifies
    warehouse stock quantities, and applies real-time inventory deductions securely.
    """
    user_id = current_user.get("id")
    logger.info(f"User {user_id} initiated a marketplace store purchase for item ID {payload.gear_item_id}")

    # 1. Fetch item entry from database, verify structural existence
    item = db.query(GearItem).filter(GearItem.id == payload.gear_item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target inventory item entry could not be located inside catalog databases."
        )

    # 2. Real-Time Boundary Check: Prevent overselling and negative inventory conditions
    if item.stock_quantity < payload.purchase_quantity:
        logger.warning(f"Checkout transaction interrupted for User {user_id}: Insufficient inventory balance.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction Interrupted: Insufficient warehouse balance reserves."
        )

    # 3. Dynamic Price Allocation: Compute pricing metrics securely on the server side
    computed_invoice_cost = float(item.price_pkr * payload.purchase_quantity)

    # 4. Automated Inventory Logic: Atomically subtract purchased units directly from table cell
    item.stock_quantity = item.stock_quantity - payload.purchase_quantity

    # 5. Commit permanent order receipt down into your persistent ledger table row columns
    db_order = GearOrder(
        user_id=user_id,
        gear_item_id=payload.gear_item_id,
        purchase_quantity=payload.purchase_quantity,
        total_invoice_pkr=computed_invoice_cost
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    logger.info(f"E-commerce transaction successful! Order ID {db_order.id} generated. Warehouse stock updated.")
    return db_order
