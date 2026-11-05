"""Single-writer pilot. Persist pending before issuing the external create."""
import sqlite3
from pathlib import Path


def reserve(directory, label, summary, jira):
    root = Path(directory)
    if not (root / ".pilot-state-volume").is_file():
        raise RuntimeError("Missing persistent writer volume or provisioning marker")
    db = sqlite3.connect(root/"reservations.sqlite3", timeout=30)
    try:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS reservation(label TEXT PRIMARY KEY, issue TEXT)")
            fresh = db.execute("INSERT OR IGNORE INTO reservation VALUES (?,NULL)", (label,)).rowcount
        key, = db.execute("SELECT issue FROM reservation WHERE label=?", (label,)).fetchone()
        if key is None:
            key = jira.search(label)
            if not key:
                if not fresh:
                    raise RuntimeError(f"Unconfirmed Jira creation for {label}; reconcile before retry")
                key = jira.create(label, summary)
            jira.verify(key,label)
            with db:
                db.execute("UPDATE reservation SET issue=? WHERE label=?", (key,label))
        else:
            jira.verify(key,label)
        return key
    finally:
        db.close()
