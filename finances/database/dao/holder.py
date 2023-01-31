from sqlalchemy.ext.asyncio import AsyncSession

from finances.database.dao.user import UserDAO


class DAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    @property
    def user(self):
        return UserDAO(self.session)