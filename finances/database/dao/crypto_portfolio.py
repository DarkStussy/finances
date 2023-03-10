from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from finances.database.dao import BaseDAO
from finances.database.models import CryptoPortfolio
from finances.exceptions.base import MergeModelError, AddModelError
from finances.exceptions.crypto_portfolio import CryptoPortfolioExists, \
    CryptoPortfolioNotFound
from finances.models import dto


class CryptoPortfolioDAO(BaseDAO[CryptoPortfolio]):
    def __init__(self, session: AsyncSession):
        super().__init__(CryptoPortfolio, session)

    async def get_by_id(
            self,
            crypto_portfolio_id: UUID
    ) -> dto.CryptoPortfolio:
        crypto_portfolio = await self._get_by_id(crypto_portfolio_id)
        if crypto_portfolio is None:
            raise CryptoPortfolioNotFound
        return crypto_portfolio.to_dto()

    async def get_all(self, user: dto.User) -> list[dto.CryptoPortfolio]:
        result = await self.session.execute(
            select(CryptoPortfolio).where(CryptoPortfolio.user_id == user.id)
        )
        return [crypto_portfolio.to_dto() for crypto_portfolio in
                result.scalars().all()]

    async def create(self, crypto_portfolio_dto: dto.CryptoPortfolio) \
            -> dto.CryptoPortfolio:

        try:
            crypto_portfolio = await self._create(crypto_portfolio_dto)
        except AddModelError as e:
            raise CryptoPortfolioExists from e
        else:
            return crypto_portfolio.to_dto()

    async def merge(self, crypto_portfolio_dto: dto.CryptoPortfolio) \
            -> dto.CryptoPortfolio:
        try:
            crypto_portfolio = await self._merge(crypto_portfolio_dto)
        except MergeModelError as e:
            raise CryptoPortfolioExists from e
        else:
            return crypto_portfolio.to_dto()

    async def delete_by_id(self, crypto_portfolio_id: UUID,
                           user_id: UUID) -> int:
        stmt = delete(CryptoPortfolio) \
            .where(CryptoPortfolio.id == crypto_portfolio_id,
                   CryptoPortfolio.user_id == user_id) \
            .returning(CryptoPortfolio.id)
        currency = await self.session.execute(stmt)
        return currency.scalar()
