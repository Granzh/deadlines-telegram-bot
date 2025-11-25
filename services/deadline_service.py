from datetime import datetime

from sqlalchemy import select

from db.models import Deadline
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
            q = select(Deadline).where(
                Deadline.deadline_at <= datetime.now(), not Deadline.notified
            )
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

    async def mark_notified(self, deadline_id: int):
        async with Session() as session:
            q = select(Deadline).where(Deadline.id == deadline_id)
            res = await session.execute(q)
            deadline = res.scalar_one()
            deadline.notified = True
            await session.commit()
