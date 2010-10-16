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

def _git_rev_parse(commit):
    # skip expensive git-rev-parse if given a full commit id
    if re.match('[0-9a-f]{40}$', commit):
        return commit

    error, output = _getstatusoutput("git-rev-parse", "--verify", commit)
    if error:
        return None
    return output

class Autoversion:
    Error = Error

    @staticmethod
    def _get_commit_times_map():
        error, output = _getstatusoutput("git-rev-list", "--pretty=format:%at", "--all")
        if error:
            raise Error("git-rev-list failed")

        d = {}
        entries = ( entry.strip().split("\n") for entry in output.split("commit ")[1:] )
        for entry in entries:
            commit = entry[0]
            timestamp = int(entry[1])

            d[commit] = timestamp
        return d
    
    def __init__(self, precache=False):
        if precache:
            self.commit_times_map = self._get_commit_times_map()
        else:
            self.commit_times_map = None

    def _rev_parse_shortcommit(self, timestamp, shortcommit):
        if not self.commit_times_map is None:
            self.commit_times_map = self._get_commit_times_map()
            
        for commit, commit_timestamp in self.commit_times_map.items():
            if commit.startswith(shortcommit) and commit_timestamp == timestamp:
                return commit

        raise Error("no matching commits")

    def version2commit(self, version):
        # easy street if its a version from git-describe
        version = re.sub(r'(\+\d+\+g[0-9a-f]{7})$',
                         lambda m: m.group(1).replace("+", "-"),
                         version)
        commit = _git_rev_parse("v" + version)
        if commit:
            return commit

        m = re.match(r'^0\+(\d\d\d\d)\.(\d\d?)\.(\d\d?)\+(\d\d?):(\d\d?):(\d\d?)\+([0-9a-f]{8})$', version)
        if not m:
            commit = _git_rev_parse(version)
            if commit:
                return commit

            raise Error("illegal version `%s'" % version)

        year, month, day, hour, min, sec, shortcommit = m.groups()

        # if the commit is not ambigious - we're ok
        commit = _git_rev_parse(shortcommit)
        if commit:
            return commit

        timestamp = timegm((int(year), int(month), int(day), int(hour), int(min), int(sec)))
        return self._rev_parse_shortcommit(timestamp, shortcommit)
    
    def _get_commit_time(self, commit):
        if self.commit_times_map:
            return self.commit_times_map[commit]
        
        error, output = _getstatusoutput("git-cat-file", "commit", commit)
        if error:
            raise Error("can't get commit log for `%s'" % commit)

        timestamp = int(re.search(r' (\d{10}) ', output).group(1))
        return timestamp

    def commit2version(self, commit):
        val = _git_rev_parse(commit)
        if val is None:
            raise Error("illegal commit `%s'" % commit)
        commit = val

        error = True
        error, version = _getstatusoutput("git-describe", commit)

        if not error:
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
