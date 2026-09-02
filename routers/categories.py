from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.category import Categories, CategoryStatusEnum
from schemas.category_schemas import CategoryCreate, CategoryResponse
from utils.auth_utils import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories Management"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_current_admin)]


@router.get("", response_model=list[CategoryResponse], status_code=status.HTTP_200_OK)
def get_all_active_categories(db: db_dependency):
    """
    PUBLIC ACCESSIBLE: Fetches all active taxonomy records.
    """
    return db.query(Categories).filter(Categories.status == CategoryStatusEnum.active).all()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_category(
        category_request: CategoryCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Inserts a new category and maps the executing admin's ID as creator_id.
    """
    clean_name = category_request.name.strip()
    existing_category = db.query(Categories).filter(Categories.name == clean_name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category named '{clean_name}' already exists."
        )

    db_category = Categories(
        name=clean_name,
        description=category_request.description,
        creator_id=current_admin.get("id")  # 🏛️ Accountability mapping
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
def update_existing_category(
        category_id: int,
        category_request: CategoryCreate,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Modifies existing category parameters and tracks the modifier admin.
    """
    category = db.query(Categories).filter(Categories.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target category profile does not exist."
        )

    category.name = category_request.name.strip()
    category.description = category_request.description

    # 🏛️ Actively uses current_admin to clear the PyCharm highlight warning
    category.updated_by = current_admin.get("id")

    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def soft_delete_category(
        category_id: int,
        current_admin: admin_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Soft-deletes a category safely and records the executing admin's ID.
    """
    category = db.query(Categories).filter(Categories.id == category_id).first()

    if not category or category.status == CategoryStatusEnum.inactive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category record not found or already deactivated."
        )

    # 🏛️ Apply soft-delete switch values using active execution variables
    category.status = CategoryStatusEnum.inactive
    category.updated_by = current_admin.get("id")  # 👈 Clears PyCharm warning flag

    db.add(category)
    db.commit()
    return {"message": f"Category '{category.name}' has been safely soft-deleted."}
