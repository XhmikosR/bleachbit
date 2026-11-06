#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

# For CI, build the RPM and SRPM with only the spec's BuildRequires
# installed. rpmbuild runs as a regular user, as on OBS.

set -euo pipefail

distro="$1"
spec=bleachbit.spec

case "$distro" in
    fedora)
        # fedora_version comes from OBS, Fedora only sets %fedora
        defines=(--define "fedora_version $(rpm -E %fedora)")
        dnf -y install --setopt=install_weak_deps=False \
            'dnf5-command(builddep)' rpm-build shadow-utils util-linux
        dnf -y builddep --setopt=install_weak_deps=False "${defines[@]}" --spec "$spec"
        ;;
    opensuse)
        defines=(--define "is_opensuse 1" --define "suse_version 1699")
        # The BuildRequires use %{modern_python}, so get its macros first
        # busybox-gawk conflicts with the gawk rpm-build needs
        zypper --non-interactive install --no-recommends \
            python-rpm-macros rpm-build shadow util-linux -busybox-gawk
        mapfile -t deps < <(rpmspec -q --buildrequires "${defines[@]}" "$spec")
        zypper --non-interactive install --no-recommends "${deps[@]}"
        ;;
    *)
        echo "ERROR: unsupported distro '$distro'" >&2
        exit 1
        ;;
esac

useradd --create-home builder
topdir=/home/builder/rpmbuild
runuser -u builder -- mkdir -p "$topdir"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

"$(rpm -E '%{__python3}')" setup.py sdist --dist-dir "$topdir/SOURCES"
# Put the CI build number and git revision in the release
rev=$(sed -n 's/^revision = "\(.*\)"$/\1/p' bleachbit/Revision.py)
build=$(sed -n 's/^build_number = "\(.*\)"$/\1/p' bleachbit/Revision.py)
grep -q '^Release: *1%{?dist}$' "$spec"
sed "s/^\(Release: *\)1%{?dist}$/\11.${build:?}.git${rev:?}%{?dist}/" \
    "$spec" > "$topdir/SPECS/$spec"

runuser -u builder -- env HOME=/home/builder \
    rpmbuild -ba --define "_topdir $topdir" "${defines[@]}" "$topdir/SPECS/$spec"

mkdir -p rpms
cp "$topdir"/RPMS/*/*.rpm "$topdir"/SRPMS/*.rpm rpms/
