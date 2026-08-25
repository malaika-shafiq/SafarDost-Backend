from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.category import Categories
from schemas.category_schemas import CategoryCreate, CategoryResponse
from utils.auth_utils import get_current_admin  # 🔒 Security Gate Dependency

router = APIRouter(prefix="/categories", tags=["Categories Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


# ==========================================
# 1. READ ALL ACTIVE CATEGORIES (Public / Traveler Mobile App Access)
# ==========================================
@router.get("", response_model=list[CategoryResponse], status_code=status.HTTP_200_OK)
def get_all_active_categories(db: db_dependency):
    """
    Fetches all active taxonomy records from safardost.db.
    Automatically filters out soft-deleted ('n') records so they vanish from the mobile layout.
    """
    return db.query(Categories).filter(Categories.status == "y").all()


# ==========================================
# 2. CREATE A CATEGORY (🔒 Admin Account Gate Only)
# ==========================================
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_category(
        category_request: CategoryCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Inserts a new category into the lookup cluster.
    Prevents naming duplicates to maintain clean data hygiene across Pakistan points.
    """
    # Defensive Check: Prevent duplicate naming entries
    clean_name = category_request.name.strip()
    existing_category = db.query(Categories).filter(Categories.name == clean_name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category named '{clean_name}' already exists in the system layout."
        )

    db_category = Categories(
        name=clean_name,
        description=category_request.description
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# ==========================================
# 3. UPDATE AN EXISTING CATEGORY (🔒 Admin Account Gate Only)
# ==========================================
@router.put("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
def update_existing_category(
        category_id: int,
        category_request: CategoryCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modifies structural configuration labels.
    Triggers the SQLAlchemy onupdate lifecycle to recalibrate the updated_at column stamp.
    """
    category = db.query(Categories).filter(Categories.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target category profile does not exist."
        )

    # Apply fresh value assignments
    category.name = category_request.name.strip()
    category.description = category_request.description

    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ==========================================
# 4. SOFT-DELETE CATEGORY (🔒 Admin Account Gate Only)
# ==========================================
@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def soft_delete_category(
        category_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Deactivates category tracking blocks by flipping the status switch to 'n'.
    Guards active historic constraints without corrupting connected relational dependency chains.
    """
    category = db.query(Categories).filter(Categories.id == category_id).first()
    if not category or category.status == "n":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category record not found or already deactivated."
        )

    # Execute the requested soft-delete configuration flag
    category.status = "n"

    db.add(category)
    db.commit()
    return {"message": f"Category '{category.name}' has been safely soft-deleted and hidden from mobile views."}
