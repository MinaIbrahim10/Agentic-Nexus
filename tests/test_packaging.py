from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_packaging_files_exist():
    required = [
        ".env.example",
        "scripts/setup.sh",
        "scripts/run_api.sh",
        "scripts/seed_demo.sh",
        "scripts/seed_demo.py",
        "scripts/demo.sh",
    ]

    for item in required:
        assert (
            ROOT / item
        ).is_file(), item


def test_readme_has_concept_to_code_table():
    readme = (
        ROOT / "README.md"
    ).read_text()

    concepts = [
        "API endpoints",
        "Database",
        "Authentication",
        "Background jobs",
        "Caching logic",
        "LLM integration",
    ]

    for concept in concepts:
        assert concept in readme


def test_readme_has_two_command_start_path():
    readme = (
        ROOT / "README.md"
    ).read_text()

    assert "./scripts/setup.sh" in readme
    assert "./scripts/run_api.sh" in readme
    assert "two commands" in readme


def test_readme_has_five_minute_demo():
    readme = (
        ROOT / "README.md"
    ).read_text()

    assert "5-Minute Demo Path" in readme
    assert "./scripts/demo.sh" in readme
    assert "5-MINUTE DEMO: PASS" in readme


def test_gitignore_covers_local_runtime_artifacts():
    ignore = (
        ROOT / ".gitignore"
    ).read_text()

    required = [
        ".env",
        ".venv/",
        "*.duckdb",
        "__pycache__/",
        "*.log",
    ]

    for pattern in required:
        assert pattern in ignore
