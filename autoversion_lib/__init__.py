# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of AutoVersion
#
# AutoVersion is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import re

from time import gmtime
from calendar import timegm
import urllib.parse
from typing import Generator

from gitwrapper import Git, GitError  # type: ignore


class AutoverError(Exception):
    pass


class Describes:
    """Class that maps git describes to git commits and vice versa"""

    def _get_describes_commits(
            self,
            commits: list[str] | None = None
    ) -> list[tuple[str, str]]:
        if commits is None:
            commits = self.git.rev_list("--all")

        describes = list(
                map(urllib.parse.unquote, self.git.describe(*commits))
        )
        return list(zip(describes, commits))

    def __init__(
            self,
            git: Git,
            precache: bool = False,
            precache_commits: list[str] | None = None
    ) -> None:
        self.git = git

        self.map_describes_commits: dict[str, str] | None
        self.map_commits_describes: dict[str, str] | None

        if precache:
            describes_commits = self._get_describes_commits(precache_commits)
            self.map_describes_commits = dict(describes_commits)
            self.map_commits_describes = dict(
                    ((v[1], v[0]) for v in describes_commits)
            )
        else:
            self.map_describes_commits = None
            self.map_commits_describes = None

        self.precache = precache

    def describe2commit(self, describe: str) -> str | None:
        if self.precache:
            assert self.map_describes_commits is not None
            commit = self.map_describes_commits.get(describe)
        else:
            commit = self.git.rev_parse(describe)
        return commit

    def commit2describe(self, commit: str) -> str | None:
        if self.precache:
            assert self.map_commits_describes is not None
            return self.map_commits_describes.get(commit)

        describe = self.git.describe(commit)
        if describe:
            return urllib.parse.unquote(describe[0])

        return None


class Shorts:
    """Class that maps short-commits to commits"""

    def _get_commit_shorts(
            self,
            shortlen: int,
            commits: list[str] | None = None
    ) -> Generator[tuple[str, str], None, None]:
        if commits is None:
            commits = self.git.rev_list("--all")

        for commit in commits:
            yield commit[:shortlen], commit

    def __init__(
            self,
            git: Git,
            precache: bool = False,
            precache_commits: list[str] | None = None,
            precache_shortlen: int = 8
    ) -> None:
        self.git = git

        self.precache: dict[str, str | None]

        if precache:
            keyvals = self._get_commit_shorts(
                    precache_shortlen, precache_commits
            )
            precache_: dict[str, str | None]
            # don't resolve ambigious values (assign None to doubles)
            precache_ = {}
            for key, val in keyvals:
                if key in precache_:
                    precache_[key] = None
                else:
                    precache_[key] = val
            self.precache = precache_
        else:
            self.precache = {}

    def short2commit(self, short: str) -> str | None:
        """map a short commit to a commit.
        Returns None if a one-to-one mapping does not exist (I.e., non-existant
        or ambigious)
        """
        if self.precache:
            if short in self.precache:
                return self.precache[short]
            return None

        return self.git.rev_parse("--verify", short)


class Timestamps:
    """Class that maps git commits to timestamps"""

    def _get_commit_timestamps(self) -> Generator[tuple[str, int], None, None]:
        lines = self.git.rev_list("--pretty=format:%at", "--all")
        for i in range(0, len(lines), 2):
            commit = lines[i]
            if not commit.startswith("commit "):
                raise AutoverError(f"badly formatted line ({lines[i]})")
            commit = commit[len("commit "):]
            timestamp = int(lines[i + 1])

            yield commit, timestamp

    def __init__(self, git: Git, precache: bool = False) -> None:
        self.git = git
        self.precache: dict[str, int] = {}
        self.precache_commits: list[str] = []
        if precache:
            commit_timestamps = self._get_commit_timestamps()
            for commit, timestamp in commit_timestamps:
                self.precache[commit] = timestamp
                self.precache_commits.append(commit)

    def commit2timestamp(self, commit: str) -> int:
        if self.precache:
            return self.precache[commit]

        output = self.git.cat_file("commit", commit)
        m = re.search(r" (\d{9,10}) ", output)
        assert m is not None
        timestamp = int(m.group(1))
        return timestamp


class Autoversion:
    def __init__(self, path: str, precache: bool = False) -> None:
        try:
            git = Git(path)
        except GitError as e:
            raise AutoverError(f"failed to initialize gitwrapper: {e}")

        self.timestamps = Timestamps(git, precache)
        precache_commits = self.timestamps.precache_commits

        self.shorts = Shorts(git, precache, precache_commits=precache_commits)
        self.describes = Describes(
                git,
                precache,
                precache_commits=precache_commits
        )
        self.git = git

    def _resolve_ambigious_shortcommit(
            self,
            short: str,
            timestamp: int
    ) -> str:
        if not self.timestamps.precache:
            self.timestamps = Timestamps(self.git, precache=True)

        for commit, commit_timestamp in list(self.timestamps.precache.items()):
            if commit.startswith(short) and commit_timestamp == timestamp:
                return commit

        raise AutoverError("no matching commits")

    def version2commit(self, version: str) -> str:
        # easy street if its a version from git-describe
        if version.endswith("+0"):
            version = version[:-2]

        version = re.sub(
            r"(\+\d+\+g[0-9a-f]{7})$",
            lambda m: m.group(1).replace("+", "-"), version
        )

        commit = self.describes.describe2commit("v" + version)
        if commit:
            return commit

        m = re.match(
            r"^0\+(\d\d\d\d)\.(\d\d?)\.(\d\d?)\+(\d\d?)"
            r".(\d\d?).(\d\d?)\+([0-9a-f]{8})$",
            version,
        )
        if not m:
            commit = self.describes.describe2commit(version)
            if commit:
                return commit

            # look for describes that end with '/version'
            for desc, commit in self.describes._get_describes_commits():
                if (
                        desc.endswith(f"/{version}")
                        or desc.endswith(f"/v{version}")
                        or desc.endswith(f"/V{version}")
                ):
                    return commit

            raise AutoverError(f"illegal version `{version}'")

        year, month, day, hour, minu, sec, shortcommit = m.groups()

        # if the commit is not ambigious - we're ok
        commit = self.shorts.short2commit(shortcommit)
        if commit:
            return commit

        timestamp = timegm(
            (int(year), int(month), int(day), int(hour), int(minu), int(sec))
        )
        return self._resolve_ambigious_shortcommit(shortcommit, timestamp)

    def commit2version(self, commit: str) -> str:
        version = self.describes.commit2describe(commit)
        if version:
            m = re.search(r"(.*)(-\d+-g[0-9a-f]{7})$", version)
            if m:
                version = m.group(1) + m.group(2).replace("-", "+")
            elif not version[-1].isdigit():
                version += "+0"

            if version.startswith("v") or version.startswith("V"):
                return version[1:]
            # if includes a slash, assume that it's debian style
            # branch/tag handle (i.e. owner/tag or owner/ranch)
            # Note '/' is illegal in pkg name, so uses greedy match
            if "/" in version:
                version = version.rsplit("/", 1)[-1]
                if not version:
                    raise AutoverError(
                            "Illegal branchname for version generation:"
                            f" {version}"
                    )

            return version

        tm = gmtime(self.timestamps.commit2timestamp(commit))
        return "0+{}.{}.{}+{:02d}.{:02d}.{:02d}+{}".format(
            tm.tm_year,
            tm.tm_mon,
            tm.tm_mday,
            tm.tm_hour,
            tm.tm_min,
            tm.tm_sec,
            commit[:8],
        )


# convenience functions
def version2commit(path: str, version: str) -> str:
    return Autoversion(path).version2commit(version)


def commit2version(path: str, commit: str) -> str:
    return Autoversion(path).commit2version(commit)
