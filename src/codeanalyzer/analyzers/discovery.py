"""Manifest-driven ecosystem detection and tool negotiation.

Declarative-first: manifests name the expected toolchain; runtime probing
only validates availability and version. Does not walk every acquisition
channel to discover capabilities.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from codeanalyzer.analyzers.adapter import AnalyzerAdapter
from codeanalyzer.domain.tooling import ToolStatus

_FLUTTER_SDK_RE = re.compile(r"sdk:\s*['\"]([^'\"]+)['\"]")


class EcosystemManifest(BaseModel):
    """Detected toolchain expectation for a project root."""

    ecosystem: str
    languages: list[str] = Field(default_factory=list)
    expected_analyzers: list[str] = Field(default_factory=list)
    manifest_files: list[str] = Field(default_factory=list)
    version_requirements: dict[str, str] = Field(default_factory=dict)


def detect_ecosystems(project_path: str) -> list[EcosystemManifest]:
    """Identify expected tools from project manifests, not from PATH probes."""
    root = Path(project_path)
    found: list[EcosystemManifest] = []

    python_manifests = [
        name
        for name in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")
        if (root / name).exists()
    ]
    if python_manifests or any(root.glob("*.py")):
        found.append(
            EcosystemManifest(
                ecosystem="python",
                languages=["python"],
                expected_analyzers=["mypy"],
                manifest_files=python_manifests,
            )
        )

    pubspec = root / "pubspec.yaml"
    if pubspec.exists():
        requirement: dict[str, str] = {}
        sdk = _flutter_sdk_constraint(pubspec.read_text(encoding="utf-8", errors="replace"))
        if sdk:
            requirement["flutter_analyze"] = sdk
        found.append(
            EcosystemManifest(
                ecosystem="flutter",
                languages=["dart"],
                expected_analyzers=["flutter_analyze"],
                manifest_files=["pubspec.yaml"],
                version_requirements=requirement,
            )
        )

    package_json = root / "package.json"
    tsconfig = root / "tsconfig.json"
    js_manifests: list[str] = []
    js_analyzers: list[str] = []
    js_languages: list[str] = []
    js_requirements: dict[str, str] = {}
    if package_json.exists():
        js_manifests.append("package.json")
        js_analyzers.append("eslint")
        js_languages.extend(["javascript", "typescript"])
        js_requirements.update(_package_json_requirements(package_json))
    if tsconfig.exists():
        js_manifests.append("tsconfig.json")
        if "typescript" not in js_analyzers:
            js_analyzers.append("typescript")
        if "typescript" not in js_languages:
            js_languages.append("typescript")
    if js_manifests:
        found.append(
            EcosystemManifest(
                ecosystem="javascript",
                languages=js_languages,
                expected_analyzers=js_analyzers,
                manifest_files=js_manifests,
                version_requirements=js_requirements,
            )
        )

    composer = root / "composer.json"
    if composer.exists():
        found.append(
            EcosystemManifest(
                ecosystem="php",
                languages=["php"],
                expected_analyzers=["phpstan"],
                manifest_files=["composer.json"],
            )
        )

    return found


def negotiate_tools(adapters: list[AnalyzerAdapter], project_path: str) -> list[ToolStatus]:
    """Probe installed adapters and attach manifest-derived requirements."""
    expected: dict[str, str] = {}
    for eco in detect_ecosystems(project_path):
        for analyzer_id in eco.expected_analyzers:
            expected[analyzer_id] = eco.version_requirements.get(analyzer_id, "")

    statuses: list[ToolStatus] = []
    for adapter in adapters:
        analyzer_id = adapter.capabilities().analyzer_id
        status = adapter.probe(project_path=project_path)
        if analyzer_id in expected:
            requirement = expected[analyzer_id] or None
            status = status.model_copy(update={"project_requirement": requirement})
        statuses.append(status)
    return statuses


def _flutter_sdk_constraint(text: str) -> str | None:
    match = _FLUTTER_SDK_RE.search(text)
    return match.group(1) if match else None


def _package_json_requirements(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    requirements: dict[str, str] = {}
    engines = data.get("engines")
    if isinstance(engines, dict):
        typescript = engines.get("typescript")
        if isinstance(typescript, str) and typescript:
            requirements["typescript"] = typescript
    dev_deps = data.get("devDependencies")
    deps = data.get("dependencies")
    for mapping in (dev_deps, deps):
        if not isinstance(mapping, dict):
            continue
        eslint = mapping.get("eslint")
        if isinstance(eslint, str) and eslint and "eslint" not in requirements:
            requirements["eslint"] = eslint
        tsc = mapping.get("typescript")
        if isinstance(tsc, str) and tsc and "typescript" not in requirements:
            requirements["typescript"] = tsc
    return requirements
