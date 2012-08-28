#!/bin/bash

set -e

tmp=$(mktemp -d)

trap cleanup EXIT
cleanup() {
    set +e
    [ -z "$tmp" -o ! -d "$tmp" ] || rm -rf "$tmp"
}

unset CDPATH
pwd=$(pwd)
svn=$(date +%Y%m%d)
dirname=cp2k-2.3
url=https://cp2k.svn.sourceforge.net/svnroot/cp2k/trunk/cp2k
rev={$svn}

cd "$tmp"
svn checkout -r ${rev} ${url} $dirname
cd $dirname
tools/get_revision_number . >src/REVISION
find . -type d -name .svn -print0 | xargs -0r rm -rf
cd ..
tar jcf "$pwd"/$dirname-$svn.tar.bz2 $dirname
cd - >/dev/null
