import pytest

from app.domain.state import InvalidTransition, ItemState, transition


def test_approved_draft_cannot_skip_to_live() -> None:
    with pytest.raises(InvalidTransition):
        transition(ItemState.APPROVED, ItemState.LIVE)


def test_intake_advances_to_researching() -> None:
    assert transition(ItemState.INTAKE, ItemState.RESEARCHING) is ItemState.RESEARCHING


def test_failed_is_terminal() -> None:
    with pytest.raises(InvalidTransition):
        transition(ItemState.FAILED, ItemState.RESEARCHING)


def test_live_can_return_to_drafting_for_a_revision() -> None:
    assert transition(ItemState.LIVE, ItemState.DRAFTING) is ItemState.DRAFTING
