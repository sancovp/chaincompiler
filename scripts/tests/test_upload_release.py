"""THE UPLOAD's driver (`scripts/upload_release.py`, DESIGN.md §18): its order, and its decisions against a stand-in PyPI.

The order is read from this repository's own build files and skills. The run is given a fake PyPI (which versions it
holds, which projects it has) and a fake upload, so no test touches the network. Run from the repository root:
`python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from upload_release import packages, run, upload_order  # noqa: E402

PKGS = packages(REPO)
V = next(iter({p["version"] for p in PKGS.values()}))


def test_the_order_puts_every_package_after_its_siblings_and_the_server_closure_first():
    order = upload_order(REPO)
    assert sorted(order) == sorted(PKGS)
    for n in order:
        assert all(order.index(r) < order.index(n) for r in PKGS[n]["requires"]), n
    server_closure = order[: order.index("chaincompiler-si") + 1]
    assert set(server_closure) == {"rulecatcher", "honeyc", "skillchain-compiler", "chaincompiler", "chaincompiler-accc",
                                   "corcc", "sccc", "chainaios", "chaincompiler-si"}
    assert order.index("glyphsteer") < order.index("personacc") and order.index("skill2framework") < order.index("goldenreq")


class FakePyPI:
    """Which versions PyPI holds and which projects it has; an upload of a new name past `quota` answers 429."""
    def __init__(self, holds: set[str], quota: int):
        self.holds, self.projects, self.quota, self.uploads = set(holds), set(holds), quota, []

    def status(self, name, version):
        return name in self.holds

    def project(self, name):
        return 200 if name in self.projects else 404

    def upload(self, script, folder):
        name = next(n for n, p in PKGS.items() if p["folder"] == folder)
        if name not in self.projects:
            if self.quota == 0:
                return 1, "HTTPError: 429 Too Many Requests\nToo many new projects created"
            self.quota -= 1
            self.projects.add(name)
        self.holds.add(name)
        self.uploads.append(name)
        return 0, f"[package] uploaded {name} {V} to PyPI"


def go(pypi: FakePyPI, capsys) -> tuple[int, str]:
    code = run(REPO, "publish_package.sh", status=pypi.status, project=pypi.project, upload=pypi.upload)
    return code, capsys.readouterr().out


def test_day_one_alphabetical_state_resumes_in_order_within_the_quota(capsys):
    # what PyPI held after the alphabetical first pass: four new names that need honeyc, and rulecatcher
    pypi = FakePyPI({"chaincompiler-accc", "chaincompiler-archetype", "chainaios", "chaincompiler", "rulecatcher"}, quota=4)
    code, out = go(pypi, capsys)
    assert code == 3
    assert pypi.uploads == ["honeyc", "corcc", "skillchain-compiler", "sccc"]
    assert "chaincompiler-si" in out.split("waiting:")[1]


def test_a_package_waits_until_every_sibling_it_requires_is_held(capsys):
    pypi = FakePyPI(set(), quota=1)
    code, out = go(pypi, capsys)
    assert code == 3 and pypi.uploads == ["honeyc"]
    assert "chaincompiler" in out and "waits: PyPI does not hold rulecatcher" in out


def test_after_a_429_a_held_projects_version_still_uploads(capsys):
    # every project exists but at an older version, save personacc, a new name with the quota spent
    pypi = FakePyPI(set(), quota=0)
    pypi.projects = set(PKGS) - {"personacc"}
    code, out = go(pypi, capsys)
    assert code == 3
    assert set(pypi.uploads) == set(PKGS) - {"personacc", "personapack"}
    assert "personacc" in out and "429" in out and "personapack                waits: PyPI does not hold personacc" in out


def test_a_refusal_of_a_version_pypi_holds_reads_as_uploaded(capsys):
    pypi = FakePyPI(set(PKGS) - {"goldenreq"}, quota=4)
    pypi.upload = lambda script, folder: (1, f"[package] REFUSED: PyPI already holds goldenreq {V} — move the version")
    code, out = go(pypi, capsys)
    assert code == 0 and f"PyPI holds {len(PKGS)} of {len(PKGS)}" in out


def test_a_failure_names_twines_error_not_the_builds_last_line(capsys):
    # the publish script's output as it comes back: twine's error on stdout, the build's progress after it on stderr
    out = ("[package] PyPI goldenreq " + V + "\nUploading goldenreq.whl\n\x1b[31mERROR   \x1b[0m HTTPError: 403 Forbidden"
           " from https://upload.pypi.org/legacy/\n         The user isn't allowed to upload to project 'goldenreq'.\n"
           "* Creating isolated environment: venv+pip...\n* Building wheel...\n")
    pypi = FakePyPI(set(PKGS) - {"goldenreq"}, quota=4)
    pypi.upload = lambda script, folder: (1, out)
    code, printed = go(pypi, capsys)
    assert code == 1
    line = next(l for l in printed.splitlines() if l.strip().startswith("goldenreq"))
    assert "HTTPError: 403 Forbidden" in line and "isn't allowed to upload to project 'goldenreq'" in line
    assert "Building wheel" not in line


def test_everything_held_uploads_nothing(capsys):
    pypi = FakePyPI(set(PKGS), quota=4)
    code, out = go(pypi, capsys)
    assert code == 0 and pypi.uploads == []
