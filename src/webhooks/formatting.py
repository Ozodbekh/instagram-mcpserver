from datetime import UTC, datetime
from json import dumps

from src.webhooks.constants import (
    CHANGES_KEY,
    ENTRY_KEY,
    MESSAGING_EVENT,
    MESSAGING_KEY,
    MILLISECOND_THRESHOLD,
    MILLISECONDS_PER_SECOND,
    UNKNOWN_EVENT,
)


def delivery_messages(payload: dict) -> list[str]:
    entries = payload.get(ENTRY_KEY)

    if not isinstance(entries, list) or not entries:
        return [_message(kind=UNKNOWN_EVENT, entry={}, body=payload)]

    messages = []

    for entry in entries:
        if not isinstance(entry, dict):
            messages.append(_message(kind=UNKNOWN_EVENT, entry={}, body=entry))
            continue

        for kind, body in _events(entry):
            messages.append(_message(kind=kind, entry=entry, body=body))

    return messages


def _events(entry):
    events = [
        (change.get('field', UNKNOWN_EVENT), change.get('value', change))
        for change in _listed(entry, CHANGES_KEY)
        if isinstance(change, dict)
    ]
    events += [(MESSAGING_EVENT, item) for item in _listed(entry, MESSAGING_KEY)]

    return events or [(UNKNOWN_EVENT, entry)]


def _listed(entry, key):
    items = entry.get(key)

    return items if isinstance(items, list) else []


def _message(*, kind, entry, body):
    header = [f'Instagram · {kind}']

    account = entry.get('id', '')
    if account:
        header.append(f'account: {account}')

    moment = _moment(entry.get('time'))
    if moment:
        header.append(f'time: {moment}')

    return '\n'.join(header) + '\n\n' + dumps(body, indent=2, ensure_ascii=False, sort_keys=True)


def _moment(timestamp):
    if not isinstance(timestamp, int) or isinstance(timestamp, bool):
        return ''

    if abs(timestamp) >= MILLISECOND_THRESHOLD:
        timestamp = timestamp / MILLISECONDS_PER_SECOND

    try:
        return datetime.fromtimestamp(timestamp, UTC).isoformat()
    except (OSError, OverflowError, ValueError):
        return ''
