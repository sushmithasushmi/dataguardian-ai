**# Source Extraction Failure Runbook**



**## Purpose**



**This runbook provides troubleshooting guidance for failures that occur while extracting data from source systems.**



**---**



**## Scenario 1: PostgreSQL table does not exist**



**### Symptoms**



**- Pipeline fails during source extraction.**

**- PostgreSQL returns an `UndefinedTable` error.**

**- Error message contains:**

&#x20; **`relation "<table\_name>" does not exist`**

**- A `TABLE\_START` event may exist without a corresponding `TABLE\_EXTRACTED` event.**



**### Likely Causes**



**- Incorrect table name in pipeline configuration.**

**- Source table was renamed.**

**- Source table was removed.**

**- Incorrect database schema is being queried.**

**- Case-sensitive or quoted identifier mismatch.**



**### Investigation Steps**



**1. Identify the table mentioned in the PostgreSQL error.**

**2. Verify that the table exists in the source database.**

**3. Confirm the expected schema.**

**4. Compare the configured table name with the actual database table.**

**5. Check recent schema or deployment changes.**



**### Recommended Remediation**



**- Correct the table name if it is misspelled.**

**- Update the configured schema if the table exists under a different schema.**

**- Remove the table from the ingestion configuration if it is no longer required.**

**- Restore or recreate the table only if the source owner confirms that it should exist.**

**- Rerun the pipeline after validating the configuration.**



**### Safety Notes**



**Do not automatically create missing source tables.**



**Do not modify production schemas without confirmation from the source-system owner.**



**---**



**## Scenario 2: Source database connection failure**



**### Symptoms**



**- Connection timeout.**

**- Authentication failure.**

**- Connection refused.**

**- DNS or hostname resolution error.**



**### Likely Causes**



**- Database unavailable.**

**- Invalid credentials.**

**- Network issue.**

**- Incorrect hostname or port.**

**- Firewall or security-group restriction.**



**### Recommended Remediation**



**- Verify database availability.**

**- Validate connection configuration.**

**- Check credentials securely.**

**- Confirm network connectivity.**

**- Retry only after confirming that the source system is reachable.**



**---**



**## Scenario 3: Permission denied**



**### Symptoms**



**- PostgreSQL returns permission-related errors.**

**- Connection succeeds but SELECT fails.**



**### Likely Causes**



**- Service account lost access.**

**- Table permissions changed.**

**- Schema permissions changed.**



**### Recommended Remediation**



**- Verify the pipeline service account permissions.**

**- Request the minimum required SELECT permission.**

**- Do not grant broader permissions than necessary.**

