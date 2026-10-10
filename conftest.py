# Programs under tools/manual/ contact real projectors and USB hardware. They are
# named check_*.py so no collector picks them up, and this ignore keeps that true
# even if someone later adds a test_*.py there by habit.
#
# archive/ holds unsupported legacy implementations. deployment/ is a linked git
# worktree that may or may not be checked out here; neither is this branch's
# source, and both contain modules that exit or touch hardware on import.
collect_ignore_glob = ["tools/manual/*", "archive/*", "deployment/*"]
