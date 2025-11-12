# backend/schemas/auth.py
"""Authentication and authorization schemas"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

from .common import BaseResponse


class TokenType(str, Enum):
    """Token types"""
    BEARER = "bearer"
    REFRESH = "refresh"


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    remember_me: bool = Field(False, description="Extended session duration")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "doctor@clinic.com",
                "password": "SecurePassword123!",
                "remember_me": False
            }
        }


class LoginResponse(BaseResponse):
    """Login response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: TokenType = Field(TokenType.BEARER, description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Optional[dict] = Field(None, description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Login successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": "STF001",
                    "email": "doctor@clinic.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "roles": ["physician"]
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseResponse):
    """Refresh token response schema"""
    access_token: str = Field(..., description="New JWT access token")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke")
    all_devices: bool = Field(False, description="Logout from all devices")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: EmailStr = Field(..., description="Email address associated with account")


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserPermission(BaseModel):
    """User permission schema"""
    resource: str = Field(..., description="Resource name")
    actions: List[str] = Field(..., description="Allowed actions")
    conditions: Optional[dict] = Field(None, description="Additional conditions")


class UserRole(BaseModel):
    """User role schema"""
    role_id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[str] = Field(default_factory=list, description="Role permissions")
    is_primary: bool = Field(False, description="Whether this is the primary role")


class CurrentUser(BaseModel):
    """Current authenticated user schema"""
    user_id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    is_active: bool = Field(True, description="Whether user is active")
    roles: List[UserRole] = Field(default_factory=list, description="User roles")
    permissions: List[UserPermission] = Field(default_factory=list, description="Computed permissions")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def role_names(self) -> List[str]:
        """Get list of role names"""
        return [role.role_name for role in self.roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return role_name in self.role_names
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""
        for permission in self.permissions:
            if permission.resource == resource and action in permission.actions:
                return True
        return False
    
    def can_prescribe(self) -> bool:
        """Check if user can prescribe medication"""
        prescribing_roles = ["physician", "nurse_practitioner"]
        return any(role in self.role_names for role in prescribing_roles)
    
    def can_admit_patients(self) -> bool:
        """Check if user can admit patients"""
        admitting_roles = ["physician", "nurse_practitioner"]
        return any(role in self.role_names for role in admitting_roles)


class SessionInfo(BaseModel):
    """Session information schema"""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation time")
    expires_at: datetime = Field(..., description="Session expiration time")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    is_active: bool = Field(True, description="Whether session is active")


class TwoFactorAuthRequest(BaseModel):
    """Two-factor authentication request schema"""
    code: str = Field(..., min_length=6, max_length=6, regex="^\\d{6}$", description="6-digit OTP code")
    trust_device: bool = Field(False, description="Trust this device for future logins")


class TwoFactorAuthSetupResponse(BaseResponse):
    """Two-factor authentication setup response"""
    secret: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="QR code image as base64")
    backup_codes: List[str] = Field(..., description="Backup codes for recovery")


class AccessControlRequest(BaseModel):
    """Access control check request"""
    resource: str = Field(..., description="Resource to access")
    action: str = Field(..., description="Action to perform")
    resource_id: Optional[str] = Field(None, description="Specific resource ID")


class AccessControlResponse(BaseResponse):
    """Access control check response"""
    allowed: bool = Field(..., description="Whether access is allowed")
    reason: Optional[str] = Field(None, description="Reason for denial if not allowed")
    required_roles: Optional[List[str]] = Field(None, description="Roles that would grant access")


class ApiKeyRequest(BaseModel):
    """API key generation request"""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days")
    scopes: List[str] = Field(default_factory=list, description="API key scopes")


class ApiKeyResponse(BaseResponse):
    """API key generation response"""
    api_key: str = Field(..., description="Generated API key")
    api_key_id: str = Field(..., description="API key ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "API key generated successfully",
                "api_key": "wc_live_1234567890abcdef",
                "api_key_id": "KEY001",
                "expires_at": "2025-02-01T00:00:00Z"
            }
        }


class SecurityAuditLog(BaseModel):
    """Security audit log schema"""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[str] = Field(None, description="User involved")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    success: bool = Field(..., description="Whether action was successful")
    details: Optional[dict] = Field(None, description="Additional event details")


# Export all schemas
__all__ = [
    "TokenType",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "UserPermission",
    "UserRole",
    "CurrentUser",
    "SessionInfo",
    "TwoFactorAuthRequest",
    "TwoFactorAuthSetupResponse",
    "AccessControlRequest",
    "AccessControlResponse",
    "ApiKeyRequest",
    "ApiKeyResponse",
    "SecurityAuditLog",
]