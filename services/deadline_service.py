from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from db.models import Deadline, User
from db.session import Session


class DeadlineService:
    async def create(self, user_id: int, title: str, dt):
        async with Session() as session:
            d = Deadline(user_id=user_id, title=title, deadline_at=dt)
            session.add(d)
            await session.commit()
            return d

    async def get_due(self):
        async with Session() as session:
            q = select(Deadline).where(Deadline.deadline_at <= datetime.now())
            res = await session.execute(q)
            return res.scalars().all()

    async def list_for_user(self, user_id: int):
        async with Session() as session:
            q = (
                select(Deadline)
                .where(Deadline.user_id == user_id)
                .order_by(Deadline.deadline_at)
            )
            res = await session.execute(q)
            return res.scalars().all()

    async def delete(self, deadline_id: int):
        async with Session() as session:
            q = select(Deadline).where(Deadline.id == deadline_id)
            res = await session.execute(q)
            deadline = res.scalar_one_or_none()

            if not deadline:
                return False

            await session.delete(deadline)
            await session.commit()
            return True

    async def get_by_id(self, deadline_id: int):
        async with Session() as session:
            q = select(Deadline).where(Deadline.id == deadline_id)
            res = await session.execute(q)
            return res.scalar_one_or_none()

    async def get_or_create_user(self, telegram_id: int) -> User:
        async with Session() as session:
            q = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(q)
            user = res.scalar_one_or_none()

            if user:
                return user

            user = User(
                telegram_id=telegram_id,
                timezone="UTC",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def edit_timezone(self, telegram_id: int, timezone: str) -> bool:
        if not is_valid_timezone(timezone):
            return False

        async with Session() as session:
            q = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(q)
            user = res.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=telegram_id,
                    timezone="UTC",
                )
                session.add(user)

            user.timezone = timezone
            await session.commit()
            return True

    async def get_timezone_for_user(self, telegram_id: int) -> str:
        async with Session() as session:
            q = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(q)
            user = res.scalar_one_or_none()

            if not user:
                return "UTC"

            return user.timezone

    async def update(self, deadline_id: int, title: str = None, dt: datetime = None):
        async with Session() as session:
            q = select(Deadline).where(Deadline.id == deadline_id)
            res = await session.execute(q)
            deadline = res.scalar_one_or_none()

            if not deadline:
                return False

            if title is not None:
                deadline.title = title
            if dt is not None:
                deadline.deadline_at = dt

            await session.commit()
            return True


def is_valid_timezone(timezone: str) -> bool:
    try:
        ZoneInfo(timezone)
        return True
    except Exception:
        return False
