from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, SmallInteger, DateTime, func, Date

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "d_user"
    id = Column(Integer, primary_key=True, index=True)
    public_name = Column(String)
    first_name = Column(String)
    email = Column(String)
    password = Column(String)

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"