import re
import commands
import datetime

class Error(Exception):
    pass

def _getstatusoutput(command, *args):
    command = command + " ".join([commands.mkarg(arg) for arg in args])
    return commands.getstatusoutput(command)

def _git_rev_parse(commit):
    error, output = _getstatusoutput("git-rev-parse --verify", commit)
    if error:
        return None
    return output

def _get_commit_date(commit):
    error, timestamp = _getstatusoutput("git-show --quiet --pretty=format:%at", commit)
    if error:
        raise Error("can't get timestamp for commit `%s'" % commit)
    timestamp = int(timestamp)
    
    return datetime.date.fromtimestamp(timestamp)
    

def commit2version(commit):
    val = _git_rev_parse(commit)
    if val is None:
        raise Error("illegal commit `%s'" % commit)
    commit = val
    
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
        error, output = _getstatusoutput("git-rev-list --all")
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

