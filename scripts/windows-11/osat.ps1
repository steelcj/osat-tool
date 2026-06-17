# osat.ps1 — wrapper managed by osat-tool.
# Points to the currently active version. To update, rerun install-osat.py.
# Do not edit the rendered copy at $env:USERPROFILE\bin\osat.ps1 by hand.
& python3 "$env:USERPROFILE\bin\osat-tool\__OSAT_VERSION__\osat.py" @args
