import nox


@nox.session(reuse_venv=True)
def tests(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements.txt")
    session.env["SKIP_NETWORK"] = session.env.get("SKIP_NETWORK", "true")
    session.run("pytest", "-q")


@nox.session(reuse_venv=True)
def smoke(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.env["PYTHONPATH"] = "src"
    session.run("python", "scripts/smoke_integrated_server.py")
    session.run("python", "scripts/smoke_endpoints.py")


@nox.session(reuse_venv=True)
def deps_report(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.env["PYTHONPATH"] = "src"
    session.run(
        "python",
        "-c",
        "from vpn_merger.utils.dependencies import print_dependency_report; print_dependency_report()",
    )

