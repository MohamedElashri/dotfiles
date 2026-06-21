#!/usr/bin/env bash
# Shared platform-detection helper.  Source this file; do not execute it directly.
#
# Usage:  source "$(dirname "${BASH_SOURCE[0]}")/lib/platform.sh"
#         platform="$(detect_platform)"
#
# Outputs one of: linux | mac | hep
#
# Detection logic (first match wins):
#   mac  — uname returns Darwin
#   hep  — AFS or CVMFS mount found, OR hostname matches a known HEP pattern
#           (lxplus*, sneezy, sleepy, goofy, *.cern.ch, *.uc.edu, *.geop.*)
#   linux — everything else

detect_platform() {
    local os; os="$(uname -s)"
    if [[ "$os" == "Darwin" ]]; then
        echo mac
        return
    fi
    local host; host="$(hostname 2>/dev/null || true)"
    if [[ -d /afs/cern.ch ]] || [[ -d /cvmfs/lhcb.cern.ch ]] || \
       grep -qiE "(lxplus|sneezy|sleepy|goofy|cern\.ch|\.uc\.edu|geop\.)" <<< "$host"; then
        echo hep
        return
    fi
    echo linux
}
