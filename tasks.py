import uuid
from pathlib import Path

import httpx
from invoke import Context, task


MAIN_DIRECTORY_PATH = Path(__file__).parent


@task
def format(context: Context) -> None:
    """Run RUFF to format all Python files."""

    exec_cmds = ["ruff format .", "ruff check . --fix"]
    with context.cd(MAIN_DIRECTORY_PATH):
        for cmd in exec_cmds:
            context.run(cmd)


@task
def lint_yaml(context: Context) -> None:
    """Run Linter to check all Python files."""
    print(" - Check code with yamllint")
    exec_cmd = "yamllint ."
    with context.cd(MAIN_DIRECTORY_PATH):
        context.run(exec_cmd)


@task
def lint_pyright(context: Context) -> None:
    """Run Linter to check all Python files."""
    print(" - Check code with mypy")
    exec_cmd = "pyright workshop_b2"
    with context.cd(MAIN_DIRECTORY_PATH):
        context.run(exec_cmd)


@task
def lint_ruff(context: Context) -> None:
    """Run Linter to check all Python files."""
    print(" - Check code with ruff")
    exec_cmd = "ruff check ."
    with context.cd(MAIN_DIRECTORY_PATH):
        context.run(exec_cmd)


@task(name="lint")
def lint_all(context: Context) -> None:
    """Run all linters."""
    lint_yaml(context)
    lint_ruff(context)
    lint_pyright(context)


###
## Lab 1 Commands
###
def create_lab1_devices(url: str, site_id: int) -> httpx.Response:
    from workshop_b2.lab1.database import models as Lab1Models

    dev = Lab1Models.DeviceModel(
        name=f"device-{str(uuid.uuid4())[-8:]}", manufacturer="cisco", site_id=site_id
    )
    with httpx.Client() as client:
        print(f"Creating device: {dev.model_dump()}")
        return client.post(f"{url}/api/devices/", json=dev.model_dump())


@task
def lab1_start(context: Context, reload: bool = True) -> None:
    """Start Lab1."""
    exec_cmd = "fastapi run workshop_b2/lab1/main.py --port 8101"
    if reload:
        exec_cmd += " --reload"
    context.run(exec_cmd)


@task
def lab1_destroy(context: Context, reload: bool = False) -> None:
    """Destroy Lab1."""
    context.run("rm database.db")


@task
def lab1_load(
    context: Context, url: str = "http://localhost:8101", site_name: str = "site-1"
) -> None:
    """Load devices into Lab1."""
    with httpx.Client() as client:
        response = client.get(f"{url}/api/sites/")
        response.raise_for_status()
        site_id = [s["id"] for s in response.json() if s["name"] == site_name]
        if not site_id:
            response = client.post(
                f"{url}/api/sites/",
                json={
                    "name": site_name,
                    "site_id": site_id,
                    "address": "123 Wall Street",
                    "label": site_name,
                },
            )
            response.raise_for_status()
            site_id = response.json()["id"]

    for _ in range(0, 5):
        response = create_lab1_devices(url=url, site_id=site_id)
        response.raise_for_status()


@task
def lab1_test(context: Context) -> None:
    """Run pytest against Lab1."""
    exec_cmd = "pytest tests/lab1"
    context.run(exec_cmd)


###
## Lab 2 Commands
###
def create_lab2_devices(
    url: str,
    site_name: str,
    wants_tags: bool = False,
    tags: list["Tag"] | None = None,
) -> httpx.Response:
    from workshop_b2.lab2.database import models as Lab2Models

    dev = Lab2Models.DeviceModel(
        name=f"device-{str(uuid.uuid4())[-8:]}",
        site={"name": site_name, "label": site_name, "address": "123 Wall Street"},
        tags=tags if wants_tags else [],
    )
    with httpx.Client() as client:
        print(f"Creating device: {dev.model_dump()}")
        return client.post(f"{url}/api/devices/", json=dev.model_dump())


@task
def lab2_start(context: Context, reload: bool = True) -> None:
    """Start Lab2."""
    exec_cmd = "fastapi run workshop_b2/lab2/main.py --port 8102"
    if reload:
        exec_cmd += " --reload"
    context.run("docker compose up -d")
    context.run(exec_cmd)


@task
def lab2_destroy(context: Context, reload: bool = False) -> None:
    """Destroy Lab2."""
    context.run("docker compose down -v")


@task
def lab2_load(
    context: Context,
    url: str = "http://localhost:8102",
    site_name: str = "site-1",
    tags: bool = False,
) -> None:
    from workshop_b2.lab2.database import models as Lab2Models

    """Load devices into Lab2."""
    with httpx.Client() as client:
        response = client.get(f"{url}/api/sites/")
        response.raise_for_status()
        site_id = [s["name"] for s in response.json() if s["name"] == site_name]
        if not site_id:
            response = client.post(
                f"{url}/api/sites/",
                json={
                    "name": site_name,
                    "label": site_name,
                    "address": "123 Wall Street",
                },
            )
            response.raise_for_status()

    default_tags = [
        {"name": "tag1", "color": "red"},
        {"name": "tag2", "color": "blue"},
        {"name": "tag3", "color": "yellow"},
        {"name": "tag4", "color": "orange"},
        {"name": "tag5", "color": "green"},
        {"name": "tag6", "color": "green"},
    ]
    is_tagged = "tags" in Lab2Models.Device.model_fields
    if tags and is_tagged:
        with httpx.Client() as client:
            response = client.get(f"{url}/api/tags/")
            response.raise_for_status()
            found_tags = [t["name"] for t in response.json()]
            for tag in default_tags:
                if tag["name"] not in found_tags:
                    response = client.post(f"{url}/api/tags/", json=tag)
                    response.raise_for_status()
    else:
        print("No tags to load due to tags not being implemented in the model.")
    for _ in range(0, 4):
        # Get initial even or odd tag and then skip by 2
        odds_or_even = _ % 2
        assigned_tags = default_tags[odds_or_even::2]
        device_tags = assigned_tags if tags and is_tagged else []
        response = create_lab2_devices(
            url=url, site_name=site_name, wants_tags=tags, tags=device_tags
        )
        response.raise_for_status()


# @task
# def lab2_test(context: Context) -> None:
#     """Run pytest against Lab2."""
#     exec_cmd = "pytest tests/lab2"
#     context.run(exec_cmd)
