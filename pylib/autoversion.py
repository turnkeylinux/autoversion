import re
import subprocess
from time import gmtime
from calendar import timegm

class Error(Exception):
    pass

def _getstatusoutput(*command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

    return p.returncode, p.stdout.read().rstrip("\n")

def _getoutput(*command):
    error, output = _getstatusoutput(*command)
    if error:
        raise Error("command failed with exitcode=%d: %s" % (error, " ".join(command)))
    return output

def git_rev_parse(commit):
    # skip expensive git-rev-parse if given a full commit id
    if re.match('[0-9a-f]{40}$', commit):
        return commit

    error, output = _getstatusoutput("git-rev-parse", "--verify", commit)
    if error:
        return None
    return output

class Describes:
    """Class that maps git describes to git commits and vice versa"""
    
    @staticmethod
    def _get_describes_commits(revs=None):
        if revs is None:
            revs = _getoutput("git-rev-list", "--all").split("\n")

        command = ["git-describe"]
        command.extend(revs)

        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        describes = p.stdout.read().rstrip("\n").split("\n")
        return zip(describes, revs)

    def __init__(self, precache=False, revs=None):

        if precache:
            describes_commits = self._get_describes_commits(revs)
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

class Autoversion:
    Error = Error

    @staticmethod
    def _get_map_commits_times():
        output = _getoutput("git-rev-list", "--pretty=format:%at", "--all")

        d = {}
        entries = ( entry.strip().split("\n") for entry in output.split("commit ")[1:] )
        for entry in entries:
            commit = entry[0]
            timestamp = int(entry[1])

            d[commit] = timestamp
        return d

    def __init__(self, precache=False):
        self.describes = Describes(precache)
        if precache:
            self.map_commits_times = self._get_map_commits_times()
        else:
            self.map_commits_times = None

        self.precache = precache

    def _rev_parse_shortcommit(self, timestamp, shortcommit):
        if not self.map_commits_times is None:
            self.map_commits_times = self._get_map_commits_times()
            
        for commit, commit_timestamp in self.map_commits_times.items():
            if commit.startswith(shortcommit) and commit_timestamp == timestamp:
                return commit

        raise Error("no matching commits")
    
    def version2commit(self, version):
        # easy street if its a version from git-describe
        version = re.sub(r'(\+\d+\+g[0-9a-f]{7})$',
                         lambda m: m.group(1).replace("+", "-"),
                         version)

        commit = self.describes.describe2commit("v" + version)
        if commit:
            return commit
        
        m = re.match(r'^0\+(\d\d\d\d)\.(\d\d?)\.(\d\d?)\+(\d\d?):(\d\d?):(\d\d?)\+([0-9a-f]{8})$', version)
        if not m:
            commit = self.describes.describe2commit(version)
            if commit:
                return commit

            raise Error("illegal version `%s'" % version)

        year, month, day, hour, min, sec, shortcommit = m.groups()

        # if the commit is not ambigious - we're ok
        commit = git_rev_parse(shortcommit)
        if commit:
            return commit

        timestamp = timegm((int(year), int(month), int(day), int(hour), int(min), int(sec)))
        return self._rev_parse_shortcommit(timestamp, shortcommit)
    
    def _get_commit_time(self, commit):
        if self.map_commits_times:
            return self.map_commits_times[commit]
        
        output = _getoutput("git-cat-file", "commit", commit)

        timestamp = int(re.search(r' (\d{10}) ', output).group(1))
        return timestamp

    def commit2version(self, commit):
        version = self.describes.commit2describe(commit)
        if version:
            version = re.sub(r'(-\d+-g[0-9a-f]{7})$',
                             lambda m: m.group(1).replace("-", "+"),
                             version)
            if version.startswith("v"):
                return version[1:]
            return version

        tm = gmtime(self._get_commit_time(commit))
        return "0+%d.%d.%d+%02d:%02d:%02d+%s" % (tm.tm_year, tm.tm_mon, tm.tm_mday,
                                                 tm.tm_hour, tm.tm_min, tm.tm_sec,
                                                 commit[:8])
    
# convenience functions
def version2commit(version):
    return Autoversion().version2commit(version)

def commit2version(commit):
    return Autoversion().commit2version(commit)
