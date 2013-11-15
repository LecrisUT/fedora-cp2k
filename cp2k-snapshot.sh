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
svn=20131112
dirname=cp2k-2.5
url=svn://svn.code.sf.net/p/cp2k/code/trunk/cp2k
rev=13316

cd "$tmp"
svn checkout -r ${rev} ${url} $dirname
cd $dirname
tools/get_revision_number . >REVISION
find . -type d -name .svn -print0 | xargs -0r rm -rf
cd ..
tar Jcf "$pwd"/$dirname-$svn.tar.xz $dirname
cd - >/dev/null
