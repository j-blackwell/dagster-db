from dunamai import Version
import subprocess
import toml


def _check_clean_git():
    status_output = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    changes = status_output.stdout.splitlines()
    if len(changes) > 0:
        print(f"Following files have changes {changes}")
        print("Ensure git tree is clean")
        SystemExit("Exiting...")


def _update_version() -> str:
    v = Version.from_git()
    print(f"Current version: {v.base}")
    print("How would you like to bum the version?")
    print("  [0] Major")
    print("  [1] Minor")
    print("  [2] Patch (default)")
    print("  [3] Manual")
    bump_type = input("")

    if bump_type == "":
        bump_type = "2"

    if bump_type not in {"0", "1", "2", "3"}:
        raise ValueError(f"Incorrect selection {bump_type}")
    elif bump_type == "3":
        v_new = input("Enter new version in format {Major}.{Minor}.{Patch}:\n")
        return v_new

    bump_type = int(bump_type)
    v_list = [int(x) for x in v.base.split(".")]
    v_list[bump_type] += 1

    if bump_type < 2:
        for x in range(bump_type, 2):
            v_list[x + 1] = 0

    v_new = ".".join(str(x) for x in v_list)
    print(f"New version: {v_new}")
    return v_new


def _update_pyproject_toml(v_new: str):
    with open("pyproject.toml", "r") as f:
        data = toml.load(f)

    data["project"]["version"] = v_new

    with open("pyproject.toml", "w") as f:
        toml.dump(data, f)


def _git_commit_and_tag(v_new: str):
    """Commit version update, create a Git tag, and push it."""
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True, check=True
    )
    current_message = result.stdout.strip()
    try:
        subprocess.run(["git", "add", "pyproject.toml"], check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "--amend",
                "-m",
                f"{current_message}\n\nversion({v_new})",
            ],
            check=True,
        )
        subprocess.run(["git", "tag", f"v{v_new}"], check=True)
        subprocess.run(["git", "push", "--force-with-lease"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)
        print(f"Successfully tagged and pushed version {v_new}.")
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        SystemExit("Exiting...")


def bump():
    _check_clean_git()
    v_new = _update_version()
    _update_pyproject_toml(v_new)
    _git_commit_and_tag(v_new)
