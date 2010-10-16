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

def _get_commit_gmtime(commit):
    error, output = _getstatusoutput("git-cat-file", "commit", commit)
    if error:
        raise Error("can't get commit log for `%s'" % commit)

    timestamp = int(re.search(r' (\d{10}) ', output).group(1))
    return gmtime(timestamp)
    
def commit2version(commit):
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

    tm = _get_commit_gmtime(commit)
    return "0+%d.%d.%d+%02d:%02d:%02d+%s" % (tm.tm_year, tm.tm_mon, tm.tm_mday,
                                             tm.tm_hour, tm.tm_min, tm.tm_sec,
                                             commit[:8])

def _rev_parse_shortcommit(timestamp, shortcommit):
    error, output = _getstatusoutput("git-rev-list", "--pretty=format:%at", "--all")
    if error:
        raise Error("git-rev-list failed")

    for entry in output.split("commit ")[1:]:
        commit, commit_timestamp = entry.strip().split("\n")
        commit_timestamp = int(commit_timestamp)

        if commit.startswith(shortcommit) and commit_timestamp == timestamp:
            return commit

    raise Error("no matching commits")

def version2commit(version):
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
    return _rev_parse_shortcommit(timestamp, shortcommit)

