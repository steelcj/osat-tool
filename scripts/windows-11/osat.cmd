@echo off
REM osat.cmd — wrapper managed by osat-tool.
REM Points to the currently active version. To update, rerun install-osat.py.
REM Do not edit the rendered copy at %USERPROFILE%\bin\osat.cmd by hand.
python3 "%USERPROFILE%\bin\osat-tool\__OSAT_VERSION__\osat.py" %*
