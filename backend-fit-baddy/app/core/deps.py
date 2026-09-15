from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.auth.models import User

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _UNAUTH
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _UNAUTH
    try:
        uid = int(user_id)
    except ValueError as exc:
        raise _UNAUTH from exc
    user = db.query(User).filter(User.id == uid).first()
    if user is None or not user.is_active:
        raise _UNAUTH
    return user
