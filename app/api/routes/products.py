"""제품(영수증/보증서 기반 엔티티) 관련 라우터입니다."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.api.dependencies.auth import get_current_user
from app.core.db import get_session
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def _get_product_for_user(session: Session, product_id: int, user_id: int) -> Product | None:
    """현재 사용자 소유의 제품을 조회합니다."""

    result = session.exec(select(Product).where(Product.id == product_id, Product.user_id == user_id))
    return result.first()


@router.get("", response_model=List[ProductRead])
def list_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Product]:
    """현재 사용자 소유의 제품 목록을 반환합니다."""

    result = session.exec(select(Product).where(Product.user_id == current_user.id))
    return result.all()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Product:
    """제품을 생성합니다. user_id는 토큰에서 가져옵니다."""

    product = Product(**payload.dict(), user_id=current_user.id)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Product:
    """단일 제품을 조회합니다."""

    product = _get_product_for_user(session, product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Product:
    """제품 정보를 부분 업데이트합니다."""

    product = _get_product_for_user(session, product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    product.updated_at = datetime.utcnow()

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """제품을 삭제합니다."""

    product = _get_product_for_user(session, product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    session.delete(product)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
