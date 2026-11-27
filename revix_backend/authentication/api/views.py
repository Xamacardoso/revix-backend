from http import HTTPStatus
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils import timezone
from ninja import Router
from ninja import Status

from revix_backend.authentication.api.auth import session_bearer_auth
from revix_backend.authentication.api.schemas import CredentialsSchema
from revix_backend.authentication.api.schemas import MessageSchema
from revix_backend.authentication.api.schemas import PasswordResetConfirmSchema
from revix_backend.authentication.api.schemas import PasswordResetRequestSchema
from revix_backend.authentication.api.schemas import RefreshSchema
from revix_backend.authentication.api.schemas import RegistrationSchema
from revix_backend.authentication.api.schemas import TokenPairSchema
from revix_backend.authentication.api.schemas import UserSchema
from revix_backend.authentication.providers.password import EmailAlreadyRegisteredError
from revix_backend.authentication.providers.registry import providers
from revix_backend.authentication.rate_limits import is_rate_limited
from revix_backend.authentication.services import create_session
from revix_backend.authentication.services import request_password_reset
from revix_backend.authentication.services import reset_password
from revix_backend.authentication.services import rotate_session

if TYPE_CHECKING:
    from django.http import HttpRequest

    from revix_backend.authentication.models import AuthSession

router = Router(auth=None, tags=["authentication"])


def _django_request(request) -> HttpRequest:
    return getattr(request, "_request", request)


def _limited(request, action: str, subject: str | None = None):
    if is_rate_limited(_django_request(request), action, subject=subject):
        return Status(
            HTTPStatus.TOO_MANY_REQUESTS,
            {"detail": "Too many requests. Try again later."},
        )
    return None


def _token_response(session: AuthSession, access_token: str, refresh_token: str):
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": max(
            0,
            int((session.access_expires_at - timezone.now()).total_seconds()),
        ),
    }


@router.post(
    "/register",
    response={
        201: TokenPairSchema,
        409: MessageSchema,
        422: MessageSchema,
        429: MessageSchema,
    },
)
def register(request, data: RegistrationSchema):
    limited = _limited(request, "register", data.email)
    if limited:
        return limited
    provider = providers.get_password()
    try:
        user = provider.register(
            email=data.email,
            password=data.password,
            name=data.name,
        )
    except EmailAlreadyRegisteredError:
        return Status(
            HTTPStatus.CONFLICT,
            {"detail": "An account with this email already exists."},
        )
    except ValidationError as error:
        return Status(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            {"detail": "; ".join(error.messages)},
        )
    session, access_token, refresh_token = create_session(user)
    return Status(
        HTTPStatus.CREATED,
        _token_response(session, access_token, refresh_token),
    )


@router.post(
    "/login",
    response={200: TokenPairSchema, 401: MessageSchema, 429: MessageSchema},
)
def login(request, data: CredentialsSchema):
    limited = _limited(request, "login", data.email)
    if limited:
        return limited
    provider = providers.get("password")
    user = provider.authenticate({"email": data.email, "password": data.password})
    if user is None:
        return Status(HTTPStatus.UNAUTHORIZED, {"detail": "Invalid email or password."})
    session, access_token, refresh_token = create_session(user)
    return Status(HTTPStatus.OK, _token_response(session, access_token, refresh_token))


@router.post(
    "/refresh",
    response={200: TokenPairSchema, 401: MessageSchema, 429: MessageSchema},
)
def refresh(request, data: RefreshSchema):
    limited = _limited(request, "refresh")
    if limited:
        return limited
    rotated = rotate_session(data.refresh_token)
    if rotated is None:
        return Status(
            HTTPStatus.UNAUTHORIZED,
            {"detail": "Invalid or expired refresh token."},
        )
    session, access_token, refresh_token = rotated
    return Status(HTTPStatus.OK, _token_response(session, access_token, refresh_token))


@router.post("/logout", auth=session_bearer_auth, response={204: None})
def logout(request):
    session = request.auth
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at", "updated_at"])
    return Status(HTTPStatus.NO_CONTENT, None)


@router.get("/me", auth=session_bearer_auth, response=UserSchema)
def current_user(request):
    return request.auth.user


@router.post(
    "/password-reset/request",
    response={202: MessageSchema, 429: MessageSchema},
)
def password_reset_request(request, data: PasswordResetRequestSchema):
    limited = _limited(request, "password_reset_request", data.email)
    if limited:
        return limited
    request_password_reset(data.email)
    return Status(
        HTTPStatus.ACCEPTED,
        {
            "detail": (
                "If an account matches that email, recovery instructions will be sent."
            ),
        },
    )


@router.post(
    "/password-reset/confirm",
    response={
        200: MessageSchema,
        400: MessageSchema,
        422: MessageSchema,
        429: MessageSchema,
    },
)
def password_reset_confirm(request, data: PasswordResetConfirmSchema):
    limited = _limited(request, "password_reset_confirm", data.token)
    if limited:
        return limited
    try:
        completed = reset_password(token=data.token, new_password=data.new_password)
    except ValidationError as error:
        return Status(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            {"detail": "; ".join(error.messages)},
        )
    if not completed:
        return Status(
            HTTPStatus.BAD_REQUEST,
            {"detail": "Invalid or expired recovery token."},
        )
    return Status(HTTPStatus.OK, {"detail": "Password updated. Please sign in again."})
