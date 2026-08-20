\# Data Quality Failure Runbook



\## Purpose



This runbook provides investigation and remediation guidance for common data-quality failures detected by DataGuardian.



\---



\## Scenario 1: Negative transaction or order amount



\### Symptoms



\- Data-quality validation fails.

\- `total\_amount` or another monetary column contains a negative value.

\- Great Expectations reports a failure for an expected minimum value.



\### Likely Causes



\- Source-system defect.

\- Incorrect transformation logic.

\- Refunds or reversals represented incorrectly.

\- Sign conversion issue.

\- Corrupted source record.



\### Investigation Steps



1\. Identify the affected record.

2\. Verify the original source value.

3\. Check whether negative values are valid for the business process.

4\. Review recent transformation changes.

5\. Compare the record with historical transactions.

6\. Determine whether the issue affects one record or a larger batch.



\### Recommended Remediation



\- Correct transformation logic if the sign was changed incorrectly.

\- Quarantine invalid records when the source value cannot be trusted.

\- Coordinate with the source-system owner if the bad value originated upstream.

\- Reprocess affected records after the issue is corrected.



\### Safety Notes



Do not automatically replace negative monetary values with zero.



Do not delete failed records without preserving them for investigation.



\---



\## Scenario 2: Null primary or business key



\### Symptoms



\- Required identifier is NULL.

\- Great Expectations reports a not-null validation failure.

\- Records cannot be reliably joined to downstream datasets.



\### Likely Causes



\- Missing source-system identifier.

\- Incorrect column mapping.

\- Parsing or transformation defect.

\- Schema change.



\### Recommended Remediation



\- Validate the source record.

\- Review column mappings.

\- Quarantine records without a reliable identifier.

\- Do not generate replacement identifiers unless the business process explicitly supports it.



\---



\## Scenario 3: Duplicate records



\### Symptoms



\- Unique-key validation fails.

\- Multiple records contain the same expected unique identifier.



\### Likely Causes



\- Source system sent duplicate records.

\- Pipeline replayed the same batch.

\- Retry logic created duplicates.

\- Deduplication logic failed.



\### Recommended Remediation



\- Identify the duplication pattern.

\- Check pipeline retry and replay history.

\- Compare ingestion timestamps.

\- Deduplicate only using a documented business key and deterministic rules.

\- Reprocess the affected partition if necessary.



\---



\## Scenario 4: Invalid status value



\### Symptoms



\- A categorical field contains a value outside the approved set.

\- Great Expectations reports an `ExpectColumnValuesToBeInSet` failure.



\### Likely Causes



\- New source-system status.

\- Typographical error.

\- Schema or business-rule change.

\- Incorrect transformation mapping.



\### Recommended Remediation



\- Confirm whether the new status is valid.

\- Update mapping rules only after the business definition is confirmed.

\- Quarantine unknown values until they are understood.

