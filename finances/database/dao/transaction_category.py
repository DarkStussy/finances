from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finances.database.dao import BaseDAO
from finances.database.models import TransactionCategory
from finances.exceptions.base import AddModelError, MergeError
from finances.exceptions.transaction import TransactionCategoryExists, \
    TransactionCategoryNotFound
from finances.models import dto


class TransactionCategoryDAO(BaseDAO[TransactionCategory]):
    def __init__(self, session: AsyncSession):
        super().__init__(TransactionCategory, session)

    async def get_by_id(self, category_id: int) -> dto.TransactionCategory:
        category = await self._get_by_id(category_id)
        if category is None or category.deleted:
            raise TransactionCategoryNotFound
        return category.to_dto()

    async def get_all(self, user_dto: dto.User,
                      transaction_type: str | None = None) \
            -> list[dto.TransactionCategory]:
        stmt = select(TransactionCategory).where(
            TransactionCategory.user_id == user_dto.id,
            TransactionCategory.deleted.__eq__(False)
        )
        if transaction_type:
            stmt = stmt.where(TransactionCategory.type == transaction_type)

        result = await self.session.execute(stmt)
        return [transaction_category.to_dto() for transaction_category in
                result.scalars().all()]

    async def create(self, transaction_category_dto: dto.TransactionCategory) \
            -> dto.TransactionCategory:
        try:
            transaction_category = await self._create(transaction_category_dto)
        except AddModelError as e:
            raise TransactionCategoryExists from e
        else:
            return transaction_category.to_dto()

    async def merge(self, category_dto: dto.TransactionCategory) \
            -> dto.TransactionCategory:
        try:
            category = await self._merge(category_dto)
        except MergeError as e:
            raise TransactionCategoryExists from e
        else:
            return category.to_dto()

    async def delete_by_id(self, category_id: int, user_id: UUID) -> int:
        stmt = delete(TransactionCategory) \
            .where(TransactionCategory.id == category_id,
                   TransactionCategory.user_id == user_id) \
            .returning(TransactionCategory.id)
        currency = await self.session.execute(stmt)
        await self.commit()
        return currency.scalar()
