"""JWT signing and verification security regression tests using the production HS256 contract."""
import os
from datetime import timedelta

os.environ.setdefault("JWT_SECRET", "test-only-jwt-secret-do-not-use-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import jwt

from app.auth.jwt_handler import ALGORITHM, SECRET_KEY, create_access_token, verify_token


def test_valid_hs256_token_round_trip():
    token = create_access_token({"sub": "17", "token_version": 2})
    assert verify_token(token)["sub"] == "17"
    assert jwt.get_unverified_header(token)["alg"] == ALGORITHM == "HS256"


def test_expired_token_is_rejected():
    token = create_access_token({"sub": "17"}, expires_delta=timedelta(seconds=-60))
    assert verify_token(token) is None


def test_wrong_algorithm_is_rejected():
    token = jwt.encode({"sub": "17"}, SECRET_KEY, algorithm="HS384")
    assert verify_token(token) is None


def test_tampered_token_is_rejected():
    token = create_access_token({"sub": "17"})
    signed, signature = token.rsplit(".", 1)
    changed = ("A" if signature[-1] != "A" else "B")
    assert verify_token(signed + "." + signature[:-1] + changed) is None
