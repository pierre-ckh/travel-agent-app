# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import bcrypt
from typing import Optional, Dict, Any
from datetime import datetime

Base = declarative_base()

# SQLAlchemy ORM Model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# DatabaseTool for CrewAI
class DatabaseTool:
    """Database tool for CrewAI to handle user CRUD operations with bcrypt password hashing"""
    
    def __init__(self, database_url: str = "sqlite:///travel_app.db"):
        """
        Initialize the database connection and create tables
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.engine = create_engine(database_url, echo=False, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._active_sessions: Dict[int, Any] = {}  # Track logged-in users
    
    def _get_session(self) -> Session:
        """Create a new database session"""
        return self.SessionLocal()
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def register(self, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            Dictionary with success status and user data or error message
        """
        session = self._get_session()
        try:
            # Check if user already exists
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                return {
                    'success': False,
                    'error': 'User with this email already exists'
                }
            
            # Create new user with hashed password
            hashed_password = self._hash_password(password)
            new_user = User(
                email=email,
                hashed_password=hashed_password
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return {
                'success': True,
                'user': new_user.to_dict(),
                'message': f'User {email} registered successfully'
            }
            
        except IntegrityError as e:
            session.rollback()
            return {
                'success': False,
                'error': f'Database integrity error: {str(e)}'
            }
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }
        finally:
            session.close()
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            Dictionary with success status and user data or error message
        """
        session = self._get_session()
        try:
            # Find user by email
            user = session.query(User).filter_by(email=email).first()
            
            if not user:
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Verify password
            if not self._verify_password(password, user.hashed_password):
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Track logged-in session
            self._active_sessions[user.id] = {
                'user_id': user.id,
                'email': user.email,
                'login_time': datetime.utcnow()
            }
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': f'User {email} logged in successfully',
                'session_id': user.id  # In production, use proper session tokens
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Login failed: {str(e)}'
            }
        finally:
            session.close()
    
    def logout(self, user_id: int) -> Dict[str, Any]:
        """
        Logout a user
        
        Args:
            user_id: ID of the user to logout
            
        Returns:
            Dictionary with success status and message
        """
        try:
            if user_id in self._active_sessions:
                user_email = self._active_sessions[user_id]['email']
                del self._active_sessions[user_id]
                return {
                    'success': True,
                    'message': f'User {user_email} logged out successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'User is not logged in'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Logout failed: {str(e)}'
            }
    
    def unregister(self, email: str, password: str) -> Dict[str, Any]:
        """
        Delete a user account after password verification
        
        Args:
            email: User's email address
            password: Plain text password for verification
            
        Returns:
            Dictionary with success status and message
        """
        session = self._get_session()
        try:
            # Find user by email
            user = session.query(User).filter_by(email=email).first()
            
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Verify password before deletion
            if not self._verify_password(password, user.hashed_password):
                return {
                    'success': False,
                    'error': 'Invalid password'
                }
            
            # Remove from active sessions if logged in
            if user.id in self._active_sessions:
                del self._active_sessions[user.id]
            
            # Delete user
            session.delete(user)
            session.commit()
            
            return {
                'success': True,
                'message': f'User {email} unregistered successfully'
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': f'Unregistration failed: {str(e)}'
            }
        finally:
            session.close()
    
    def get_user(self, user_id: Optional[int] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information by ID or email
        
        Args:
            user_id: User's ID
            email: User's email address
            
        Returns:
            Dictionary with user data or error message
        """
        if not user_id and not email:
            return {
                'success': False,
                'error': 'Either user_id or email must be provided'
            }
        
        session = self._get_session()
        try:
            if user_id:
                user = session.query(User).filter_by(id=user_id).first()
            else:
                user = session.query(User).filter_by(email=email).first()
            
            if user:
                return {
                    'success': True,
                    'user': user.to_dict()
                }
            else:
                return {
                    'success': False,
                    'error': 'User not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get user: {str(e)}'
            }
        finally:
            session.close()
    
    def update_password(self, email: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Update user's password
        
        Args:
            email: User's email address
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Dictionary with success status and message
        """
        session = self._get_session()
        try:
            # Find user by email
            user = session.query(User).filter_by(email=email).first()
            
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Verify old password
            if not self._verify_password(old_password, user.hashed_password):
                return {
                    'success': False,
                    'error': 'Invalid current password'
                }
            
            # Update to new password
            user.hashed_password = self._hash_password(new_password)
            session.commit()
            
            return {
                'success': True,
                'message': f'Password updated successfully for {email}'
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': f'Password update failed: {str(e)}'
            }
        finally:
            session.close()
    
    def is_logged_in(self, user_id: int) -> bool:
        """
        Check if a user is currently logged in
        
        Args:
            user_id: User's ID
            
        Returns:
            True if user is logged in, False otherwise
        """
        return user_id in self._active_sessions
    
    def get_active_sessions(self) -> Dict[int, Any]:
        """
        Get all active user sessions
        
        Returns:
            Dictionary of active sessions
        """
        return self._active_sessions.copy()
    
    # Additional methods needed for FastAPI integration
    def create_user(self, user_data: dict) -> dict:
        """Create a new user - FastAPI compatible method"""
        with self.SessionLocal() as session:
            # Create new user with SQLAlchemy
            new_user = User(
                email=user_data["email"],
                username=user_data.get("username", user_data["email"]),
                hashed_password=user_data["password_hash"],
                full_name=user_data.get("full_name"),
                is_active=user_data.get("is_active", True)
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "created_at": new_user.created_at,
                "is_active": new_user.is_active
            }
    
    def get_user_by_auth(self, username: str = None, email: str = None) -> dict:
        """Get user - FastAPI compatible method"""
        with self.SessionLocal() as session:
            if username:
                user = session.query(User).filter_by(username=username).first()
            elif email:
                user = session.query(User).filter_by(email=email).first()
            else:
                return None
            
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "password_hash": user.hashed_password,
                    "created_at": user.created_at,
                    "is_active": user.is_active
                }
            return None
    
    def update_last_login(self, user_id: int):
        """Update last login timestamp"""
        # This would update the last_login field in the database
        pass
    
    def delete_user(self, user_id: int):
        """Delete user by ID"""
        # This would delete the user from the database
        pass
    
    def save_search_result(self, user_id: int, search_id: str, params: dict, results: dict):
        """Save search results to database"""
        # This would save the search results to the database
        pass
    
    def get_search_result(self, search_id: str, user_id: int):
        """Get search result by ID"""
        # This would retrieve the search result from the database
        return None
    
    def get_user_searches(self, user_id: int, skip: int = 0, limit: int = 20):
        """Get user's search history"""
        # This would retrieve the user's search history from the database
        return []


# Alias for backwards compatibility
Database = DatabaseTool

# Example usage for CrewAI
if __name__ == "__main__":
    # Initialize the database tool
    db_tool = DatabaseTool("postgresql://username:password@localhost/testdb")
    
    # Register a new user
    result = db_tool.register("user@example.com", "SecurePassword123!")
    print("Register:", result)
    
    # Login
    result = db_tool.login("user@example.com", "SecurePassword123!")
    print("Login:", result)
    
    # Get user info
    result = db_tool.get_user(email="user@example.com")
    print("Get User:", result)
    
    # Update password
    result = db_tool.update_password("user@example.com", "SecurePassword123!", "NewPassword456!")
    print("Update Password:", result)
    
    # Logout
    if result.get('success'):
        user_id = 1  # Use actual user_id from login response
        result = db_tool.logout(user_id)
        print("Logout:", result)
    
    # Unregister
    result = db_tool.unregister("user@example.com", "NewPassword456!")
    print("Unregister:", result)