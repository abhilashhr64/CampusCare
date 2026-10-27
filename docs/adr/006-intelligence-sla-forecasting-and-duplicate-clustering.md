# ADR-006: Intelligence, SLA Risk Forecasting, and Multi-Signal Duplicate Clustering

## Status
Accepted

## Context
In campus operations, college complaints queues frequently experience duplicate submissions for single physical infrastructure events (e.g. power failure in a lab block, network outages, library chiller leaks). When dozens of students submit similar grievances, staff queues become overwhelmed. Furthermore, complaint SLA deadlines often breach silently without advance hazard warning, and student attendance deficits are typically communicated punitively after semester thresholds have already failed.

Under rules `B1`, `B3`, `NR-10`, and `EV-3`:
1. Duplicate detection must identify co-located and textually overlapping complaints without cross-tenant data leakage.
2. SLA risk assessment must compute real-time breach probabilities so department staff can intervene before deadlines expire.
3. Attendance deficit alerts must be supportive, deterministic, and provide actionable recovery projections without AI hallucinations.
4. Qualitative feedback theme extraction must strictly maintain $k \ge 5$ anonymity, masking individual submissions.

## Decision
1. **Multi-Signal Duplicate Detection:**
   - Evaluates complaints within the same tenant.
   - Computes title and description token similarity combined with physical location matching (`location_tag`, e.g., QR tags).
   - Generates duplicate clusters referencing a canonical complaint (`fk_complaint_dup_canonical`) and duplicate complaint (`fk_complaint_dup_duplicate`).
   - Forced PostgreSQL RLS ensures tenant complaints can never cluster with or observe complaints from another tenant (`TN-1`, `TN-6`).

2. **Continuous SLA Risk Forecasting:**
   - Categorizes risk based on hours remaining until committed SLA expiration:
     - $\le 6$ hours: `CRITICAL` (projected breach probability 0.92)
     - $6 < h \le 18$ hours: `HIGH` (projected breach probability 0.68)
     - $18 < h \le 30$ hours: `MEDIUM` (projected breach probability 0.35)
     - $> 30$ hours: `LOW` (projected breach probability 0.10)
   - Evaluates complaints strictly under tenant RLS without mutating complaint state without human staff action (`B4`).

3. **Supportive Attendance Deficit Interventions:**
   - Proactively evaluates student attendance against institutional threshold ($T = 0.75$).
   - Calculates deterministic recovery requirement:
     $$C_{attend} = \left\lceil \frac{T \cdot C_{conducted} - C_{attended}}{1 - T} \right\rceil$$
   - Emits supportive notification via transactional outbox (`publish_event`) delivering clear, non-punitive guidance: "Attend next $X$ consecutive classes to return to 75% safe standing."

4. **K-Anonymity Guarded Feedback Thematic Extraction:**
   - Before extracting qualitative themes, verifies that total answer responses for the cycle and lecturer satisfy $count \ge k$ ($k = 5$).
   - Below $k$, extraction raises a hard barrier, refusing to reveal themes or excerpts.
   - Above $k$, aggregates qualitative feedback into high-level categories (`LAB_AND_PRACTICALS`, `EXPLANATION_PACING`, etc.) and masks individual phrases.

## Consequences
- **Positive:** Reduces administrative duplicate triage workload; gives departments predictive visibility before SLA breaches; empowers students with deterministic attendance recovery paths; preserves $k$-anonymity guarantees.
- **Negative:** Requires background workers for continuous periodic scanning (`EV-3`); requires composite foreign keys and tenant isolation enforcement on new analytics tables.
