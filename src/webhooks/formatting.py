from datetime import UTC, datetime
from json import dumps

from src.webhooks.constants import (
    CHANGES_KEY,
    ENTRY_KEY,
    MESSAGING_EVENT,
    MESSAGING_KEY,
    UNKNOWN_EVENT,
)


def delivery_messages(payload: dict) -> list[str]:
    messages = []

    for entry in payload.get(ENTRY_KEY, []):
        if not isinstance(entry, dict):
            messages.append(_message(kind=UNKNOWN_EVENT, entry={}, body=entry))
            continue

        events = _events(entry)

        for kind, body in events:
            messages.append(_message(kind=kind, entry=entry, body=body))

    if not messages:
        messages.append(_message(kind=UNKNOWN_EVENT, entry={}, body=payload))

    return messages


def _events(entry):
    events = [
        (change.get('field', UNKNOWN_EVENT), change.get('value', change))
        for change in entry.get(CHANGES_KEY, [])
        if isinstance(change, dict)
    ]
    events += [(MESSAGING_EVENT, item) for item in entry.get(MESSAGING_KEY, [])]

    if events:
        return events

    return [(UNKNOWN_EVENT, entry)]


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
    if not isinstance(timestamp, int):
        return ''

    return datetime.fromtimestamp(timestamp, UTC).isoformat()
