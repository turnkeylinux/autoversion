#!/bin/sh

set -e

if [[ $# != 2 ]]; then
    echo syntax: $0 oldname newname
    exit 1
fi

oldname=$1
newname=$2
cat Makefile | \
awk 'BEGIN {p = 1} /^init:/ { p=0 } /^updatelinks:/ { p=1} p { print }' | \
sed "s/make init/make rename/; \
     s/^progname=.*/progname=$newname/" > Makefile.tmp
mv Makefile.tmp Makefile

sed -i -e "s/^progname=.*/progname=$newname/" debian/rules

sed -i -e "s/^Source:.*/Source: $newname/; \
           s/^Package:.*/Package: $newname/; \
           s/^Maintainer:.*/Maintainer: $GIT_AUTHOR_NAME <$GIT_AUTHOR_EMAIL>/" debian/control

[ -f ${oldname}.leo ] && mv ${oldname}.leo ${newname}.leo
$(dirname $0)/updatelinks.sh
