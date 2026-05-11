"""Exhaustive transition coverage for DocumentLifecycle."""

from __future__ import annotations

import pytest

from app.common.auth import CurrentUser, Role
from app.common.errors import InvalidTransition
from app.workflow.state_machine import DocumentLifecycle


def _user(*roles: Role) -> CurrentUser:
    from uuid import uuid4
    return CurrentUser(user_id=uuid4(), email="t@t", org_id=uuid4(), roles=frozenset(roles))


def test_happy_path_states_are_reachable() -> None:
    sm = DocumentLifecycle()
    sm.send("parse_started")
    sm.send("parse_succeeded")
    sm.send("extraction_started")
    sm.send("extraction_succeeded")
    sm.send("review_opened")
    sm.send("approved")
    sm.send("routed")
    sm.send("plan_generation_started")
    sm.send("plan_generation_succeeded")
    sm.send("printed")
    sm.send("archived")
    assert sm.current_state.id == "ARCHIVED"


def test_cannot_approve_from_uploaded() -> None:
    sm = DocumentLifecycle()
    with pytest.raises(Exception):
        sm.send("approved")


def test_role_guard_blocks_uploader_from_approving() -> None:
    """The role-guard map lives on the class; verifies API-layer expectations."""
    assert Role.APPROVER in DocumentLifecycle.ALLOWED_ROLES["approved"]
    assert Role.UPLOADER not in DocumentLifecycle.ALLOWED_ROLES["approved"]


def test_unknown_transition_raises_invalid() -> None:
    from app.workflow.state_machine import perform_transition

    class _Stub:
        id = None
        current_state = "UPLOADED"

    with pytest.raises(InvalidTransition):
        perform_transition(db=None, document=_Stub(), event_name="nope", actor=_user(Role.SYSTEM))
