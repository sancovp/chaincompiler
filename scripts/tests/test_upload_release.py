"""THE UPLOAD's driver (`scripts/upload_release.py`, DESIGN.md §18): its order, and its decisions against a stand-in PyPI.

The order is read from this repository's own build files and skills. The run is given a fake PyPI (which versions it
holds, which projects it has) and a fake upload, so no test touches the network. Run from the repository root:
`python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from upload_release import packages, run, upload_order, whole  # noqa: E402

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


UPLOADED = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
LATER = UPLOADED + timedelta(hours=1)                # every cache life long past


class LaggingPyPI:
    """PyPI's pages as they can stand after an upload (scalable-publishing DESIGN.md §4): each version's JSON holds the
    release, its newest file uploaded at UPLOADED; the project's JSON still names the version before it, as v0.3.2's
    read did; and the simple index — its HTML form and the JSON form pip and uv ask for, which PyPI's cache keeps apart,
    each cached up to 600 s — lists the release's files for the names in `html` and in `json` only."""
    def __init__(self, html: set[str], json_form: set[str] | None = None, silent: set[str] = frozenset()):
        self.html, self.json = set(html), set(html if json_form is None else json_form)
        self.silent, self.asked = set(silent), []

    def get(self, url: str, accept: str | None = None) -> tuple[int, str, dict]:
        self.asked.append((url, accept))
        name = url.split("/")[4]
        if name in self.silent:
            return 0, "", {}
        if url.endswith(f"/{V}/json"):
            return 200, json.dumps({"info": {"name": name, "version": V}, "urls": [
                {"filename": f"{name}-{V}.tar.gz", "upload_time_iso_8601": "2026-01-01T11:59:40.000000Z"},
                {"filename": f"{name}-{V}-py3-none-any.whl", "upload_time_iso_8601": "2026-01-01T12:00:00.000000Z"}]}), \
                {"cache-control": "max-age=900, public"}
        if url.endswith(f"/pypi/{name}/json"):
            return 200, json.dumps({"info": {"name": name, "version": "0.0.1"}, "releases": {"0.0.1": [{}]}}), {}
        if url.endswith(f"/simple/{name}/"):
            files = [f"{name.replace('-', '_')}-0.0.1.tar.gz"]
            in_json = accept == "application/vnd.pypi.simple.v1+json"
            if name in (self.json if in_json else self.html):
                files.append(f"{name.replace('-', '_')}-{V}-py3-none-any.whl")
            body = (json.dumps({"files": [{"filename": f} for f in files]}) if in_json
                    else "".join(f'<a href="x">{f}</a>' for f in files))
            return 200, body, {"cache-control": "max-age=600, public", "vary": "Accept-Encoding, Accept"}
        return 404, "", {}


def test_whole_reads_each_versions_json_never_the_projects(capsys):
    # the project's JSON still names 0.0.1; a reading of it would call the release short
    web = LaggingPyPI(html=set(PKGS))
    code = whole(REPO, get=web.get, now=LATER)
    out = capsys.readouterr().out
    assert code == 0, out
    assert f"PyPI holds {V} whole" in out
    assert not [u for u, _ in web.asked if u.endswith("/json") and not u.endswith(f"/{V}/json")]


def test_whole_waits_until_the_simple_index_lists_the_release(capsys):
    web = LaggingPyPI(html=set(PKGS) - {"goldenreq"})
    code = whole(REPO, get=web.get, now=LATER)
    out = capsys.readouterr().out
    assert code == 3 and "for goldenreq" in out and "HTML does not list it" in out


def test_whole_waits_until_the_form_pip_reads_lists_the_release(capsys):
    # v0.3.3's first install: the HTML form listed chaincompiler-si's release while the JSON form pip reads did not
    web = LaggingPyPI(html=set(PKGS), json_form=set(PKGS) - {"chaincompiler-si"})
    code = whole(REPO, get=web.get, now=LATER)
    out = capsys.readouterr().out
    assert code == 3 and "for chaincompiler-si" in out, out
    line = next(l for l in out.splitlines() if l.strip().startswith("chaincompiler-si "))
    assert "HTML lists it · JSON does not list it" in line
    assert ("https://pypi.org/simple/chaincompiler-si/", "application/vnd.pypi.simple.v1+json") in web.asked


def test_whole_waits_out_the_index_cache_after_an_upload(capsys):
    # both forms list it, but the newest upload is 281 s old and the index is cached up to 600 s: another reader can still
    # be served a copy from before the upload, so the release is not yet called whole
    web = LaggingPyPI(html=set(PKGS))
    code = whole(REPO, get=web.get, now=UPLOADED + timedelta(seconds=281))
    out = capsys.readouterr().out
    assert code == 3 and "uploaded within the index's cache life" in out, out
    assert "(281 s ago)" in out and "cached up to 600 s" in out
    assert whole(REPO, get=web.get, now=UPLOADED + timedelta(seconds=601)) == 0


def test_a_version_pypi_does_not_hold_is_told_apart_from_the_index_lag(capsys):
    # a 404 on the version's JSON: read again first, since in the minutes after an upload a cache can still serve it
    web = LaggingPyPI(html=set(PKGS))
    real = web.get
    web.get = lambda url, accept=None: (404, "", {}) if url.endswith(f"/goldenreq/{V}/json") else real(url, accept)
    code = whole(REPO, get=web.get, now=LATER)
    out = capsys.readouterr().out
    assert code == 4 and f"PyPI does not hold {V} for goldenreq by its version's JSON" in out
    assert "read again in a minute; if it still answers 404, run the upload again" in out


def test_whole_decides_nothing_without_pypis_answer(capsys):
    web = LaggingPyPI(html=set(PKGS), silent={"honeyc"})
    code = whole(REPO, get=web.get, now=LATER)
    assert code == 1 and "no answer for honeyc" in capsys.readouterr().out
