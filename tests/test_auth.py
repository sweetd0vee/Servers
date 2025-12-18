from datetime import datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest

import app.auth as auth


class StubStreamlit(SimpleNamespace):
    """Minimal stub to satisfy auth.py logging calls."""

    def __init__(self):
        super().__init__()
        self.session_state = {}

    def error(self, *_, **__):
        return None

    def warning(self, *_, **__):
        return None

    def info(self, *_, **__):
        return None

    def stop(self):
        raise RuntimeError("stop called")


@pytest.fixture
def rsa_keys():
    """Generate ephemeral RSA key pair for JWT signing/verification."""
    private_key = jwt.algorithms.RSAAlgorithm.generate_private_key()
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture(autouse=True)
def patch_streamlit(monkeypatch):
    stub = StubStreamlit()
    monkeypatch.setattr(auth, "st", stub)
    yield stub


def _make_token(private_key, aud="srv-keycloak-client", exp=None):
    exp = exp or (datetime.utcnow() + timedelta(minutes=5))
    payload = {"sub": "123", "aud": aud, "exp": exp}
    return jwt.encode(payload, private_key, algorithm="RS256")


def test_verify_token_accepts_valid_token(monkeypatch, rsa_keys):
    private_key, public_key = rsa_keys
    token = _make_token(private_key)
    monkeypatch.setattr(auth, "get_public_key", lambda: public_key)

    payload = auth.verify_token(token)

    assert payload is not None
    assert payload["sub"] == "123"


def test_verify_token_rejects_expired_token(monkeypatch, rsa_keys):
    private_key, public_key = rsa_keys
    expired = datetime.utcnow() - timedelta(minutes=1)
    token = _make_token(private_key, exp=expired)
    monkeypatch.setattr(auth, "get_public_key", lambda: public_key)

    payload = auth.verify_token(token)

    assert payload is None


def test_has_role_checks_realm_roles(monkeypatch, rsa_keys, patch_streamlit):
    private_key, public_key = rsa_keys
    token = _make_token(private_key)
    monkeypatch.setattr(auth, "get_public_key", lambda: public_key)
    patch_streamlit.session_state["access_token"] = token

    # Force auth path to succeed without hitting Keycloak
    monkeypatch.setattr(auth, "check_auth", lambda: True)
    monkeypatch.setattr(
        auth, "verify_token", lambda _: {"realm_access": {"roles": ["admin", "user"]}}
    )

    assert auth.has_role(["admin"]) is True
    assert auth.has_role(["viewer"]) is False

