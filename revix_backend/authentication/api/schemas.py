from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import Field
from pydantic import field_validator

INVALID_EMAIL_MESSAGE = "Enter a valid email address."


class CredentialsSchema(Schema):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip()
        try:
            validate_email(value)
        except ValidationError as error:
            msg = INVALID_EMAIL_MESSAGE
            raise ValueError(msg) from error
        return value


class RegistrationSchema(CredentialsSchema):
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(default="", max_length=255)


class RefreshSchema(Schema):
    refresh_token: str = Field(min_length=40, max_length=200)


class PasswordResetRequestSchema(Schema):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip()
        try:
            validate_email(value)
        except ValidationError as error:
            msg = INVALID_EMAIL_MESSAGE
            raise ValueError(msg) from error
        return value


class PasswordResetConfirmSchema(Schema):
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class UserSchema(Schema):
    id: int
    email: str
    name: str


class TokenPairSchema(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int


class MessageSchema(Schema):
    detail: str
