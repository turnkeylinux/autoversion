<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="51" clone_windows="0"/>
<globals body_outline_ratio="0.5">
	<global_window_position top="0" left="604" height="951" width="666"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="zaril.20101001195902" a="E"><vh>Project</vh>
<v t="zaril.20101001201018" a="E"><vh>development log</vh>
<v t="zaril.20101014055754"><vh>research debian versions</vh></v>
<v t="zaril.20101001195902.1" a="E"><vh>design</vh>
<v t="zaril.20101001195902.2" a="E"><vh>brainstorming</vh></v>
<v t="zaril.20101001195902.3"><vh>terminology</vh></v>
<v t="zaril.20101001195902.5"><vh>cli syntax and psuedo-logic</vh></v>
<v t="zaril.20101001195902.6"><vh>use cases</vh></v>
</v>
<v t="zaril.20101001201018.3" a="E"><vh>implementation</vh>
<v t="zaril.20101014064439" a="M"><vh>implement basic functionality</vh></v>
<v t="zaril.20101014064439.1" a="M"><vh>optimize autoversion</vh></v>
<v t="zaril.20101014064538" a="M"><vh>upgrade autoversion's autoversioning mechanism</vh></v>
<v t="zaril.20101014055955" a="M"><vh>bug: bad version returned when tag doesn't start with v</vh></v>
<v t="zaril.20101014063204.1" a="EM"><vh>allow autoversion to be used with forks</vh></v>
<v t="zaril.20101014063204" a="ETV"><vh>add revision count to untagged autoversions</vh>
<v t="zaril.20101016095956"><vh>bench.py</vh></v>
</v>
</v>
</v>
<v t="zaril.20101001200109.1"><vh>bugs/wishlist</vh></v>
</v>
</vnodes>
<tnodes>
<t tx="zaril.20101001195902">@nocolor
</t>
<t tx="zaril.20101001195902.1"></t>
<t tx="zaril.20101001195902.2">scan deltas since last scan
    yes, to detect which paths changed
        run sourceversion-list on them

    inefficient alternative
        if anything changed, run sourceversion-list on all paths
   
remember - we're using branches for development
    don't touch working directory?
        this way if we have a catastrophic failure - no lost data
    clone repository for all operations
    checkout correct branch to a different working directory?

fixed untagged auto-versioning
    its unclear with untagged versions what is the newest pacakge (sub-day precision)
        add hour/minute/second precision?
        add daily count?
            count all commits today + 1

    need to change auto-version so that untagged versions always precede tagged versions
        e.g., tagged version = 0.0.1-1-g472ece7
            package--2010-09-23.1.33879c21
            package-0-2010-09-23.1.33879c21 
            package-0000-2010-09-23.1.33879c21
        

tag-based auto-versioning
    for single projects only (debian/ in top directory)
        tags are per-repository
        reminder: we're using git-describe

    separate program for mappings versions/commits vice versa
        map commits to versions
        map versions from commits (rev list -&gt; versions)
            initially map HEAD -&gt; 

    logic
        current state saved in a temporary commit
        map version to commit
        seek to commit
        autogenerate a changelog
        build package
        restore original state

for non-tagged versioning pool doesn't know how to generate versions
    it only knows how to read the changelog
        first line for every changelog commit -&gt; thats the version

    committing changes to more than one package at a time will produce a similar changelog entry
        in both packages

    moving or copying a source directory looses its history of old versions
        git-log debian/changelog
            won't produce 

multiple Debian sources in Sumo arena
    versions based on changelog entries
        chanko brings changelog into overlay on first import
    
    use hooks to auto-generate changelog entry?
        append turnkey&lt;N&gt;?
            configurable string 
                environment variable

            (could also be .0)

        provide some method of supressing the changelog?
            touch debian/changelog 
                if you've changed it yourself, it won't auto-update

    provide user a tool to choose to update the changelog?

    develop Sumo seek capability and commit hooks

multiple Debian sources in Git repositories
    
    debian/changelog based versioning

    changes don't necessarily generate a new version
        you have to change the changelog for a new version to be created
        
        a list of changelog commits generated
            seek to those commits for the contents of that package version

            allow us to develop and commit to packages without effecting pool
                test packages locally before changing the commit log 


          
* QUESTIONS

Q: is tagged auto-versioning embedded or do we calculate the tagged auto-version independently?
    we also need the ability to seek back to arbitrary earlier versions
        seeking back to the tag is trivial
        seeking back to the offset is simple if unreliable (includes short commit id)
</t>
<t tx="zaril.20101001195902.3">tagged autoversion := tag based autoversion (e.g., the version tag created by git-tag-release)
    version calculation based on git-describe (fast)

    format
        &lt;tag&gt;
        &lt;tag&gt;-&lt;revisions&gt;-&lt;shortcommit&gt;

        examples:        
            1.0
            1.0-4-gff3c39c
    
untagged autoversion := autoversion
    version may be calculated more slowly
    untagged autoversion should always be lower than a tagged autoversion

    format
        0-&lt;YYYY.MM.DD&gt;-&lt;shortcommit&gt;

        examples:
            0-2010.10.07-f55f9ecd
</t>
<t tx="zaril.20101001195902.5">autoversion &lt;commit&gt; [ ... ]
autoversion -r &lt;version&gt; [ ... ]

Options:
  -r --reverse          map version to git commit



</t>
<t tx="zaril.20101001195902.6"># print the latest version
autoversion HEAD

# print the latest version and previous version before that
autoversion HEAD HEAD^

# print the commit of the specified version
autoversion -r 0-2010.10.07-f55f9ecd

# print a list of all versions 
autoversion $(git-rev-list --all)

# stress test autoversion
autoversion -r $(autoversion $(git-rev-list --all))</t>
<t tx="zaril.20101001200109.1"></t>
<t tx="zaril.20101001201018"></t>
<t tx="zaril.20101001201018.3"></t>
<t tx="zaril.20101014055754">SUMMARY
    format of debian version
        [epoch:]upstream_version[-debian_revision]

    the debian revision is split at the last -

RESOURCE: http://people.debian.org/~calvin/unofficial/

The Debian package version number is parsed from the top entry of debian/changelog, eg. mypackage (1.0-0joe1) unstable; urgency=low. The `-0joe1' is the debian release number. Subsequent releases have release numbers `-0joe2', `-0joe3', etc.
If there is already an official package, for example with version `1.0-4', then use `1.0-4joe1'.
You can compare versions with dpkg, see the dpkg(8) manpage for more info.

advanced package versioning:

    * The package version is a beta version or release candidate, for example 1.0b1 or 1.0rc2
      Problems will arise because dpkg will consider the final version 1.0 lower than the beta or release candidate version. The solution is to use a version like 0.99+1.0rc2-0joe1 which uses a lower version than 1.0 (0.99) and joins the release candidate version with a plus sign. This way the final version is greater than the previous one: 0.99+1.0rc2-0joe1 &lt; 1.0-0joe1.
    * The new upstream version is lower than the previous one.
      How can this happen? A simple typo for example. Instead of 1.0 someone uploaded the package as version 10.0. Now the new upstream version 1.1 is not greater than the last one. Solution is to use an epoch: 10.0-0joe1 &lt; 1:1.1-0joe1. See the Debian Policy epoch entry for an explanation.

RESOURCE: http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version

5.6.12 Version

The version number of a package. The format is: [epoch:]upstream_version[-debian_revision]

The three components here are:

epoch

    This is a single (generally small) unsigned integer. It may be omitted, in which case zero is assumed. If it is omitted then the upstream_version may not contain any colons.

    It is provided to allow mistakes in the version numbers of older versions of a package, and also a package's previous version numbering schemes, to be left behind.

upstream_version

    This is the main part of the version number. It is usually the version number of the original ("upstream") package from which the .deb file has been made, if this is applicable. Usually this will be in the same format as that specified by the upstream author(s); however, it may need to be reformatted to fit into the package management system's format and comparison scheme.

    The comparison behavior of the package management system with respect to the upstream_version is described below. The upstream_version portion of the version number is mandatory.

    The upstream_version may contain only alphanumerics[33] and the characters . + - : (full stop, plus, hyphen, colon) and should start with a digit. If there is no debian_revision then hyphens are not allowed; if there is no epoch then colons are not allowed.

debian_revision

    This part of the version number specifies the version of the Debian package based on the upstream version. It may contain only alphanumerics and the characters + and . (plus and full stop) and is compared in the same way as the upstream_version is.

    It is optional; if it isn't present then the upstream_version may not contain a hyphen. This format represents the case where a piece of software was written specifically to be turned into a Debian package, and so there is only one "debianization" of it and therefore no revision indication is required.

    It is conventional to restart the debian_revision at 1 each time the upstream_version is increased.

    The package management system will break the version number apart at the last hyphen in the string (if there is one) to determine the upstream_version and debian_revision. The absence of a debian_revision compares earlier than the presence of one (but note that the debian_revision is the least significant part of the version number).

The upstream_version and debian_revision parts are compared by the package management system using the same algorithm:

The strings are compared from left to right.

First the initial part of each string consisting entirely of non-digit characters is determined. These two parts (one of which may be empty) are compared lexically. If a difference is found it is returned. The lexical comparison is a comparison of ASCII values modified so that all the letters sort earlier than all the non-letters.

Then the initial part of the remainder of each string which consists entirely of digit characters is determined. The numerical values of these two parts are compared, and any difference found is returned as the result of the comparison. For these purposes an empty string (which can only occur at the end of one or both version strings being compared) counts as zero.

These two steps (comparing and removing initial non-digit strings and initial digit strings) are repeated until a difference is found or both strings are exhausted.

Note that the purpose of epochs is to allow us to leave behind mistakes in version numbering, and to cope with situations where the version numbering scheme changes. It is not intended to cope with version numbers containing strings of letters which the package management system cannot interpret (such as ALPHA or pre-), or with silly orderings (the author of this manual has heard of a package whose versions went 1.1, 1.2, 1.3, 1, 2.1, 2.2, 2 and so forth). </t>
<t tx="zaril.20101014055955"></t>
<t tx="zaril.20101014063204">IDEAS
    revision counts
        calculate revision count for that day
    
        calculate revision count for all commits
            add global revision count to each anonymous version
                0+2010.10.16+4ca0d043 -&gt; 0+23+2010.10.16+4ca0d043

        GOTCHA: you can't assign reliable index numbers to commits in a distributed VCS
            post-merge the autoversions would suddenly be different
        
    increase precision of timestamp? 
        add numeric timestamp
            1192522383.2392991

            0+2010.10.16+4ca0d043 -&gt; 0+2010.10.16+1192522383.23+4ca0d043

        add readable precision
            0+2010.10.16+4ca0d043 -&gt; 0+2010.10.16+08:29:44+4ca0d043
                looks better

          
    optimizations
        motivation - autoversion will be the bottleneck for verseek -l in git-single

        we'll need to turn autoversion.py into a class
            store internal caches

        optimize operation for multiple lookups by storing the rev-list internally
            if we store rev-list in a hash -&gt; even faster lookups
    
        while we're at it, we can optimize get_commit_date() for multiple lookups too

    what about merges?
        git-rev-list topo-order


    0+2010.10.16+4ca0d043 -&gt; 0+23+2010.10.16+4ca0d043
    
E: git-rev-list --topo-order post merging
    the `index' would change following a merge

Q: how do I get timezone-neutral timestamps?
A: the unixtimestamp is always neutral time.time() 

Q: how do I turn this back to a timestamp?
A: calendar.timegm is the inverse of time.gmtime
        e.g., 
            calendar.timegm(time.gmtime()[:6])

    so simply parse the autoversion to a tuple and push it into calendar.timegm
        0+2010.10.16+08:29:44+4ca0d043

git-rev-list --pretty=format:%at HEAD

parse with
    dict([ entry.strip().split("\n") for entry in commands.getoutput("git-rev-list --pretty=format:%at HEAD").split("commit ")[1:]  ])
</t>
<t tx="zaril.20101014063204.1">IDEAS
    replace - with +
        why not ~?
            according to DPM ~ is illegal in versions
                allowed: alphanumerics . + and -
    
            also ~ &gt; . (in python, but not according to dpkg --compare-versions)
    
    debian revision should only be for forked projects 
        non-forked projects shouldn't have debian revisions

example tags
    1.0
        1.0+13+gff3c39c

    1.0-3turnkey
        1.0-3turnkey+13+gff3c39c

anonymous tags
    0+2010.10.14+d3fa6327

logic
    commit -&gt; version
        if git-describe returns a matching pattern:
            replace the two last - with +
    
    version -&gt; commit
        if we match the pattern:
            replace two last + with -
            pass to git-describe</t>
<t tx="zaril.20101014064439"></t>
<t tx="zaril.20101014064439.1">time autoversion -r $(autoversion $(git-rev-list --all)) &gt; /dev/null
	down to 1.32 for pyproject
		3.64 for covin

	optimizations shaved saved two seconds for covin
		40% improvement

	full optimizations (including multiple arguments on command line)
		20 seconds vs 3.6 seconds

* optimization ideas
don't rev_parse a full commit

don't output to stdout
	saves a second!

precompiling regexps
	does nothing

don't use getstatusoutput, use Popen
	neglible improvement

use git-cat-file instead of git-show
	slight improvement

don't use --verify flag in git-rev-parse?
	nothing

Q: how much does git-describe take?
1.42 vs 2.32: 1 second

Q: how much does git-show take?
1.4 vs 0.5: 1 second

Q: how much does git-rev-parse?
A: 0.5 seconds
	no different between --verify and no --verify
	
* running a profiler on the result
python /usr/lib/python2.4/profile.py -s cumulative /turnkey/projects/autoversion/pylib/cmd_autoversion.py $(git-rev-list --all)

* autoversion stress test:
git-rev-list --all |xargs -n1 autoversion | xargs -n1 autoversion -r

time autoversion -r $(autoversion $(git-rev-list --all))


</t>
<t tx="zaril.20101014064538">apply patches
    autoversion.diff
    autoversion-disabled.diff

GOTCHA: circular dependency
    verseek depends on autoversion
    to build autoversion pool uses verseek

    SOLUTION: 

        create debian/changelog manually (with bogus version?) to `bootstrap' autoversion
            install manually built binary into fabrication environment
                rebuild autoversion with itself
</t>
<t tx="zaril.20101016095956">import os
import time

def bench(f, howmany):
    start = time.time()
    for i in xrange(howmany):
        f()
    end = time.time()

    elapsed = end - start

    print "%d runs in %.4f seconds (%.2f per/sec)" % (howmany, elapsed,
                                                      howmany / elapsed)

  
def a():
    os.system("git-rev-list --after=2010-10-16 --before=2010-10-17 HEAD &gt; /dev/null")

def b():
    os.system("git-rev-list HEAD &gt; /dev/null")

bench(a, 100)
bench(b, 100)
</t>
</tnodes>
</leo_file>
