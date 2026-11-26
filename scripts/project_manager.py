#!/usr/bin/env python3
"""Initialize, import sources into, inspect, or remove a paper-to-slides project."""

import argparse
import json
import shutil
import stat
from contextlib import contextmanager
from http.client import HTTPException
from pathlib import Path

from prepare_sources import add_source_arguments, prepare, sha256


MARKER = ".paper-to-slides"
FORMAT = "paper-to-slides 1\n"
APPROVAL = ".outline-approved.sha256"


def is_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def project_directory(path):
    if is_link(path):
        raise ValueError(f"Project directory is a link or junction: {path}")
    root = path.resolve(strict=True)
    marker = root / MARKER
    if is_link(marker) or not marker.is_file() or marker.read_text(encoding="utf-8") != FORMAT:
        raise ValueError(f"Expected a project initialized by project_manager.py: {root}")
    return root


def project_path(root, name):
    path = root / name
    if is_link(path):
        raise ValueError(f"Managed path is a link or junction: {path}")
    return path


@contextmanager
def project_lock(root):
    lock = root / ".paper-to-slides.lock"
    try:
        lock.touch(exist_ok=False)
    except FileExistsError as error:
        raise ValueError(f"Project is in use: {lock}") from error
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def init(path):
    if is_link(path):
        raise ValueError(f"Project directory is a link or junction: {path}")
    root = path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with project_lock(root):
        if any(child.name != ".paper-to-slides.lock" for child in root.iterdir()):
            raise ValueError(f"Project directory must be empty: {root}")
        (root / "slides" / "figures").mkdir(parents=True)
        (root / MARKER).write_text(FORMAT, encoding="utf-8")
    return root


def clean_build(root):
    folders = [project_path(root, name) for name in ("build", "build-failed")]
    for folder in folders:
        if folder.exists():
            shutil.rmtree(folder)


def outline_digest(root):
    outline = project_path(root, "outline.md")
    if not outline.is_file():
        raise ValueError("Expected outline.md before recording or checking approval.")
    return sha256(outline)


def require_approved_outline(root):
    digest = outline_digest(root)
    approval = project_path(root, APPROVAL)
    if not approval.is_file() or approval.read_text(encoding="utf-8").strip() != digest:
        raise ValueError("outline.md is not approved in its current version. After explicit approval, run approve-outline.")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "import-sources", "approve-outline", "status", "clean", "delete"):
        subparser = commands.add_parser(command)
        subparser.add_argument("project", type=Path)
        if command == "import-sources":
            add_source_arguments(subparser)
        if command == "delete":
            subparser.add_argument("--yes", action="store_true", help="Confirm deletion of the whole managed project")
        if command == "approve-outline":
            subparser.add_argument("--yes", action="store_true", help="Record explicit approval of the current outline.md")
    args = parser.parse_args()
    try:
        if args.command == "init":
            print(init(args.project))
            return
        root = project_directory(args.project)
        if args.command == "status":
            files = ("sources/manifest.json", "template-source/inventory.json", "template-spec.json",
                     "outline.md", "speaker-notes.md", "slides/main.tex",
                     "build/main.pdf", "build/check.json", "build/main.pptx", "build-failed/check.json")
            status = {name: (root / name).is_file() for name in files}
            try:
                require_approved_outline(root)
                status["outline_approved"] = True
            except ValueError:
                status["outline_approved"] = False
            print(json.dumps(status, indent=2))
            return
        with project_lock(root):
            if args.command == "import-sources":
                args.output_dir = project_path(root, "sources")
                print(prepare(args))
            elif args.command == "approve-outline":
                if not args.yes:
                    raise ValueError("Use approve-outline --yes only after explicit approval of the current outline.")
                approval = project_path(root, APPROVAL)
                approval.write_text(outline_digest(root) + "\n", encoding="utf-8")
                print(approval)
            elif args.command == "clean":
                clean_build(root)
                print(root / "build")
            elif args.yes:
                shutil.rmtree(root)
                print(root)
            else:
                raise ValueError("Use delete --yes to remove the project, including its source archive and authored slides.")
    except (HTTPException, OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Project operation failed: {error}\n")


if __name__ == "__main__":
    main()
