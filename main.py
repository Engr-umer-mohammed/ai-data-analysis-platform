# main.py
# AI Data Analysis Agent — Terminal Interface
# Version 2.0 — With Customization Support
#
# This is the terminal interface for the complete
# AI Data Analysis Agent pipeline. It serves as
# the primary testing and validation environment
# during development, and mirrors exactly what
# the Telegram deployment layer will call —
# ensuring every behavior verified here works
# identically in production without modification.
#
# Architecture note:
# This file contains zero business logic.
# All intelligence, orchestration, error handling,
# session management, and output generation lives
# inside data_agent.py and its dependencies.
# main.py is a pure interface layer — its only
# responsibility is presenting options to the user
# and passing their inputs to the agent.

import os
import sys
from datetime import datetime
from data_agent import DataAnalysisAgent
from config.config import config


# ─── DISPLAY UTILITIES ────────────────────────────────────────────

def clear_line() -> None:
    print()


def separator(char: str = "═", width: int = 58) -> str:
    return char * width


def print_header() -> None:
    print("\n" + separator())
    print("       AI DATA ANALYSIS AGENT  v2.0")
    print("       Intelligent Dataset Intelligence")
    print(separator())
    print(f"  Session started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    active_client = config.get_active_client()
    if active_client:
        print(f"  Active Client   : {active_client.upper()}")
    else:
        print(f"  Active Client   : Default (no client-specific config)")


def print_menu(agent: DataAnalysisAgent) -> None:
    total = agent.get_total_sessions()
    print("\n" + separator("─", 58))
    print("  MAIN MENU")
    print(separator("─", 58))
    print("  1.  Analyze a new data file")
    print("  2.  View session history")
    print("  3.  Show output folder locations")
    print("  4.  Set active client")
    print("  5.  Exit")
    print(separator("─", 58))
    print(f"  Total sessions completed : {total}\n")


# ─── MENU HANDLERS ──────────────────────────────────────────────────

def handle_analyze(agent: DataAnalysisAgent) -> None:
    """
    Collect file path from user, validate it through
    the agent before committing to the full pipeline,
    run the analysis, and present the complete session
    summary including all output file locations.
    """

    print("\n" + separator("─", 58))
    print("  NEW ANALYSIS")
    print(separator("─", 58))
    print("  Supported formats : CSV, Excel, JSON, TXT")
    print("  Enter the full path to your data file.")
    print("  Example: C:\\Users\\you\\data\\sales.csv")

    active_client = config.get_active_client()
    print(f"  Active Client    : {active_client or 'Default'}")

    print(separator("─", 58))

    file_path = input("\n  File path: ").strip().strip('"')

    if not file_path:
        print("\n  No path entered. Returning to menu.")
        return

    print("\n  Validating file...")
    is_valid, message = agent.validate_file(file_path)

    if not is_valid:
        print(f"\n  Validation failed:\n  {message}")
        print("\n  Please check the path and try again.")
        return

    print(f"  {message}")
    print("\n  Starting full analysis pipeline...")
    print("  This may take 30 to 90 seconds depending")
    print("  on file size and AI model response time.")
    print()

    session = agent.analyze(file_path)
    print(session.get_terminal_summary())

    if session.pipeline_success:
        print(
            "\n  All outputs are saved and ready.\n"
            "  Open the reports and charts folders\n"
            "  to review the full results."
        )
    else:
        print(
            "\n  Pipeline completed with errors.\n"
            "  Check the stage error details above.\n"
            "  Partial outputs may still be available."
        )


def handle_history(agent: DataAnalysisAgent) -> None:
    """
    Display the persistent session history maintained
    by the agent across all previous runs. This gives
    a longitudinal view of every dataset analyzed
    since the agent was first initialized.
    """

    print("\n" + separator("─", 58))
    print("  SESSION HISTORY")
    print(separator("─", 58))
    print()
    print(agent.get_session_history())


def handle_folders() -> None:
    """
    Display the current output folder structure with
    the actual paths on disk, and a count of files
    currently inside each folder. Useful for locating
    outputs without navigating through the filesystem
    manually, and for verifying the agent is writing
    to the expected locations.
    """

    print("\n" + separator("─", 58))
    print("  OUTPUT FOLDER LOCATIONS")
    print(separator("─", 58))

    folders = {
        "Text Reports": "reports",
        "Excel Reports": "excel_reports",
        "Charts": "charts",
        "Session History": ".",
    }

    file_filters = {
        "Text Reports": ".txt",
        "Excel Reports": ".xlsx",
        "Charts": ".png",
        "Session History": "analysis_history.json",
    }

    for label, folder in folders.items():
        abs_path = os.path.abspath(folder)
        ext = file_filters[label]

        if label == "Session History":
            history_path = os.path.join(
                abs_path, "analysis_history.json"
            )
            exists = os.path.exists(history_path)
            status = "Found" if exists else "Not yet created"
            print(
                f"\n  {label}\n"
                f"    Path   : {history_path}\n"
                f"    Status : {status}"
            )
            continue

        if os.path.exists(folder):
            all_files = []
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith(ext):
                        all_files.append(
                            os.path.join(root, f)
                        )
            count = len(all_files)
            size_kb = sum(
                os.path.getsize(f)
                for f in all_files
                if os.path.exists(f)
            ) / 1024

            print(
                f"\n  {label}\n"
                f"    Path   : {abs_path}\n"
                f"    Files  : {count} {ext} file"
                f"{'s' if count != 1 else ''}\n"
                f"    Size   : {size_kb:.1f} KB total"
            )
        else:
            print(
                f"\n  {label}\n"
                f"    Path   : {abs_path}\n"
                f"    Status : Folder not yet created"
            )

    print()


# ─── Client Selection Handler ──────────────────────────────────────

def handle_client_selection() -> None:
    """
    Set the active client for the current session.
    This determines which client-specific thresholds
    are used in the analysis.
    """
    print("\n" + separator("─", 58))
    print("  CLIENT SELECTION")
    print(separator("─", 58))

    available_clients = config.get_all_clients()
    active_client = config.get_active_client()

    print(f"  Current active client: {active_client or 'Default'}")
    print()

    if not available_clients:
        print("  No client configurations found.")
        print("  Create JSON files in customization/clients/{domain}/ to add clients.")  # ← UPDATED
        print()
        return

    print("  Available clients:")
    for i, client_name in enumerate(available_clients, 1):
        marker = "  ← ACTIVE" if client_name == active_client else ""
        print(f"    {i}. {client_name}{marker}")

    print()
    print("  Enter '0' to use Default (no client-specific config)")
    print("  Enter 'c' to clear active client")
    print()

    choice = input("  Select client (number): ").strip()

    if choice.lower() == 'c':
        config._config['active_client'] = None
        print("\n  Active client cleared. Using defaults.")
        return

    try:
        idx = int(choice)
        if idx == 0:
            config._config['active_client'] = None
            print("\n  Using default configuration.")
        elif 1 <= idx <= len(available_clients):
            selected = available_clients[idx - 1]
            config._config['active_client'] = selected
            print(f"\n  Active client set to: {selected.upper()}")
        else:
            print("\n  Invalid selection.")
    except ValueError:
        print("\n  Invalid input.")


# ─── STARTUP VALIDATION ────────────────────────────────────────────

def validate_environment() -> bool:
    """
    Before initializing the agent, verify that the
    execution environment has everything required.
    This catches missing API keys, absent libraries,
    and misconfigured environments early — before
    the user reaches the analysis stage and encounters
    a cryptic failure midway through a long pipeline run.
    Returns True if the environment is ready.
    """

    print("\n  Checking environment...")
    issues = []

    required_libraries = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("openpyxl", "openpyxl"),
        ("google.genai", "google-genai"),
        ("dotenv", "python-dotenv"),
    ]

    for module_name, pip_name in required_libraries:
        try:
            __import__(module_name)
        except ImportError:
            issues.append(
                f"Missing library: {pip_name}  "
                f"→  pip install {pip_name}"
            )

    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        issues.append(
            "Missing GEMINI_API_KEY in .env file  "
            "→  Add: GEMINI_API_KEY=your_key_here"
        )

    required_files = [
        "data_agent.py",
        "data_loader.py",
        "statistical_analyzer.py",
        "visualizer.py",
        "report_generator.py",
        "config/config.py",
    ]

    for filename in required_files:
        if not os.path.exists(filename):
            issues.append(
                f"Missing project file: {filename}"
            )

    if issues:
        print("\n  Environment issues found:")
        for issue in issues:
            print(f"    ✗  {issue}")
        print(
            "\n  Resolve the issues above before"
            " running the agent."
        )
        return False

    print("  Environment verified. All checks passed.")
    return True


# ─── MAIN ENTRY POINT ─────────────────────────────────────────────

def main() -> None:
    """
    Primary entry point for the terminal interface.
    Validates the environment, initializes the agent,
    and runs the interactive menu loop until the user
    explicitly chooses to exit. Every menu action is
    handled by a dedicated function that contains all
    the input collection and output display logic for
    that specific operation, keeping this function
    clean and focused purely on the control flow.
    """

    print_header()

    if not validate_environment():
        sys.exit(1)

    env_client = os.getenv("AI_ACTIVE_CLIENT")
    if env_client:
        config._config['active_client'] = env_client
        print(f"  Active client set from environment: {env_client.upper()}")

    print("\n  Initializing agent components...")
    agent = DataAnalysisAgent()

    while True:
        print_menu(agent)

        choice = input("  Enter choice (1/2/3/4/5): ").strip()

        if choice == "1":
            handle_analyze(agent)

        elif choice == "2":
            handle_history(agent)

        elif choice == "3":
            handle_folders()

        elif choice == "4":
            handle_client_selection()

        elif choice == "5":
            print(
                f"\n  Agent shutting down.\n"
                f"  Total sessions this run : "
                f"{agent.get_total_sessions()}\n"
                f"  All outputs are saved.\n"
                f"  Goodbye.\n"
            )
            sys.exit(0)

        else:
            print(
                "\n  Invalid input. "
                "Please enter 1, 2, 3, 4, or 5."
            )


if __name__ == "__main__":
    main()