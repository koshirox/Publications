from fastapi import APIRouter, Depends, HTTPException

import crud_categories as categories
from auth import CurrentUser, Db, current_user
from schemas import CategoryIn, CategoryOut, Id

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(current_user)])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Db):
    return categories.list_categories(db)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: Id, db: Db):
    category = categories.get_category(db, category_id)
    if category is None:
        raise HTTPException(404, "Категория не найдена")
    return category


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryIn, db: Db, user: CurrentUser):
    return categories.create_category(db, user.id, data.name)


@router.put("/{category_id}", response_model=CategoryOut)
def change_category(category_id: Id, data: CategoryIn, db: Db, user: CurrentUser):
    get_category(category_id, db)
    return categories.rename_category(db, user.id, category_id, data.name)


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: Id, db: Db, user: CurrentUser):
    get_category(category_id, db)
    categories.delete_category(db, user.id, category_id)
