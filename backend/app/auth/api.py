from fastapi import APIRouter, Depends, status

from .repository import PostgresAuthRepository
from .schemas import LoginRequest, RefreshTokenRequest, SignupRequest, TokenResponse, UserResponse
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

auth_repository = PostgresAuthRepository()


def get_auth_service() -> AuthService:
    return AuthService(repository=auth_repository)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, service: AuthService = Depends(get_auth_service)) -> UserResponse:
    return await service.signup(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.login(payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.refresh(payload)
