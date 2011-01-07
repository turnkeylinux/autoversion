import re
import subprocess
from time import gmtime
from calendar import timegm
import urllib

class Error(Exception):
    pass

def _getstatusoutput(*command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    return p.returncode, output.rstrip("\n")

def _getoutput(*command):
    error, output = _getstatusoutput(*command)
    if error:
        raise Error("command failed with exitcode=%d: %s" % (error, " ".join(command)))
    return output

def git_rev_parse(rev):
    error, commit = _getstatusoutput("git-rev-parse", "--verify", rev)
    if error:
        return None
    
    return commit

class Describes:
    """Class that maps git describes to git commits and vice versa"""
    
    @staticmethod
    def _get_describes_commits(commits=None):
        if commits is None:
            commits = _getoutput("git-rev-list", "--all").split("\n")

        command = ["git-describe"]
        command.extend(commits)

        status, output = _getstatusoutput(*command)

        describes = output.split("\n")
        return zip(describes, commits)

    def __init__(self, precache=False, precache_commits=None):
        if precache:
            describes_commits = self._get_describes_commits(precache_commits)
            self.map_describes_commits = dict(describes_commits)
            self.map_commits_describes = dict(( (v[1], v[0]) for v in describes_commits ))
        else:
            self.map_describes_commits = None
            self.map_commits_describes = None

        self.precache = precache
    
    def describe2commit(self, describe):
        if self.precache:
            commit = self.map_describes_commits.get(describe)
        else:
            commit = git_rev_parse(describe)
        return commit

    def commit2describe(self, commit):
        if self.precache:
            return self.map_commits_describes.get(commit)

        error, describe = _getstatusoutput("git-describe", commit)
        if not error:
            return describe

        return None

class Shorts:
    """Class that maps short-commits to commits"""
    def _get_commit_shorts(self, shortlen, commits=None):
        if commits is None:
            commits = _getoutput("git-rev-list", "--all").split("\n")
        
        for commit in commits:
            yield commit[:shortlen], commit

    def __init__(self, precache=False, precache_commits=None, precache_shortlen=8):
        if precache:
            keyvals = self._get_commit_shorts(precache_shortlen, precache_commits)

            # don't resolve ambigious values (assign None to doubles)
            precache = {}
            for key, val in keyvals:
                if key in precache:
                    precache[key] = None
                else:
                    precache[key] = val
            self.precache = precache
        else:
            self.precache = {}

    def short2commit(self, short):
        """map a short commit to a commit.
        Returns None if a one-to-one mapping does not exist (I.e., non-existant or ambigious)
        """
        if self.precache:
            if short in self.precache:
                return self.precache[short]
            return None

        return git_rev_parse(short)

class Timestamps:
    """Class that maps git commits to timestamps"""

    @staticmethod
    def _get_commit_timestamps():
        output = _getoutput("git-rev-list", "--pretty=format:%at", "--all")

        entries = ( entry.strip().split("\n") for entry in output.split("commit ")[1:] )
        for entry in entries:
            commit = entry[0]
            timestamp = int(entry[1])

            yield commit, timestamp

    def __init__(self, precache=False):
        self.precache = {}
        self.precache_commits = []
        if precache:
            commit_timestamps = self._get_commit_timestamps()
            for commit, timestamp in commit_timestamps:
                self.precache[commit] = timestamp
                self.precache_commits.append(commit)
                
    def commit2timestamp(self, commit):
        if self.precache:
            return self.precache[commit]
        
        output = _getoutput("git-cat-file", "commit", commit)
        timestamp = int(re.search(r' (\d{10}) ', output).group(1))
        return timestamp

class Autoversion:
    Error = Error

    def __init__(self, precache=False):
        self.timestamps = Timestamps(precache)
        precache_commits = self.timestamps.precache_commits
        
        self.shorts = Shorts(precache, precache_commits=precache_commits)
        self.describes = Describes(precache, precache_commits=precache_commits)

    def _resolve_ambigious_shortcommit(self, short, timestamp):
        if not self.timestamps.precache:
            self.timestamps = Timestamps(precache=True)
            
        for commit, commit_timestamp in self.timestamps.precache.items():
            if commit.startswith(short) and commit_timestamp == timestamp:
                return commit

        raise Error("no matching commits")
    
    def version2commit(self, version):
        # easy street if its a version from git-describe
        version = re.sub(r'(\+\d+\+g[0-9a-f]{7})$',
                         lambda m: m.group(1).replace("+", "-"),
                         version)
        version = urllib.quote(version)
        
        commit = self.describes.describe2commit("v" + version)
        if commit:
            return commit
        
        m = re.match(r'^0\+(\d\d\d\d)\.(\d\d?)\.(\d\d?)\+(\d\d?).(\d\d?).(\d\d?)\+([0-9a-f]{8})$', version)
        if not m:
            commit = self.describes.describe2commit(version)
            if commit:
                return commit

            raise Error("illegal version `%s'" % version)

        year, month, day, hour, min, sec, shortcommit = m.groups()

        # if the commit is not ambigious - we're ok
        commit = self.shorts.short2commit(shortcommit)
        if commit:
            return commit

        timestamp = timegm((int(year), int(month), int(day), int(hour), int(min), int(sec)))
        return self._resolve_ambigious_shortcommit(shortcommit, timestamp)
    
    def commit2version(self, commit):
        version = self.describes.commit2describe(commit)
        if version:
            version = urllib.unquote(version)
            version = re.sub(r'(-\d+-g[0-9a-f]{7})$',
                             lambda m: m.group(1).replace("-", "+"),
                             version)
            if version.startswith("v"):
                return version[1:]
            return version

        tm = gmtime(self.timestamps.commit2timestamp(commit))
        return "0+%d.%d.%d+%02d.%02d.%02d+%s" % (tm.tm_year, tm.tm_mon, tm.tm_mday,
                                                 tm.tm_hour, tm.tm_min, tm.tm_sec,
                                                 commit[:8])
    
# convenience functions
def version2commit(version):
    return Autoversion().version2commit(version)

def commit2version(commit):
    return Autoversion().commit2version(commit)
