# Errata

Record corrections to published material here, newest first. Include the date, page and section, prior claim, corrected claim, and supporting source or reproducible check.

## 2026-11-17 · Block 01, runtime model and Figure 2

The previous model equated dispatch with the operation applied by the environment, and Figure 2 labeled submission as execution. Dispatch is an attempt. The scheduler can accept a request even if the acknowledgement is lost, and a dispatched request may never reach the scheduler. The controller records its evidence separately from the operation the scheduler actually applied. In [the revised figure](https://hieutrungle.github.io/agentic-systems-notes/curriculum/01-agent-fundamentals.html#fig-agent-runtime), step through dispatch, scheduler acceptance, and job completion to inspect the three events.
