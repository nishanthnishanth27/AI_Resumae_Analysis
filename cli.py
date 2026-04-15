"""
Command-line interface for Resume Screening AI System.

Usage examples
--------------
# Screen resumes from JSON files
python cli.py --job job.txt --resumes resumes.json --top 3

# Screen resumes from text files in a folder
python cli.py --job job.txt --folder ./resume_files/ --top 5

# Export results to JSON
python cli.py --job job.txt --resumes resumes.json --output results.json
"""

import argparse
import json
import os
import sys

from resume_screener import ResumeScreener

# ── ANSI colours ─────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
GOLD   = "\033[33m"


def grade_color(grade: str) -> str:
    return {
        "Excellent": GREEN,
        "Good": CYAN,
        "Fair": YELLOW,
        "Poor": RED,
    }.get(grade, RESET)


def bar(score: float, width: int = 30) -> str:
    filled = int(score / 100 * width)
    color = GREEN if score >= 60 else YELLOW if score >= 40 else RED
    return color + "█" * filled + DIM + "░" * (width - filled) + RESET


def print_results(results: list, total: int):
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}  RESUME SCREENING RESULTS  —  {len(results)} of {total} candidates{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}\n")

    for r in results:
        rank_icons = {1: f"{GOLD}🥇{RESET}", 2: "🥈", 3: "🥉"}
        icon = rank_icons.get(r["rank"], f"  #{r['rank']}")

        gc = grade_color(r["grade"])
        print(f"  {icon}  {BOLD}{r['name']}{RESET}  {gc}[{r['grade']}]{RESET}")
        print(f"      Score: {BOLD}{r['score']}%{RESET}  {bar(r['score'])}")
        if r.get("email"):
            print(f"      Email: {DIM}{r['email']}{RESET}")
        if r["matched_keywords"]:
            kw_str = "  ".join(r["matched_keywords"][:8])
            print(f"      Keywords: {DIM}{kw_str}{RESET}")
        print()

    print(f"{BOLD}{CYAN}{'─'*60}{RESET}\n")


def load_resumes_from_json(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("resumes JSON must be an array of objects")
    return data


def load_resumes_from_folder(folder: str) -> list:
    resumes = []
    for fname in sorted(os.listdir(folder)):
        if fname.endswith(".txt"):
            fpath = os.path.join(folder, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
            name = os.path.splitext(fname)[0].replace("_", " ").title()
            resumes.append({"name": name, "text": text})
    return resumes


def main():
    parser = argparse.ArgumentParser(
        description="Resume Screening AI — rank candidates against a job description"
    )
    parser.add_argument("--job", required=True, help="Path to job description text file")
    parser.add_argument("--resumes", help="Path to resumes JSON file")
    parser.add_argument("--folder", help="Folder of .txt resume files")
    parser.add_argument("--top", type=int, default=None, help="Number of top candidates to show")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    # Load job description
    if not os.path.isfile(args.job):
        print(f"{RED}Error: job file not found: {args.job}{RESET}", file=sys.stderr)
        sys.exit(1)
    with open(args.job, "r", encoding="utf-8") as f:
        job_description = f.read()

    # Load resumes
    resumes = []
    if args.resumes:
        resumes = load_resumes_from_json(args.resumes)
    elif args.folder:
        resumes = load_resumes_from_folder(args.folder)
    else:
        print(f"{RED}Error: provide --resumes or --folder{RESET}", file=sys.stderr)
        sys.exit(1)

    if not resumes:
        print(f"{YELLOW}No resumes found.{RESET}", file=sys.stderr)
        sys.exit(0)

    # Screen
    screener = ResumeScreener()
    results = screener.screen(job_description, resumes, top_n=args.top)

    # Display
    print_results(results, total=len(resumes))

    # Optional export
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"{GREEN}Results saved to {args.output}{RESET}\n")


if __name__ == "__main__":
    main()
