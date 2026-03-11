import os
import mimetypes
from pathlib import Path
from datetime import datetime

# ----------------------------
# CONFIG
# ----------------------------

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".mypy_cache",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".log",
    ".lock",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".db",
}

MAX_FILE_SIZE_MB = 2  # Avoid dumping huge files


# ----------------------------
# UTILITIES
# ----------------------------

def generate_tree(root_path: Path) -> str:
    tree_lines = []

    def walk(dir_path: Path, prefix=""):
        entries = sorted(dir_path.iterdir(), key=lambda x: x.name)

        filtered_entries = [
            e for e in entries
            if not should_exclude(e)
        ]

        for index, entry in enumerate(filtered_entries):
            connector = "└── " if index == len(filtered_entries) - 1 else "├── "
            tree_lines.append(prefix + connector + entry.name)

            if entry.is_dir():
                extension = "    " if index == len(filtered_entries) - 1 else "│   "
                walk(entry, prefix + extension)

    tree_lines.append(root_path.name)
    walk(root_path)
    return "\n".join(tree_lines)


def should_exclude(path: Path) -> bool:
    # Ignore virtualenv and other excluded dirs
    if path.name in EXCLUDE_DIRS:
        return True

    # Ignore extensions
    if path.suffix in EXCLUDE_EXTENSIONS:
        return True

    # Ignore __init__.py specifically
    if path.name == "__init__.py" and path.stat().st_size < 10:
        return True

    return False


def is_text_file(path: Path) -> bool:
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type is None or mime_type.startswith("text")


def get_file_metadata(path: Path, root: Path) -> str:
    relative_path = path.relative_to(root)

    return f"""============================================================
FILE: {relative_path.name}
RELATIVE_PATH: {relative_path}
============================================================
"""


def collect_files(root_path: Path) -> str:
    output = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # 🔥 THIS IS THE IMPORTANT PART
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS
        ]

        for filename in filenames:
            path = Path(dirpath) / filename

            if should_exclude(path):
                continue

            if path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                continue

            if not is_text_file(path):
                continue

            try:
                metadata = get_file_metadata(path, root_path)
                content = path.read_text(encoding="utf-8", errors="ignore")
                output.append(metadata + "\n" + content + "\n")
            except Exception as e:
                output.append(f"\n# Could not read file: {path}\n# Error: {e}\n")

    return "\n----------------------------------------\n".join(output)

# ----------------------------
# MAIN
# ----------------------------

def generate_prompt(project_root: str, output_file="prompt.txt"):
    root_path = Path(project_root).resolve()

    tree = generate_tree(root_path)
    files_content = collect_files(root_path)

    final_output = f"""
#############################
PROJECT STRUCTURE
#############################

{tree}

#############################
FILES
#############################

{files_content}
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_output.strip())

    print(f"\n✅ Prompt file generated: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate LLM-ready project prompt.")
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Root path of project",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="prompt.txt",
        help="Output prompt file name",
    )

    args = parser.parse_args()

    generate_prompt(args.path, args.output)