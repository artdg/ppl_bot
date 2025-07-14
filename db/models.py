from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, select, Float, DateTime, ForeignKey
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0)
    
    @classmethod
    async def get_or_create(cls, user_id: int, username: str):
        async with async_session() as session:
            stmt = select(cls).where(cls.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                return user, False

            user = cls(id=user_id, username=username, balance=100)
            session.add(user)
            await session.commit()
            return user, True
    
class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team1: Mapped[str] = mapped_column(String, nullable=False)
    team2: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="В процессе")
    winner: Mapped[str | None] = mapped_column(String, nullable=True)
    coef_team1: Mapped[float] = mapped_column(Float, default=1.5)
    coef_team2: Mapped[float] = mapped_column(Float, default=1.5)

class Bet(Base):
    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    match_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("matches.id"))
    team: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    coef: Mapped[float] = mapped_column(Float, nullable=False)

    match = relationship("Match")