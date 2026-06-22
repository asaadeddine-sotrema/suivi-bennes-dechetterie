import logging
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.security import verify_password, create_access_token, decode_access_token, hash_password
from backend import models, schemas

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> models.User:
    """Dépendance : exige un jeton JWT valide et renvoie l'utilisateur actif."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré")

    user = db.query(models.User).filter_by(id=int(payload.get("sub", 0)), actif=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable ou désactivé")
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Dépendance : restreint l'accès aux administrateurs."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Action réservée aux administrateurs")
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginPayload, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.username, actif=True).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiant ou mot de passe incorrect")
    token = create_access_token(user.id, user.role)
    return schemas.TokenResponse(access_token=token, user=schemas.UserSchema.model_validate(user))


@router.get("/me", response_model=schemas.UserSchema)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[schemas.UserSchema])
def list_users(_: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.username).all()


@router.post("/users", response_model=schemas.UserSchema, status_code=201)
def create_user(payload: schemas.UserCreate, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    if payload.role not in ("admin", "operateur"):
        raise HTTPException(status_code=422, detail="Rôle invalide (admin ou operateur)")
    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Le mot de passe doit faire au moins 6 caractères")
    if db.query(models.User).filter_by(username=payload.username).first():
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur existe déjà")
    user = models.User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=200)
def delete_user(user_id: int, current: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
    return {"supprime": True}
