from repositories import UserRepository

from schemas import UserCreateRequest


class UserService:
    def __init__(
            self,
            user_repository: UserRepository,
    ):
        self.user_repository = user_repository

    async def get_all_users(self):
        return await self.user_repository.get_all()

    async def create_user(self, schema: UserCreateRequest):
        user = await self.user_repository.create(schema=schema)
        return user