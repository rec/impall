# impall issues and remediation plan

## Issues

1. **Warnings state is restored by popping a global list entry.** `impall()`
   assumes its filter remains at index zero. Nested use or another thread can
   make it remove another caller's filter or leave its own filter behind.
2. **Module restoration changes process-global import state.** Restoring
   `sys.modules` after every import can race with imports in other threads and
   can invalidate modules that an imported module has retained references to.
3. **Pattern-list separation is POSIX-only.** Configuration values use `:`
   rather than `os.pathsep`, which conflicts with drive-letter paths on Windows.
4. **The command-line tool succeeds after failures.** `report()` prints failed
   imports but neither returns a status nor exits nonzero, so CI cannot detect
   failure through its exit code.
5. **Discovery order is filesystem-dependent.** `os.walk()` results are not
   sorted, making report output and first-exception behavior nondeterministic.
6. **Pattern documentation and implementation disagree.** Documentation claims
   module-segment `*` and `**` matching, while the code applies `fnmatch` to
   relative filesystem paths; an unused TODO confirms this is unresolved.
7. **Public typing is incomplete.** Public properties are unannotated and
   helpers accept `Path` at runtime while declaring only `str`.

## Remediation plan

1. Decide the concurrency promise for import isolation, then protect or
   explicitly constrain global warnings and module-state operations with tests
   for nesting and concurrent invocation.
2. Replace fragile warning-filter mutation with scoped restoration that cannot
   remove a caller's filter.
3. Use the platform path separator for new configuration parsing while deciding
   whether legacy colon-separated values need compatibility handling.
4. Decide the CLI failure contract, then return and propagate a nonzero status
   on unexpected failures with command-line regression tests.
5. Sort directory and file discovery and test stable ordering.
6. Either implement documented module-pattern semantics or correct the
   documentation to the supported relative-path pattern behavior.
7. Add precise public annotations and tests for `Path` inputs and configuration
   values.
