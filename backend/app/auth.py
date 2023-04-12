"""
Authentication module
"""

from app.database import DB
from passlib.context import CryptContext
from sqlalchemy.orm.exc import NoResultFound

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    """Hashes the password so as not to store
    the user password plain"""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    """
    Verifies the user actual password against the entered password
    """
    return pwd_context.verify(password, hashed_password)


class Auth:
    """
    contains method to handle authentication
    """
    def __init__(self, db: DB):
        """Initializes the class instance"""
        self.db = db

    def register_user(self, email: str, username: str, password: str):
        """
        Adds a new validated user to the database
        """
        try:
            user = self.db.find_user_by(email=email)
            if user:
                raise ValueError(f"User with {email} already exists")
        except NoResultFound:
            hashed_password = hash_password(password)
            return self.db.create_user(
                username=username,
                email=email,
                hashed_password=hashed_password
            )

    def authenticate_user(self, email: str, password: str):
        """
        Authenticates user's login credentials and returns user
        """
        try:
            user = self.db.find_user_by(email=email)
            if not verify_password(password, user.hashed_password):
                raise ValueError("Invalid password")
            return user
        except NoResultFound:
            raise ValueError(f"User with {email} not found")
