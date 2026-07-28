from enum import StrEnum


class ItemState(StrEnum):
    INTAKE = "INTAKE"
    RESEARCHING = "RESEARCHING"
    NEEDS_INPUT = "NEEDS_INPUT"
    DRAFTING = "DRAFTING"
    DRAFT_READY = "DRAFT_READY"
    EBAY_DRAFTED = "EBAY_DRAFTED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHING = "PUBLISHING"
    LIVE = "LIVE"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    FAILED = "FAILED"


class InvalidTransition(ValueError):
    pass


_ALLOWED: dict[ItemState, set[ItemState]] = {
    ItemState.INTAKE: {ItemState.RESEARCHING},
    ItemState.RESEARCHING: {
        ItemState.NEEDS_INPUT,
        ItemState.DRAFTING,
        ItemState.ACTION_REQUIRED,
    },
    ItemState.NEEDS_INPUT: {ItemState.RESEARCHING},
    ItemState.DRAFTING: {ItemState.DRAFT_READY, ItemState.ACTION_REQUIRED},
    ItemState.DRAFT_READY: {ItemState.EBAY_DRAFTED},
    ItemState.EBAY_DRAFTED: {ItemState.AWAITING_APPROVAL},
    ItemState.AWAITING_APPROVAL: {ItemState.APPROVED, ItemState.DRAFTING},
    ItemState.APPROVED: {ItemState.PUBLISHING, ItemState.AWAITING_APPROVAL},
    ItemState.PUBLISHING: {ItemState.LIVE, ItemState.ACTION_REQUIRED},
    ItemState.LIVE: {ItemState.DRAFTING, ItemState.ACTION_REQUIRED},
    ItemState.ACTION_REQUIRED: {
        ItemState.RESEARCHING,
        ItemState.DRAFTING,
        ItemState.PUBLISHING,
    },
    ItemState.FAILED: set(),
}


def transition(current: ItemState, target: ItemState) -> ItemState:
    if target not in _ALLOWED[current]:
        raise InvalidTransition(f"{current} -> {target} is not allowed")
    return target
