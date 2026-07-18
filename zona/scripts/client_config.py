"""Client-config loader for Zona's audit scripts.

The Parlami skills library is client-agnostic: NO real client names, addresses,
or phone numbers live in tracked code. Each client's school data lives in a
gitignored file at `zona/clients/<slug>.config.yml` (see
`zona/clients/example.config.yml` for the template). These scripts read that
config at runtime via `--school <slug>`; the repo ships only the template.

This keeps the SaaS repo reusable for any school and keeps real client data
(a legacy-swarm concern) out of version control.
"""

from pathlib import Path

import yaml

CLIENTS_DIR = Path(__file__).resolve().parent.parent / "clients"
SUFFIX = ".config.yml"

# Fields every school config must define for the tools to run.
REQUIRED = ("name", "address", "phone", "lat", "lng")


def _slug(path):
    return path.name[: -len(SUFFIX)]


def available_schools():
    """Slugs of real (non-template) client configs present on disk."""
    if not CLIENTS_DIR.exists():
        return []
    return sorted(_slug(p) for p in CLIENTS_DIR.glob(f"*{SUFFIX}")
                  if _slug(p) != "example")


def config_path(slug):
    return CLIENTS_DIR / f"{slug}{SUFFIX}"


def load_school(slug):
    """Return one school's config dict, or exit with a helpful message.

    Raises SystemExit (not an exception) so CLI tools fail cleanly with an
    actionable hint instead of a traceback.
    """
    path = config_path(slug)
    if not path.exists():
        have = available_schools()
        hint = (", ".join(have) if have else
                f"(none yet — copy clients/example{SUFFIX} to "
                f"clients/<slug>{SUFFIX} and fill it in)")
        raise SystemExit(f"No client config for '{slug}' at {path}\n"
                         f"Available: {hint}")
    data = yaml.safe_load(path.read_text()) or {}
    school = data.get("school", data)
    missing = [f for f in REQUIRED if not school.get(f)]
    if missing:
        raise SystemExit(f"Config {path} is missing required field(s): "
                         f"{', '.join(missing)}")
    left = [k for k, v in school.items()
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}")]
    if left:
        raise SystemExit(f"Config {path} still has unfilled placeholder(s): "
                         f"{', '.join(left)}")
    for list_field in ("aliases", "areas", "services",
                       "address_fragments", "phone_fragments", "keywords"):
        school.setdefault(list_field, [])
    return school
