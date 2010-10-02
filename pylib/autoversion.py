import re
import subprocess
import datetime

class Error(Exception):
    pass

def _getstatusoutput(*command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

    return p.returncode, p.stdout.read().rstrip("\n")
    
def _git_rev_parse(commit):
    error, output = _getstatusoutput("git-rev-parse", "--verify", commit)
    if error:
        return None
    return output

def _get_commit_date(commit):
    error, output = _getstatusoutput("git-cat-file", "commit", commit)
    if error:
        raise Error("can't get commit log for `%s'" % commit)

    timestamp = int(re.search(r' (\d{10}) ', output).group(1))
    return datetime.date.fromtimestamp(timestamp)
    

def commit2version(commit):
    val = _git_rev_parse(commit)
    if val is None:
        raise Error("illegal commit `%s'" % commit)
    commit = val

    error = True
    error, version = _getstatusoutput("git-describe", commit)

    if not error:
        return version[1:]

    date = _get_commit_date(commit)
    return "0-%d.%d.%d-%s" % (date.year, date.month, date.day, commit[:8])

def version2commit(version):
    # easy street if its a version from git-describe
    commit = _git_rev_parse("v" + version)
    if commit:
        return commit
    
    m = re.match(r'^0-(\d\d\d\d)\.(\d\d?)\.(\d\d?)-([0-9a-f]{8})$', version)
    if not m:
        raise Error("illegal version `%s'" % version)

    year, month, day, shortcommit = m.groups()

    # if the commit is not ambigious - we're ok
    commit = _git_rev_parse(shortcommit)
    if commit:
        return commit

    def rev_parse_shortcommit(date, shortcommit):
        error, output = _getstatusoutput("git-rev-list", "--all")
        if error:
            raise Error("git-rev-list --all failed")

        revs = [ rev for rev in output.split("\n")
                 if rev.startswith(shortcommit) and date == _get_commit_date(rev) ]

        if not revs:
            raise Error("no matching commits")

        if len(revs) > 1:
            raise Error("more than one commit matches shortcommit and date")

        return revs[0]

    return rev_parse_shortcommit(datetime.date(year, month, day), shortcommit)

