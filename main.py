import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ACTIVE_MODEL
from crew.job_crew import build_and_run_crew
from utils.file_loader import load_resume

console = Console()


def _find_resume_files() -> list[Path]:

    search_dirs = [Path("data"), Path("data/sample"), Path(".")]
    found = []
    for folder in search_dirs:
        if folder.exists():
            for ext in ("*.txt", "*.pdf"):
                found.extend(folder.glob(ext))

    # De-duplicate and sort, keeping paths relative and readable
    seen = set()
    unique = []
    for p in sorted(found):
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _validate_resume_content(text: str, path: str) -> tuple[bool, str]:

    if not text or not text.strip():
        return False, "The file is empty. Please provide a resume with content."

    word_count = len(text.split())
    if word_count < 30:
        return False, (
            f"The file only has {word_count} words — too short to be a resume. "
            "Make sure you selected the right file."
        )

    if word_count > 15_000:
        return False, (
            f"The file has {word_count:,} words — unusually long. "
            "Please provide just your resume (not a full document or book)."
        )

    # Warn if it looks like raw binary / garbled text (lots of non-printable chars)
    non_printable = sum(1 for c in text if not c.isprintable() and c not in "\n\r\t")
    if non_printable > len(text) * 0.05:
        return False, (
            "The file contains many unreadable characters — it may be corrupted "
            "or a scanned image PDF (which has no selectable text). "
            "Try exporting your resume as a text-based PDF or .txt file."
        )

    return True, ""


def _show_resume_preview(text: str):

    lines = [line for line in text.strip().splitlines() if line.strip()]
    preview_lines = lines[:10]
    preview = "\n".join(preview_lines)
    if len(lines) > 10:
        preview += f"\n[dim]... ({len(lines) - 10} more lines)[/dim]"


def get_resume_input() -> str:

    console.print(Rule("Load Your Resume"))

    # ── Show discovered files so the user doesn't have to guess paths ──
    available = _find_resume_files()
    if available:
        console.print("\n [bold]Resume files found on your system:[/bold]")
        for i, p in enumerate(available, 1):
            size_kb = p.stat().st_size // 1024
            console.print(f"   [{i}] {p}  [dim]({size_kb} KB)[/dim]")

    SUPPORTED_EXTENSIONS = {".txt", ".pdf"}
    MAX_RETRIES = 5
    attempt = 0

    while attempt < MAX_RETRIES:
        attempt += 1

        raw = Prompt.ask("Enter file path (or number from list above)")

        if available and raw.strip().isdigit():
            idx = int(raw.strip()) - 1
            if 0 <= idx < len(available):
                raw = str(available[idx])
                console.print(f"   → Selected: [bold]{raw}[/bold]")
            else:
                console.print(
                    f"[yellow] Number {raw} is out of range "
                    f"(1–{len(available)}). Try again.[/yellow]\n"
                )
                continue

        file_path = raw.strip().strip("\"'")

        suffix = Path(file_path).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            console.print(f"[red]❌ Unsupported file type: '{suffix}'[/red]\n")
            continue

        try:
            resume_text = load_resume(file_path)
        except FileNotFoundError:
            console.print(f" File not found:[/red] [bold]{file_path}[/bold]")

            if attempt >= 2 and available:
                console.print(
                    "Hint: try typing just the number from the list above "
                    f"(e.g. [bold]1[/bold] for {available[0]})[/yellow]"
                )
            console.print()
            continue
        except PermissionError:
            console.print(
                f"Permission denied:[/red] [bold]{file_path}[/bold]\n"
                "   The file exists but can't be read. "
                "Check that it isn't open in another application.\n"
            )
            continue
        except Exception as e:
            console.print(f"Unexpected error loading file:[/red] {e}\n")
            continue

        is_valid, error_msg = _validate_resume_content(resume_text, file_path)
        if not is_valid:
            console.print(f"File loaded but failed validation:[/red]\n   {error_msg}\n")
            continue

        word_count = len(resume_text.split())
        char_count = len(resume_text)
        console.print(
            f"\n [bold green]File loaded:[/bold green] [bold]{file_path}[/bold]  "
            f"[dim]({word_count:,} words · {char_count:,} chars)[/dim]"
        )
        _show_resume_preview(resume_text)

        confirm = Prompt.ask(
            "Does this look like your resume?",
            choices=["y", "n"],
            default="y",
        )
        if confirm.lower() == "y":
            console.print()
            return resume_text
        else:
            console.print(" No problem — let's try a different file.[/yellow]\n")
            attempt = 0
            continue

    console.print(
        Panel(
            "Could not load a valid resume after several attempts.\n\n"
            "Things to check:\n"
            "  • Is the file in the [bold]data/[/bold] folder?\n"
            "  • Is it a [bold].txt[/bold] or [bold].pdf[/bold] file?\n"
            "  • For PDFs: make sure text is selectable (not a scanned image)\n"
            "  • Try copy-pasting your resume into [bold]data/resume.txt[/bold]\n\n"
            "Run [bold]python main.py[/bold] again when ready.",
            title="❌ Too many failed attempts",
            border_style="red",
        )
    )
    sys.exit(1)


def get_jd_input() -> str:

    console.print(Rule("Paste the Job Description"))
    console.print(
        "Paste the full job description below.\n"
        "When done, type [bold]END[/bold] on a new line and press Enter.\n"
    )

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break

    jd_text = "\n".join(lines).strip()

    if not jd_text:
        console.print("No job description entered. Please try again.[/red]")
        return get_jd_input()

    console.print(f"\n Job description received ({len(jd_text)} characters)\n")
    return jd_text


def display_results(outputs: dict):

    console.print()
    console.print(Rule("Results Summary"))
    console.print()

    report_path = outputs.get("report_path", "")
    if report_path:
        console.print(
            Panel(
                f" [bold green]Full report saved![/bold green]\n\n"
                f"Location: [bold]{report_path}[/bold]\n\n"
                f"The report includes:\n"
                f"  • Resume Analysis\n"
                f"  • Job Description Breakdown\n"
                f"  • Skills Gap Analysis with Match Score\n"
                f"  • Free Learning Resources & 30-Day Sprint\n"
                f"  • Tailored Cover Letter",
                title=" Analysis Complete!",
                border_style="green",
            )
        )

    console.print(
        "  1. Read the full report at [bold]output/job_analysis_report.md[/bold]"
    )


def main():
    # Get inputs
    resume_text = get_resume_input()
    jd_text = get_jd_input()

    console.print(f"Resume: {len(resume_text):,} characters")
    console.print(f"Job description: {len(jd_text):,} characters")
    console.print(f"Model: {ACTIVE_MODEL}\n")

    confirm = Prompt.ask("Start the analysis?", choices=["y", "n"], default="y")
    if confirm.lower() != "y":
        console.print("Cancelled. Run [bold]python main.py[/bold] to start again.")
        return

    # Run the crew
    try:
        outputs = build_and_run_crew(resume_text, jd_text)
        display_results(outputs)
    except Exception as e:
        console.print(f"\n Error during analysis: {e}")
        console.print("\nCommon fixes:")
        console.print("  • Check your LLM_API_KEY in .env")
        console.print("  • Check your internet connection")
        console.print("  • If rate limited, wait 1 minute and try again")
        raise


if __name__ == "__main__":
    main()
