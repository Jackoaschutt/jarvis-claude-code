"""
What JARVIS built, written into the vault.

A Claude session remembers the conversation it is in and nothing else. Restart
the server, or come back tomorrow, and the work is gone — the files are still
on disk but nothing knows why they exist or what they were for.

So every turn that touches a file appends an entry to `Build log.md` in the
vault. That makes the work ordinary memory: the same retrieval that pulls up a
pricing note will pull up "three days ago you built the missed-call responder,
here are the files", because it is just another note.

Deliberately only turns that changed something. A log of every question asked
is noise, and noise in the vault makes every later answer worse.
"""
import datetime
import pathlib
import re

NOTE = "Build log"
# Tools that mean something was actually made or changed. A read or a search
# is JARVIS looking around, not JARVIS building.
BUILDERS = {"write", "edit", "multiedit", "notebookedit", "create_file", "str_replace"}
MAX_ENTRIES = 200


def _looks_like_work(actions):
    return any(a["name"].lower() in BUILDERS for a in actions)


def _target(action):
    """The interesting half of a tool call: the path, or the command."""
    raw = " ".join(str(action.get("input") or "").split())
    path = re.search(r"([~/][\w./ -]+\.\w{1,6})", raw)
    if path:
        return pathlib.Path(path.group(1)).name
    return raw[:70]


def summarise(actions):
    """One line per distinct thing done, in order, without repeats."""
    out = []
    for a in actions:
        name = a["name"]
        if name.lower() in {"read", "glob", "grep", "ls", "todowrite"}:
            continue
        line = f"{name} {_target(a)}".strip()
        if line not in out:
            out.append(line)
    return out[:12]


def record(vault, question, actions, ms=0, today=None):
    """Append one entry. Returns the path written, or None when nothing was built."""
    if not _looks_like_work(actions):
        return None
    vault = pathlib.Path(vault)
    if not vault.is_dir():
        return None
    path = vault / f"{NOTE}.md"
    stamp = (today or datetime.date.today()).isoformat()

    lines = summarise(actions)
    entry = [f"## {stamp} — {' '.join((question or 'untitled').split())[:70]}", ""]
    entry += [f"- {line}" for line in lines]
    if ms:
        entry.append(f"- took {ms // 1000}s")
    entry.append("")

    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = (f"---\ntype: note\nupdated: {stamp}\n---\n\n# {NOTE}\n\n"
                "What JARVIS has actually built, newest first. Written automatically\n"
                "on any turn that changed a file, so it is a record rather than a\n"
                "recollection.\n\n[[Agency]]\n\n")

    # Newest first: the top of the note is what the next question is most
    # likely to be about, and retrieval reads from the top.
    head, sep, body = text.partition("[[Agency]]\n\n")
    if not sep:                      # someone reshaped the note; append instead
        text = text.rstrip() + "\n\n" + "\n".join(entry)
    else:
        text = head + sep + "\n".join(entry) + "\n" + body
    text = re.sub(r"(?m)^updated: .*$", f"updated: {stamp}", text, count=1)

    # Keep it from growing without limit — old builds stop being useful long
    # before they stop taking up room in every prompt.
    blocks = text.split("\n## ")
    if len(blocks) > MAX_ENTRIES:
        text = blocks[0] + "\n## " + "\n## ".join(blocks[1:MAX_ENTRIES])
    path.write_text(text, encoding="utf-8")
    return path
