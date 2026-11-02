"""
Copyright (c) Cutleast
"""

import subprocess

from .release_error import ReleaseError


class TargetBranchResolver:
    """
    Determines the branch a release tag was created on.

    Git does not record the branch of a tag, so it is derived from the remote branches:

    1. A branch whose tip is the tagged commit (the usual case right after tagging).
       If several branches point at it, exactly one of them must be a release branch.
    2. Otherwise, the only release branch that contains the tagged commit.
    3. Otherwise, the default branch if it is the only branch containing the commit.

    Any other situation is ambiguous and stops the release before anything is
    published.
    """

    RELEASE_BRANCH_PREFIX: str = "release/"
    """Prefix of release branches."""

    REMOTE: str = "origin"
    """Name of the remote whose branches are inspected."""

    @staticmethod
    def resolve(
        tip_branches: list[str], containing_branches: list[str], default_branch: str
    ) -> str:
        """
        Selects the target branch from the branches related to the tagged commit.

        Args:
            tip_branches (list[str]): Branches whose tip is the tagged commit.
            containing_branches (list[str]): Branches containing the tagged commit.
            default_branch (str): Name of the repository's default branch.

        Raises:
            ReleaseError: No branch or more than one candidate branch qualifies.

        Returns:
            str: Name of the target branch.
        """

        if len(tip_branches) == 1:
            return tip_branches[0]

        if tip_branches:
            release_tips: list[str] = TargetBranchResolver.__release_branches(
                tip_branches
            )
            if len(release_tips) == 1:
                return release_tips[0]

            raise ReleaseError(
                "The tagged commit is the tip of several branches and the target "
                f"branch is ambiguous: {', '.join(sorted(tip_branches))}."
            )

        release_branches: list[str] = TargetBranchResolver.__release_branches(
            containing_branches
        )
        if len(release_branches) == 1:
            return release_branches[0]

        if release_branches:
            raise ReleaseError(
                "The tagged commit is contained in several release branches: "
                f"{', '.join(sorted(release_branches))}."
            )

        if containing_branches == [default_branch]:
            return default_branch

        raise ReleaseError(
            "Could not determine the branch of the tagged commit. Branches containing "
            f"it: {', '.join(sorted(containing_branches)) or 'none'}."
        )

    @staticmethod
    def resolve_from_git(commit: str, default_branch: str) -> str:
        """
        Determines the target branch of a commit from the fetched remote branches.

        Args:
            commit (str): The tagged commit.
            default_branch (str): Name of the repository's default branch.

        Raises:
            ReleaseError: The target branch is ambiguous or cannot be determined.

        Returns:
            str: Name of the target branch.
        """

        return TargetBranchResolver.resolve(
            TargetBranchResolver.__remote_branches("--points-at", commit),
            TargetBranchResolver.__remote_branches("--contains", commit),
            default_branch,
        )

    @staticmethod
    def __release_branches(branches: list[str]) -> list[str]:
        """
        Filters release branches.

        Args:
            branches (list[str]): Branch names.

        Returns:
            list[str]: The release branches among them.
        """

        return [
            branch
            for branch in branches
            if branch.startswith(TargetBranchResolver.RELEASE_BRANCH_PREFIX)
        ]

    @staticmethod
    def __remote_branches(filter_option: str, commit: str) -> list[str]:
        """
        Lists remote branches matching a `git branch` filter.

        Args:
            filter_option (str): Either `--points-at` or `--contains`.
            commit (str): The commit to filter for.

        Returns:
            list[str]: Branch names without the remote prefix.
        """

        output: str = subprocess.run(
            [
                "git",
                "branch",
                "--remotes",
                "--format=%(refname:short)",
                filter_option,
                commit,
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        prefix: str = f"{TargetBranchResolver.REMOTE}/"
        branches: list[str] = []
        for line in output.splitlines():
            name: str = line.strip()
            # Skip the symbolic `origin/HEAD` reference, which is shown as `origin`.
            if not name.startswith(prefix) or name == f"{prefix}HEAD":
                continue
            branches.append(name.removeprefix(prefix))

        return branches
