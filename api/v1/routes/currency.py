from fastapi import Depends, APIRouter, HTTPException, Query
from starlette import status

from api.v1.dependencies import get_current_user, dao_provider
from api.v1.models.enum.currency_type import CurrencyType
from api.v1.models.request.currency import CurrencyCreate, CurrencyChange
from api.v1.models.response.currency import CurrencyResponse
from finances.database.dao import DAO
from finances.exceptions.currency import CurrencyNotFound, CurrencyCantBeBase
from finances.models import dto
from finances.services.currency import add_new_currency, change_currency, \
    delete_currency, set_base_currency, get_currency_by_id


async def get_currency_by_id_route(
        currency_id: int,
        current_user: dto.User = Depends(get_current_user),
        dao: DAO = Depends(dao_provider)) -> CurrencyResponse:
    try:
        currency_dto = await get_currency_by_id(currency_id, current_user,
                                                dao.currency)
    except CurrencyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=e.message)
    else:
        return CurrencyResponse.from_dto(currency_dto)


async def add_new_currency_route(
        currency: CurrencyCreate,
        current_user: dto.User = Depends(get_current_user),
        dao: DAO = Depends(dao_provider)) -> CurrencyResponse:
    created_currency = await add_new_currency(currency.dict(), current_user,
                                              dao.currency)
    return CurrencyResponse.from_dto(created_currency)


async def change_currency_route(
        currency: CurrencyChange,
        current_user: dto.User = Depends(
            get_current_user),
        dao: DAO = Depends(dao_provider)) -> CurrencyResponse:
    try:
        currency = await change_currency(currency.dict(), current_user,
                                         dao.currency)
    except CurrencyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=e.message)

    return CurrencyResponse.from_dto(currency)


async def delete_currency_route(
        currency_id: int,
        current_user: dto.User = Depends(
            get_current_user),
        dao: DAO = Depends(dao_provider)):
    try:
        await delete_currency(currency_id, current_user,
                              dao.currency)
    except CurrencyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=e.message)
    raise HTTPException(status_code=status.HTTP_200_OK)


async def get_currencies_route(
        currency_type: CurrencyType = Query(default=CurrencyType.ALL),
        code: str = Query(default=None),
        current_user: dto.User = Depends(get_current_user),
        dao: DAO = Depends(dao_provider)) -> list[CurrencyResponse]:
    if currency_type == CurrencyType.CUSTOM:
        return await dao.currency.get_all(code=code, user_id=current_user.id)
    elif currency_type == CurrencyType.DEFAULT:
        return await dao.currency.get_all(code=code)
    elif currency_type == CurrencyType.ALL:
        return await dao.currency.get_all(code, current_user.id, True)


async def get_base_currency_route(
        user: dto.User = Depends(get_current_user),
        dao: DAO = Depends(dao_provider),
) -> CurrencyResponse:
    currency = await dao.user.get_base_currency(user)
    if currency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Base currency not set')
    return CurrencyResponse.from_dto(currency)


async def set_base_currency_route(
        currency_id: int,
        user: dto.User = Depends(get_current_user),
        dao: DAO = Depends(dao_provider),
):
    try:
        await set_base_currency(currency_id, user, dao)
    except CurrencyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=e.message)
    except CurrencyCantBeBase as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=e.message)
    else:
        raise HTTPException(status_code=status.HTTP_200_OK)


def get_currency_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route('/add', add_new_currency_route,
                         methods=['POST'])
    router.add_api_route('/change', change_currency_route,
                         methods=['PUT'])
    router.add_api_route('/all', get_currencies_route,
                         methods=['GET'])
    router.add_api_route('/baseCurrency', get_base_currency_route,
                         methods=['GET'])
    router.add_api_route('/baseCurrency/{currency_id}',
                         set_base_currency_route,
                         methods=['PUT'])
    router.add_api_route('/{currency_id}', delete_currency_route,
                         methods=['DELETE'])
    router.add_api_route('/{currency_id}', get_currency_by_id_route,
                         methods=['GET'])
    return router
