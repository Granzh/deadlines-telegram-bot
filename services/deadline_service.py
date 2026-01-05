import logging
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from db.models import Deadline, User
from db.session import Session
from exceptions import (
    DatabaseError,
    DeadlineCreationError,
    DeadlineDeletionError,
    DeadlineNotFoundError,
    DeadlineUpdateError,
    InvalidDeadlineError,
    InvalidTimezoneError,
    ValidationError,
)
from utils.validation import validate_telegram_user

logger = logging.getLogger(__name__)


class DeadlineService:
    def __init__(self, session_factory: async_sessionmaker = Session):
        self.session_factory = session_factory

    async def _get_or_create_user_by_id(self, session, user_id: int) -> User:
        """Get or create user by internal ID (technical entity for timezone storage)"""
        # Validate user ID
        try:
            validate_telegram_user(
                {
                    "user_id": user_id,
                    "username": None,
                    "first_name": None,
                    "is_bot": False,
                }
            )
        except Exception as e:
            logger.warning(f"Invalid user_id {user_id}: {e}")
            raise ValidationError(f"Invalid user ID: {e}")

        user_query = select(User).where(User.telegram_id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=user_id, timezone="UTC")
            session.add(user)
            logger.info(f"Created user record for telegram_id {user_id}")

        return user

    async def _ensure_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    async def create(self, user_id: int, title: str, dt: datetime) -> Deadline:
        """Create a new deadline for user"""
        dt = await self._ensure_aware(dt)

        now = datetime.now(tz=timezone.utc)

        try:
            # Validate deadline is not in past
            if dt < now:
                raise InvalidDeadlineError(dt)

            # Validate title
            if not title or not title.strip():
                raise ValidationError("Title cannot be empty")

            title = title.strip()

            async with self.session_factory() as session:
                # Get or create user (technical entity for timezone storage)

                deadline = Deadline(user_id=user_id, title=title, deadline_at=dt)
                session.add(deadline)
                await session.commit()
                await session.refresh(deadline)

                logger.info(f"Created deadline {deadline.id} for user {user_id}")
                return deadline

        except (InvalidDeadlineError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to create deadline: {e}")
            raise DeadlineCreationError(f"Failed to create deadline: {e}") from e

    async def get_due(self) -> list[Deadline]:
        """Get all deadlines that are due"""
        try:
            async with self.session_factory() as session:
                q = select(Deadline).where(Deadline.deadline_at <= datetime.now())
                res = await session.execute(q)
                deadlines = res.scalars().all()

                logger.debug(f"Found {len(deadlines)} due deadlines")
                return list(deadlines)

        except Exception as e:
            logger.error(f"Failed to get due deadlines: {e}")
            raise DatabaseError(f"Failed to get due deadlines: {e}") from e

    async def list_for_user(self, user_id: int) -> list[Deadline]:
        """Get all deadlines for a specific user"""
        try:
            async with self.session_factory() as session:
                q = (
                    select(Deadline)
                    .where(Deadline.user_id == user_id)
                    .order_by(Deadline.deadline_at)
                )
                res = await session.execute(q)
                deadlines = res.scalars().all()

                logger.debug(f"Found {len(deadlines)} deadlines for user {user_id}")
                return list(deadlines)

        except Exception as e:
            logger.error(f"Failed to list deadlines for user {user_id}: {e}")
            raise DatabaseError(f"Failed to list deadlines: {e}") from e

    async def delete(self, deadline_id: int, user_id: int) -> bool:
        """Delete a deadline by ID for authorized user"""
        try:
            # Validate user ID
            try:
                validate_telegram_user(
                    {
                        "user_id": user_id,
                        "username": None,
                        "first_name": None,
                        "is_bot": False,
                    }
                )
            except Exception as e:
                logger.warning(f"Invalid user_id {user_id}: {e}")
                raise ValidationError(f"Invalid user ID: {e}")

            async with self.session_factory() as session:
                q = select(Deadline).where(Deadline.id == deadline_id)
                res = await session.execute(q)
                deadline = res.scalar_one_or_none()

                if not deadline:
                    raise DeadlineNotFoundError(deadline_id)

                # Authorization check: user can only delete their own deadlines
                if deadline.user_id != user_id:
                    logger.warning(
                        f"User {user_id} attempted to delete deadline {deadline_id} belonging to user {deadline.user_id}"
                    )
                    raise ValidationError("You can only delete your own deadlines")

                await session.delete(deadline)
                await session.commit()

                logger.info(f"Deleted deadline {deadline_id}")
                return True

        except DeadlineNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete deadline {deadline_id}: {e}")
            raise DeadlineDeletionError(f"Failed to delete deadline: {e}") from e

    async def get_by_id(self, deadline_id: int, user_id: int) -> Optional[Deadline]:
        """Get a deadline by ID for authorized user"""
        try:
            # Validate user ID
            try:
                validate_telegram_user(
                    {
                        "user_id": user_id,
                        "username": None,
                        "first_name": None,
                        "is_bot": False,
                    }
                )
            except Exception as e:
                logger.warning(f"Invalid user_id {user_id}: {e}")
                raise ValidationError(f"Invalid user ID: {e}")

            async with self.session_factory() as session:
                q = select(Deadline).where(Deadline.id == deadline_id)
                res = await session.execute(q)
                deadline = res.scalar_one_or_none()

                if deadline:
                    # Authorization check: user can only access their own deadlines
                    if deadline.user_id != user_id:
                        logger.warning(
                            f"User {user_id} attempted to access deadline {deadline_id} belonging to user {deadline.user_id}"
                        )
                        raise ValidationError("You can only access your own deadlines")
                    logger.debug(f"Found deadline {deadline_id}")
                else:
                    logger.debug(f"Deadline {deadline_id} not found")

                return deadline

        except Exception as e:
            logger.error(f"Failed to get deadline {deadline_id}: {e}")
            raise DatabaseError(f"Failed to get deadline: {e}") from e

    async def get_or_create_user(self, telegram_id: int) -> User:
        """Get or create user by telegram_id"""
        try:
            async with self.session_factory() as session:
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
                logger.info(f"Created user for telegram_id {telegram_id}")
                return user

        except Exception as e:
            logger.error(
                f"Failed to get/create user for telegram_id {telegram_id}: {e}"
            )
            raise DatabaseError(f"Failed to get/create user: {e}") from e

    async def edit_timezone(self, telegram_id: int, timezone: str) -> bool:
        """Edit user's timezone"""
        try:
            if not is_valid_timezone(timezone):
                raise InvalidTimezoneError(timezone)

            async with self.session_factory() as session:
                q = select(User).where(User.telegram_id == telegram_id)
                res = await session.execute(q)
                user = res.scalar_one_or_none()

                if not user:
                    user = User(
                        telegram_id=telegram_id,
                        timezone=timezone,
                    )
                    session.add(user)
                    logger.info(
                        f"Created new user {telegram_id} with timezone {timezone}"
                    )
                else:
                    user.timezone = timezone
                    logger.info(
                        f"Updated timezone for user {telegram_id} to {timezone}"
                    )

                await session.commit()
                return True

        except InvalidTimezoneError:
            raise
        except Exception as e:
            logger.error(f"Failed to edit timezone for user {telegram_id}: {e}")
            raise DatabaseError(f"Failed to edit timezone: {e}") from e

    async def get_timezone_for_user(self, telegram_id: int) -> str:
        """Get user's timezone, return UTC as default"""
        try:
            async with self.session_factory() as session:
                q = select(User).where(User.telegram_id == telegram_id)
                res = await session.execute(q)
                user = res.scalar_one_or_none()

                if not user:
                    logger.debug(
                        f"User {telegram_id} not found, returning UTC timezone"
                    )
                    return "UTC"

                logger.debug(f"Found timezone {user.timezone} for user {telegram_id}")
                return user.timezone

        except Exception as e:
            logger.error(f"Failed to get timezone for user {telegram_id}: {e}")
            raise DatabaseError(f"Failed to get timezone: {e}") from e

    async def update(
        self,
        deadline_id: int,
        title: Optional[str] = None,
        dt: Optional[datetime] = None,
    ) -> bool:
        """Update deadline title and/or deadline time"""
        try:
            # Validate inputs
            if title is not None and not title.strip():
                raise ValidationError("Title cannot be empty")

            if dt is not None:
                dt = await self._ensure_aware(dt)
                if dt < datetime.now(tz=timezone.utc):
                    raise InvalidDeadlineError(dt)

            async with self.session_factory() as session:
                q = select(Deadline).where(Deadline.id == deadline_id)
                res = await session.execute(q)
                deadline = res.scalar_one_or_none()

                if not deadline:
                    raise DeadlineNotFoundError(deadline_id)

                # Update fields
                if title is not None and title.strip():
                    deadline.title = title.strip()
                    logger.debug(f"Updated title for deadline {deadline_id}")

                if dt is not None:
                    deadline.deadline_at = dt
                    logger.debug(f"Updated deadline time for deadline {deadline_id}")

                await session.commit()
                logger.info(f"Updated deadline {deadline_id}")
                return True

        except (DeadlineNotFoundError, ValidationError, InvalidDeadlineError):
            raise
        except Exception as e:
            logger.error(f"Failed to update deadline {deadline_id}: {e}")
            raise DeadlineUpdateError(f"Failed to update deadline: {e}") from e


def is_valid_timezone(timezone: str) -> bool:
    """Check if timezone is valid"""
    try:
        ZoneInfo(timezone)
        return True
    except Exception:
        return False
