"""
Remove the sample agency from the vault, and nothing else.

    python3 clear_sample_vault.py          # show what would go
    python3 clear_sample_vault.py --yes    # actually remove it

`seed_vault.py` writes a realistic but entirely invented agency — Fairview
Dental, Copper & Rye, Callum Reid, a margin model — so a fresh install has a
graph worth looking at. That is right for a first run and wrong forever after,
because `commands.context_block` puts the matching notes into Claude's system
prompt on every turn. Left in place, JARVIS reasons about your business with
nine fictional clients in its context, and never says so.

The list of what to remove is not written down here. This runs `seed_vault.py`
into a temporary directory and removes exactly the filenames it produces, so
it cannot touch a note the sample never created — your own notes, JARVIS's
`Build log`, anything you wrote in Obsidian — and it stays correct if the
sample vault is ever changed.

Nothing here is lost in any meaningful sense: `python3 seed_vault.py` writes
the same 133 notes again, deterministically.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
SEED = ROOT / "seed_vault.py"


def sample_filenames():
    """Exactly what seed_vault.py creates, by asking it rather than guessing."""
    if not SEED.exists():
        sys.exit(f"  {SEED.name} is not here, so there is no way to tell the\n"
                 f"  sample notes from yours. Refusing to delete anything.")
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        shutil.copy(SEED, work / SEED.name)
        run = subprocess.run([sys.executable, SEED.name], cwd=work,
                             capture_output=True, text=True, timeout=120)
        made = sorted(p.name for p in (work / "vault").glob("*.md"))
        if not made:
            sys.exit(f"  {SEED.name} produced no notes, so the sample list would be\n"
                     f"  empty and nothing could be matched. Refusing to continue.\n"
                     f"  {(run.stderr or run.stdout).strip()[:300]}")
        return set(made)


def main():
    vault = pathlib.Path(sys.argv[sys.argv.index("--vault") + 1]
                         if "--vault" in sys.argv else ROOT / "vault")
    if not vault.is_dir():
        sys.exit(f"  No vault at {vault}")

    sample = sample_filenames()
    here = sorted(p for p in vault.rglob("*.md"))
    doomed = [p for p in here if p.name in sample]
    kept = [p for p in here if p.name not in sample]

    print(f"\n  vault    {vault}")
    print(f"  notes    {len(here)}")
    print(f"  sample   {len(doomed)}  (invented by {SEED.name})")
    print(f"  yours    {len(kept)}\n")

    if not doomed:
        print("  Nothing to remove — no sample notes in this vault.\n")
        return
    for p in kept[:40]:
        print(f"    keep    {p.name}")
    if len(kept) > 40:
        print(f"    keep    … and {len(kept) - 40} more")
    print()

    if "--yes" not in sys.argv:
        print(f"  That is a dry run. To remove the {len(doomed)} sample notes:")
        print(f"      python3 {pathlib.Path(__file__).name} --yes\n")
        return

    for p in doomed:
        p.unlink()
    print(f"  Removed {len(doomed)} sample notes. {len(kept)} of yours left.")
    print(f"  Run /graph in the HUD, or restart, to reload memory from disk.")
    print(f"  To put the sample back:  python3 {SEED.name}\n")


if __name__ == "__main__":
    main()
