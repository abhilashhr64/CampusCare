# ADR 004: Anonymous Teacher Feedback Design & Unlinkability

## Status
Accepted

## Context
Rule **NR-10** mandates: *"Anonymous feedback has no stored link between respondent identity and answers, by design and not by policy."*
Students frequently fear retribution if their critical feedback on lecturers or course delivery can be deanonymized by database administrators, faculty, or system operators. If an answer record includes a foreign key to `user_id`, or if timestamps allow correlation attacks between participation records and answer rows, anonymity is merely policy-based and vulnerable to breach.

## Decision
We implement a **Cryptographically Decoupled Two-Table Architecture**:
1. **Participation Tracking Table (`feedback_participations`)**:
   - Schema: `(college_id, cycle_id, student_id, enrolled_class_id, submitted_at)`
   - Purpose: Prevents double voting, tracks participation percentage per class.
   - Constraint: Contains NO reference, foreign key, or link to the answers submitted.
2. **Responses Table (`feedback_answers`)**:
   - Schema: `(college_id, cycle_id, subject_id, lecturer_id, rating, comment_clean, created_epoch_bucket)`
   - Purpose: Stores the feedback payload for evaluation and analytics.
   - Constraint: Contains ZERO `student_id`, IP address, user agent, or session identifier.
3. **Correlation Mitigation**:
   - Submission endpoint processes participation marking and answer insertion in decoupled operations.
   - Timestamps in `feedback_answers` are truncated to a wide 4-hour epoch bucket or randomized with artificial jitter to prevent millisecond-level correlation with `feedback_participations.submitted_at`.
4. **k-Anonymity Thresholding (Rule AZ-6)**:
   - Lecturers NEVER see raw individual feedback rows.
   - Aggregates and qualitative themes are only visible if the number of distinct student submissions for that course/cycle meets or exceeds $k=5$.

## Consequences
### Positive
- Unlinkability is physically enforced by schema design: even a rogue DBA dumping the database cannot mathematically reconstruct which student provided a given rating or review.
- High student trust and honest feedback rates.

### Negative
- A student cannot modify or retract a previously submitted feedback response once recorded.
