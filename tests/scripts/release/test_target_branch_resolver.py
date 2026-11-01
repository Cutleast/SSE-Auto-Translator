"""
Copyright (c) Cutleast
"""

import pytest

from scripts.release.release_error import ReleaseError
from scripts.release.target_branch_resolver import TargetBranchResolver


class TestTargetBranchResolver:
    """
    Tests `scripts.release.target_branch_resolver.TargetBranchResolver`.
    """

    def test_single_branch_at_tagged_commit(self) -> None:
        """
        Tests that the only branch pointing at the tagged commit is selected.
        """

        # when
        branch: str = TargetBranchResolver.resolve(
            ["release/v3.2"], ["release/v3.2", "master"], "master"
        )

        # then
        assert branch == "release/v3.2"

    def test_release_branch_preferred_when_merged_by_fast_forward(self) -> None:
        """
        Tests that the release branch wins if the default branch was fast-forwarded to
        the same commit.
        """

        # when
        branch: str = TargetBranchResolver.resolve(
            ["master", "release/v3.2"], ["master", "release/v3.2"], "master"
        )

        # then
        assert branch == "release/v3.2"

    def test_release_branch_that_moved_on(self) -> None:
        """
        Tests that a release branch which already contains newer commits is selected.
        """

        # when
        branch: str = TargetBranchResolver.resolve(
            [], ["release/v3.2", "master"], "master"
        )

        # then
        assert branch == "release/v3.2"

    def test_hotfix_tag_on_default_branch(self) -> None:
        """
        Tests that a tag on the default branch alone targets the default branch.
        """

        # when
        branch: str = TargetBranchResolver.resolve([], ["master"], "master")

        # then
        assert branch == "master"

    @pytest.mark.parametrize(
        ("tip_branches", "containing_branches"),
        [
            (["feature/a", "feature/b"], ["feature/a", "feature/b"]),
            (
                ["master", "release/v3.2", "release/v3.3"],
                ["release/v3.2", "release/v3.3"],
            ),
            ([], ["release/v3.2", "release/v3.3"]),
            ([], ["feature/a", "master"]),
            ([], []),
        ],
    )
    def test_ambiguous_or_unknown_branch_is_rejected(
        self, tip_branches: list[str], containing_branches: list[str]
    ) -> None:
        """
        Tests that ambiguous or missing branches stop the release.

        Args:
            tip_branches (list[str]): Branches whose tip is the tagged commit.
            containing_branches (list[str]): Branches containing the tagged commit.
        """

        # then
        with pytest.raises(ReleaseError):
            TargetBranchResolver.resolve(tip_branches, containing_branches, "master")
