#!/usr/bin/env python3
import json
import pathlib
import re
import subprocess
import sys


TARGET_COMMAND = re.compile(
    r"\b(?:git\s+commit|git\s+push|gh\s+pr\s+create|gh\s+pr\s+ready)\b"
)
CODEX_HOOK = False
HTTP_STATUS_CODE = r"(?:[1-5][0-9]{2})"
STATUS_CODE_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    ".py": [
        (
            re.compile(rf"\bstatus_code\s*=\s*{HTTP_STATUS_CODE}\b"),
            "Use HTTPStatus, fastapi.status, or a project status helper instead of a numeric status_code.",
        ),
        (
            re.compile(rf"\bHTTPException\s*\([^)]*\b{HTTP_STATUS_CODE}\b"),
            "Use HTTPStatus, fastapi.status, or a project status helper for HTTPException status codes.",
        ),
        (
            re.compile(rf"\b(?:Response|JSONResponse)\s*\([^)]*\b{HTTP_STATUS_CODE}\b"),
            "Use HTTPStatus, fastapi.status, or a project status helper for response status codes.",
        ),
    ],
    ".go": [
        (
            re.compile(rf"\bWriteHeader\s*\(\s*{HTTP_STATUS_CODE}\s*\)"),
            "Use net/http status constants or a project status helper instead of numeric WriteHeader codes.",
        ),
        (
            re.compile(rf"\bhttp\.Error\s*\([^)]*,\s*{HTTP_STATUS_CODE}\s*\)"),
            "Use net/http status constants or a project status helper for http.Error status codes.",
        ),
        (
            re.compile(rf"\b(?:JSON|String|Status)\s*\(\s*{HTTP_STATUS_CODE}\b"),
            "Use net/http status constants or a project status helper for HTTP response status codes.",
        ),
    ],
    ".ts": [
        (
            re.compile(rf"@HttpCode\s*\(\s*{HTTP_STATUS_CODE}\s*\)"),
            "Use HttpStatus constants or a project status helper instead of numeric @HttpCode values.",
        ),
        (
            re.compile(rf"\bstatus\s*\(\s*{HTTP_STATUS_CODE}\s*\)"),
            "Use HttpStatus constants or a project status helper instead of numeric response status codes.",
        ),
        (
            re.compile(rf"\bHttpException\s*\([^)]*,\s*{HTTP_STATUS_CODE}\s*\)"),
            "Use HttpStatus constants or a project status helper for HttpException status codes.",
        ),
        (
            re.compile(rf"\bstatusCode\s*:\s*{HTTP_STATUS_CODE}\b"),
            "Use HttpStatus constants or a project status helper instead of numeric statusCode values.",
        ),
    ],
}
STATUS_CODE_PATTERNS[".tsx"] = STATUS_CODE_PATTERNS[".ts"]
HIGH_CONFIDENCE_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
)


def emit(payload: dict, exit_code: int = 0) -> None:
    if CODEX_HOOK:
        if payload.get("permission") == "deny":
            messages = [payload.get("user_message", "")]
            if payload.get("agent_message"):
                messages.append(payload["agent_message"])
            print(json.dumps({"systemMessage": "\n\n".join(messages)}, ensure_ascii=False))
        raise SystemExit(exit_code)

    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(exit_code)


def run(command: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
    )


def changed_files(command: str) -> set[str]:
    files: set[str] = set()
    commands = ["git diff --name-only --cached", "git diff --name-only"]

    # For push / PR create / PR ready, include committed changes not yet in upstream.
    if re.search(r"\b(?:git\s+push|gh\s+pr\s+create|gh\s+pr\s+ready)\b", command):
        upstream = run("git rev-parse --abbrev-ref --symbolic-full-name @{u}")
        if upstream.returncode == 0 and upstream.stdout.strip():
            commands.append("git diff --name-only @{u}..HEAD")

    for cmd in commands:
        result = run(cmd)
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                files.add(line)
    return files


def detect_languages(files: set[str]) -> set[str]:
    langs: set[str] = set()
    for f in files:
        suffix = pathlib.Path(f).suffix.lower()
        if suffix == ".py":
            langs.add("python")
        elif suffix == ".go":
            langs.add("go")
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            langs.add("node")
    return langs


def is_test_file(file_path: str) -> bool:
    path = pathlib.PurePosixPath(file_path)
    name = path.name.lower()
    parts = {part.lower() for part in path.parts}

    if {"test", "tests", "__tests__", "spec"} & parts:
        return True

    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith("_test.go")
        or ".test." in name
        or ".spec." in name
    )


def is_implementation_file(file_path: str) -> bool:
    path = pathlib.PurePosixPath(file_path)
    suffix = path.suffix.lower()
    if suffix not in {".py", ".go", ".js", ".jsx", ".ts", ".tsx"}:
        return False
    if is_test_file(file_path):
        return False
    if path.name.lower().endswith((".d.ts", ".config.js", ".config.ts")):
        return False
    return True


def missing_test_changes(files: set[str]) -> list[str]:
    implementation_files = sorted(f for f in files if is_implementation_file(f))
    if not implementation_files:
        return []

    test_files = [f for f in files if is_test_file(f)]
    if test_files:
        return []

    return implementation_files


def status_code_policy_violations(files: set[str]) -> list[str]:
    violations: list[str] = []
    for file_path in sorted(files):
        path = pathlib.Path(file_path)
        suffix = path.suffix.lower()
        if suffix not in STATUS_CODE_PATTERNS or is_test_file(file_path):
            continue
        if not path.exists() or not path.is_file():
            continue

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//")):
                continue
            for pattern, message in STATUS_CODE_PATTERNS[suffix]:
                if pattern.search(line):
                    violations.append(
                        f"{file_path}:{line_number}: {message}\n"
                        f"  {stripped}"
                    )
                    break
    return violations


def delivery_safety_violations(files: set[str]) -> list[str]:
    """Return high-confidence secrets and unresolved merge markers without exposing values."""
    violations: list[str] = []
    for file_path in sorted(files):
        path = pathlib.Path(file_path)
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS):
                violations.append(f"{file_path}:{line_number}: high-confidence secret pattern detected")
            if line.startswith("<<<<<<< ") or line == "=======" or line.startswith(">>>>>>> "):
                violations.append(f"{file_path}:{line_number}: unresolved merge conflict marker detected")
    return violations


def package_manager() -> str:
    root = pathlib.Path(".")
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def commands_for_language(language: str) -> tuple[list[str], list[str]]:
    if language == "python":
        return (
            ["uv run ruff check .", "ruff check ."],
            ["uv run pytest -q", "pytest -q"],
        )
    if language == "go":
        return (
            ["golangci-lint run", "go vet ./..."],
            ["go test ./..."],
        )
    if language == "node":
        pm = package_manager()
        if pm == "pnpm":
            return (["pnpm lint"], ["pnpm test"])
        if pm == "yarn":
            return (["yarn lint"], ["yarn test --watch=false"])
        return (
            ["npm run lint"],
            ["npm test -- --watch=false"],
        )
    return ([], [])


def execute_candidates(
    candidates: list[str], label: str, language: str
) -> tuple[bool, str]:
    not_found = 0
    last_output = ""
    for cmd in candidates:
        result = run(cmd)
        combined = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode == 0:
            return True, f"{language}:{label} passed with `{cmd}`"
        if result.returncode == 127:
            not_found += 1
            continue
        last_output = combined
        return False, f"{language}:{label} failed with `{cmd}`\n{combined}"
    if not_found == len(candidates):
        return True, f"{language}:{label} skipped (no runnable command found)"
    return False, f"{language}:{label} failed\n{last_output}"


def main() -> None:
    global CODEX_HOOK
    raw = sys.stdin.read().strip()
    data = json.loads(raw) if raw else {}
    CODEX_HOOK = data.get("hook_event_name") == "PreToolUse"
    command = data.get("command", data.get("tool_input", {}).get("command", ""))

    if not TARGET_COMMAND.search(command):
        emit({"permission": "allow"})

    files = changed_files(command)
    status_violations = status_code_policy_violations(files)
    if status_violations:
        emit(
            {
                "permission": "deny",
                "user_message": "HTTP status code の数値直書きが検出されました。helper / framework constant を使ってください。",
                "agent_message": "\n\n".join(status_violations),
            }
        )

    safety_violations = delivery_safety_violations(files)
    if safety_violations:
        emit(
            {
                "permission": "deny",
                "user_message": "Secretまたは未解決のmerge conflict markerが検出されました。削除または解決してから再実行してください。",
                "agent_message": "\n\n".join(safety_violations),
            }
        )

    languages = detect_languages(files)
    missing_tests = missing_test_changes(files)

    if not languages:
        emit(
            {
                "permission": "allow",
                "agent_message": "No python/go/node changes detected. Quality gate skipped.",
            }
        )

    failures: list[str] = []
    passes: list[str] = []
    for lang in sorted(languages):
        lint_cmds, test_cmds = commands_for_language(lang)
        lint_ok, lint_message = execute_candidates(lint_cmds, "lint", lang)
        if lint_ok:
            passes.append(lint_message)
        else:
            failures.append(lint_message)
            continue

        test_ok, test_message = execute_candidates(test_cmds, "test", lang)
        if test_ok:
            passes.append(test_message)
        else:
            failures.append(test_message)

    if failures:
        emit(
            {
                "permission": "deny",
                "user_message": "Commit/push/PR作成の前提チェックで失敗しました。linter/testを修正して再実行してください。",
                "agent_message": "\n\n".join(failures),
            }
        )

    if missing_tests:
        emit(
            {
                "permission": "deny",
                "user_message": "実装コードを変更した場合は、対応するテストコードも同じ変更に含めてください。",
                "agent_message": "Implementation files changed without test changes:\n"
                + "\n".join(f"- {path}" for path in missing_tests),
            }
        )

    emit(
        {
            "permission": "allow",
            "agent_message": "\n".join(passes),
        }
    )


if __name__ == "__main__":
    main()
