Map git commits to auto-versions and vice versa
===============================================

Features
--------

- Calculated versions are Debian compatible.

- Supports named versions (e.g., "1.0") based on signed tags

- Automatically calculates named version numbers for untagged commits
  that follow a tagged commit (e.g., "1.0+1+g873bc99")

- Supports anonymous date based versions (e.g.,
  "0+2015.2.13+09.03.03+38a2eec6") for untagged commits that precede any
  signed tags.
  
Usage
-----

::

    $ autoversion -h
    usage: autoversion [-h] [-r] commit

    Map git commits to auto-versions and vice versa

    positional arguments:

        commit         any revision supported by git (e.g.,commit ids, tags,
                       refs, etc.)

    optional arguments:

        -h, --help     show this help message and exit
        -r, --reverse  map version to git commit

    Example usage:

        autoversion HEAD                    # print latest version
        autoversion -r v1.0                 # print commit of version v1.0
        autoversion $(git-rev-list --all)   # print all versions

Usage example
-------------

::

    ## create repository
    $ mkdir newrepo
    $ cd newrepo
    $ touch hello
    $ git-init .
    Initialized empty Git repository in /tmp/newrepo/.git/
    $ git-add .
    $ git-commit -m "initial commit"
    [master (root-commit) 38a2eec] initial commit
     0 files changed
     create mode 100644 hello

    ## anonymous version

    $ autoversion HEAD
    0+2015.2.13+09.03.03+38a2eec6

    ## name a version by creating a signed tag
    $ git-tag -s v0.1 -m "first version"

    $ autoversion HEAD
    0.1

    ## make a revision

    $ echo revision >> hello
    $ git-commit -v hello -m "a revision"
    [master 873bc99] a revision
     1 file changed, 1 insertion(+)

    $ autoversion HEAD
    0.1+1+g873bc99

    ## "reverse" lookup: get commit id from version
    $ autoversion -r 0.1
    7128df3977bc65de7b115aec7e05472fe508c843

Version format
==============

tagged autoversion := tag based autoversion
-------------------------------------------

The version calculation is based on git-describe (fast)

There are two types of tag based autoversions

1) Tagged commit::

    format: <tag> 

    examples:

        1.0
        1.1
        1.2

2) Commit following a tagged commit::

    format: <tag>-<number-of-revisions>-<shortcommit> 
    
    examples:

        1.0-4-gff3c39c
        1.4+12+gd1b0876
    
untagged autoversion := autoversion
-----------------------------------


Format::

    0+YYYY.MM.DD+HH.MM.SS+<shortcommit>

Example::
        
    0+2015.2.13+09.03.03+38a2eec6

Notes:

* Version may be calculated more slowly.
  
* Untagged autoversion should always be evaluated by Debian package
  management as earlier than a tagged autoversion

