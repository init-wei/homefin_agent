from fastapi import APIRouter, Depends, Query

from application.dto.transaction import (
    SharedExpenseUpdateRequest,
    TransactionCategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionRead,
    TransactionSearchParams,
)
from application.services.transaction_app_service import TransactionAppService
from apps.api.dependencies import get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionRead)
def create_manual_transaction(
    request: TransactionCreateRequest,
    service: TransactionAppService = Depends(get_transaction_service),
) -> TransactionRead:
    return TransactionRead.model_validate(service.create_manual_transaction(request))


@router.get("", response_model=list[TransactionRead])
def search_transactions(
    household_id: str = Query(...),
    month: str | None = Query(None),
    member_id: str | None = Query(None),
    category_id: str | None = Query(None),
    account_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    service: TransactionAppService = Depends(get_transaction_service),
) -> list[TransactionRead]:
    params = TransactionSearchParams(
        household_id=household_id,
        month=month,
        member_id=member_id,
        category_id=category_id,
        account_id=account_id,
        limit=limit,
    )
    return [TransactionRead.model_validate(txn) for txn in service.search_transactions(params)]


@router.patch("/{transaction_id}/category", response_model=TransactionRead)
def update_transaction_category(
    transaction_id: str,
    request: TransactionCategoryUpdateRequest,
    service: TransactionAppService = Depends(get_transaction_service),
) -> TransactionRead:
    return TransactionRead.model_validate(service.update_transaction_category(transaction_id=transaction_id, request=request))


@router.patch("/{transaction_id}/shared", response_model=TransactionRead)
def mark_shared_expense(
    transaction_id: str,
    request: SharedExpenseUpdateRequest,
    service: TransactionAppService = Depends(get_transaction_service),
) -> TransactionRead:
    return TransactionRead.model_validate(service.mark_shared_expense(transaction_id=transaction_id, request=request))

