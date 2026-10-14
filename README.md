# tap-ukg-pro-ultipro

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md).

This tap:

- Pulls raw data from the [UKG PRO HCM API].
- Extracts the following resources:
    - [company_details](https://developer.ukg.com/hcm/reference/companydetails_getcompanydetails)
    - [earnings](https://developer.ukg.com/hcm/reference/get_configuration-v1-earnings)
    - [insurance_rates](https://developer.ukg.com/hcm/reference/insrate_getinsrate)
    - [job_groups](https://developer.ukg.com/hcm/reference/jobgroup_get)
    - [jobs](https://developer.ukg.com/hcm/reference/getjobslist)
    - [locations](https://developer.ukg.com/hcm/reference/getlocationslist)
    - [option_rates](https://developer.ukg.com/hcm/reference/get_configuration-v1-option-rate)
    - [organization_reporting_category](https://developer.ukg.com/hcm/reference/get_configuration-v1-organization-reporting-category)
    - [position_reports](https://developer.ukg.com/hcm/reference/positionreport_get)
    - [positions](https://developer.ukg.com/hcm/reference/get_configuration-v1-positions)
    - [shift_codes](https://developer.ukg.com/hcm/reference/get_configuration-v1-shift-codes)
    - [tax_groups](https://developer.ukg.com/hcm/reference/get_configuration-v1-tax-groups)
    - [user_profile_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-user-profile-details)
    - [org_levels](https://developer.ukg.com/hcm/reference/getorg-levelslist)
    - [award_type](https://developer.ukg.com/hcm/reference/getawardtypelist)
    - [career_provider](https://developer.ukg.com/hcm/reference/getcareerproviderlist)
    - [earnings_history_base_elements](https://developer.ukg.com/hcm/reference/earningshistory_getinsrate)
    - [direct_deposits](https://developer.ukg.com/hcm/reference/get_payroll-v1-direct-deposit)
    - [general_ledgers](https://developer.ukg.com/hcm/reference/generalledgerrundetailsv2_get)
    - [pay_register](https://developer.ukg.com/hcm/reference/payregister_get)
    - [pay_group_payperiods](https://developer.ukg.com/hcm/reference/paygrouppayperiod_getpaygrouppayperiod)
    - [payroll_deductions_history](https://developer.ukg.com/hcm/reference/payrolldeductionshistory_get)
    - [compensation_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-compensation-details)
    - [employee_changes](https://developer.ukg.com/hcm/reference/employeechanges_get_all)
    - [employee_cobra_details](https://developer.ukg.com/hcm/reference/employeecobradetails_get)
    - [contacts](https://developer.ukg.com/hcm/reference/get_personnel-v1-contacts)
    - [employee_contract_details](https://developer.ukg.com/hcm/reference/employeecontract_get)
    - [employee_demographic_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-employee-demographic-details)
    - [employee_education](https://developer.ukg.com/hcm/reference/employeeeducation_get)
    - [employee_extended_elements](https://developer.ukg.com/hcm/reference/employeeextendedelements_get)
    - [employee_job_history_details](https://developer.ukg.com/hcm/reference/employeejobhistorydetail_get)
    - [employee_multiple_jobs](https://developer.ukg.com/hcm/reference/get_personnel-v1-empl-multiple-jobs)
    - [employee_multi_phone_numbers](https://developer.ukg.com/hcm/reference/employeemultiphonenumbers_get)
    - [employee_multi_positions](https://developer.ukg.com/hcm/reference/empmultiplepositions_get)
    - [national_documents](https://developer.ukg.com/hcm/reference/nationaldocument_get)
    - [employee_supervisor_details](https://developer.ukg.com/hcm/reference/employeesupervisordetails_get)
    - [employee_status](https://developer.ukg.com/hcm/reference/kronosemployeestatus_get)
    - [employment_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-employment-details)
    - [employee_global_banks](https://developer.ukg.com/hcm/reference/employeeglobalbank_get)
    - [employee_global_localization_elements](https://developer.ukg.com/hcm/reference/empgloballocalizationelement_get)
    - [employee_pay_deduction_elements](https://developer.ukg.com/hcm/reference/employeepaydeductionelement_get)
    - [international_employees](https://developer.ukg.com/hcm/reference/internationalemployee_get)
    - [open_enrollment_employee_deductions](https://developer.ukg.com/hcm/reference/openenrollmentemployeedeductions_getauditdetails)
    - [employee_deductions](https://developer.ukg.com/hcm/reference/get_personnel-v1-emp-deductions)
    - [dependent_deductions](https://developer.ukg.com/hcm/reference/dependentdeductions_get)
    - [person_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-person-details)
    - [pto_plans](https://developer.ukg.com/hcm/reference/get_personnel-v1-pto-plans)
    - [employee_user_defined_fields](https://developer.ukg.com/hcm/reference/get_personnel-v1-user-defined-fields)
    - [employee_security_user_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-employee-security-user-details)
    - [roles](https://developer.ukg.com/hcm/reference/get_configuration-v1-roles)
    - [user_details](https://developer.ukg.com/hcm/reference/userdetails_getuserdetails)

- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Streams

**[company_details](https://developer.ukg.com/hcm/reference/companydetails_getcompanydetails)**
- Primary keys: ['companyID']
- Replication strategy: FULL_TABLE

**[earnings](https://developer.ukg.com/hcm/reference/get_configuration-v1-earnings)**
- Primary keys: ['earningCode']
- Replication strategy: FULL_TABLE

**[insurance_rates](https://developer.ukg.com/hcm/reference/insrate_getinsrate)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[job_groups](https://developer.ukg.com/hcm/reference/jobgroup_get)**
- Primary keys: ['jobGroupCode']
- Replication strategy: FULL_TABLE

**[jobs](https://developer.ukg.com/hcm/reference/getjobslist)**
- Primary keys: ['jobCode']
- Replication strategy: FULL_TABLE

**[locations](https://developer.ukg.com/hcm/reference/getlocationslist)**
- Primary keys: ['locationCode']
- Replication strategy: FULL_TABLE

**[option_rates](https://developer.ukg.com/hcm/reference/get_configuration-v1-option-rate)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[organization_reporting_category](https://developer.ukg.com/hcm/reference/get_configuration-v1-organization-reporting-category)**
- Primary keys: ['code']
- Replication strategy: FULL_TABLE

**[position_reports](https://developer.ukg.com/hcm/reference/positionreport_get)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[positions](https://developer.ukg.com/hcm/reference/get_configuration-v1-positions)**
- Primary keys: ['integrationRecordId']
- Replication strategy: INCREMENTAL

**[shift_codes](https://developer.ukg.com/hcm/reference/get_configuration-v1-shift-codes)**
- Primary keys: ['shiftCode']
- Replication strategy: FULL_TABLE

**[tax_groups](https://developer.ukg.com/hcm/reference/get_configuration-v1-tax-groups)**
- Primary keys: ['taxCalcGroupIdCode']
- Replication strategy: FULL_TABLE

**[user_profile_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-user-profile-details)**
- Primary keys: ['userId']
- Replication strategy: FULL_TABLE

**[org_levels](https://developer.ukg.com/hcm/reference/getorg-levelslist)**
- Primary keys: ['code', 'level']
- Replication strategy: FULL_TABLE

**[award_type](https://developer.ukg.com/hcm/reference/getawardtypelist)**
- Primary keys: ['code']
- Replication strategy: FULL_TABLE

**[career_provider](https://developer.ukg.com/hcm/reference/getcareerproviderlist)**
- Primary keys: ['code']
- Replication strategy: FULL_TABLE

**[earnings_history_base_elements](https://developer.ukg.com/hcm/reference/earningshistory_getinsrate)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[direct_deposits](https://developer.ukg.com/hcm/reference/get_payroll-v1-direct-deposit)**
- Primary keys: ['accountRecordId']
- Replication strategy: FULL_TABLE

**[general_ledgers](https://developer.ukg.com/hcm/reference/generalledgerrundetailsv2_get)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[pay_register](https://developer.ukg.com/hcm/reference/payregister_get)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[pay_group_payperiods](https://developer.ukg.com/hcm/reference/paygrouppayperiod_getpaygrouppayperiod)**
- Primary keys: []
- Replication strategy: INCREMENTAL

**[payroll_deductions_history](https://developer.ukg.com/hcm/reference/payrolldeductionshistory_get)**
- Primary keys: ['recordId']
- Replication strategy: FULL_TABLE

**[compensation_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-compensation-details)**
- Primary keys: ['companyID', 'employeeID']
- Replication strategy: FULL_TABLE

**[employee_changes](https://developer.ukg.com/hcm/reference/employeechanges_get_all)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[employee_cobra_details](https://developer.ukg.com/hcm/reference/employeecobradetails_get)**
- Primary keys: ['personID']
- Replication strategy: FULL_TABLE

**[contacts](https://developer.ukg.com/hcm/reference/get_personnel-v1-contacts)**
- Primary keys: ['contactId']
- Replication strategy: FULL_TABLE

**[employee_contract_details](https://developer.ukg.com/hcm/reference/employeecontract_get)**
- Primary keys: ['employeeId', 'contractNumber']
- Replication strategy: INCREMENTAL

**[employee_demographic_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-employee-demographic-details)**
- Primary keys: ['employeeId']
- Replication strategy: FULL_TABLE

**[employee_education](https://developer.ukg.com/hcm/reference/employeeeducation_get)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[employee_extended_elements](https://developer.ukg.com/hcm/reference/employeeextendedelements_get)**
- Primary keys: ['personID']
- Replication strategy: INCREMENTAL

**[employee_job_history_details](https://developer.ukg.com/hcm/reference/employeejobhistorydetail_get)**
- Primary keys: ['employeeId', 'jobEffectiveDate']
- Replication strategy: INCREMENTAL

**[employee_multiple_jobs](https://developer.ukg.com/hcm/reference/get_personnel-v1-empl-multiple-jobs)**
- Primary keys: ['employeeId', 'jobCode']
- Replication strategy: FULL_TABLE

**[employee_multi_phone_numbers](https://developer.ukg.com/hcm/reference/employeemultiphonenumbers_get)**
- Primary keys: ['employeeId', 'auditKey']
- Replication strategy: FULL_TABLE

**[employee_multi_positions](https://developer.ukg.com/hcm/reference/empmultiplepositions_get)**
- Primary keys: []
- Replication strategy: INCREMENTAL

**[national_documents](https://developer.ukg.com/hcm/reference/nationaldocument_get)**
- Data Key = data
- Primary keys: ['employeeId', 'nationalDocumentId']
- Replication strategy: FULL_TABLE

**[employee_supervisor_details](https://developer.ukg.com/hcm/reference/employeesupervisordetails_get)**
- Primary keys: ['employeeID']
- Replication strategy: FULL_TABLE

**[employee_status](https://developer.ukg.com/hcm/reference/kronosemployeestatus_get)**
- Data Key = body
- Primary keys: []
- Replication strategy: FULL_TABLE

**[employment_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-employment-details)**
- Primary keys: ['companyID', 'employeeID']
- Replication strategy: INCREMENTAL

**[employee_global_banks](https://developer.ukg.com/hcm/reference/employeeglobalbank_get)**
- Data Key = data
- Primary keys: ['bankId', 'employeeId']
- Replication strategy: FULL_TABLE

**[employee_global_localization_elements](https://developer.ukg.com/hcm/reference/empgloballocalizationelement_get)**
- Data Key = data
- Primary keys: ['employeeId', 'fieldId']
- Replication strategy: INCREMENTAL

**[employee_pay_deduction_elements](https://developer.ukg.com/hcm/reference/employeepaydeductionelement_get)**
- Data Key = data
- Primary keys: ['employeeId', 'payDeductionId']
- Replication strategy: INCREMENTAL

**[international_employees](https://developer.ukg.com/hcm/reference/internationalemployee_get)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[open_enrollment_employee_deductions](https://developer.ukg.com/hcm/reference/openenrollmentemployeedeductions_getauditdetails)**
- Primary keys: ['employeeId', 'deductionCode']
- Replication strategy: INCREMENTAL

**[employee_deductions](https://developer.ukg.com/hcm/reference/get_personnel-v1-emp-deductions)**
- Primary keys: ['employeeId', 'dedCode']
- Replication strategy: FULL_TABLE

**[dependent_deductions](https://developer.ukg.com/hcm/reference/dependentdeductions_get)**
- Primary keys: []
- Replication strategy: INCREMENTAL

**[person_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-person-details)**
- Primary keys: ['employeeId']
- Replication strategy: INCREMENTAL

**[pto_plans](https://developer.ukg.com/hcm/reference/get_personnel-v1-pto-plans)**
- Primary keys: ['employeeId', 'companyId', 'ptoPlan']
- Replication strategy: FULL_TABLE

**[employee_user_defined_fields](https://developer.ukg.com/hcm/reference/get_personnel-v1-user-defined-fields)**
- Primary keys: ['employeeId']
- Replication strategy: FULL_TABLE

**[employee_security_user_details](https://developer.ukg.com/hcm/reference/get_personnel-v1-employee-security-user-details)**
- Primary keys: []
- Replication strategy: FULL_TABLE

**[roles](https://developer.ukg.com/hcm/reference/get_configuration-v1-roles)**
- Primary keys: ['rolID']
- Replication strategy: FULL_TABLE

**[user_details](https://developer.ukg.com/hcm/reference/userdetails_getuserdetails)**
- Primary keys: ['userId']
- Replication strategy: FULL_TABLE


## Authentication

The tap uses HTTP Basic authentication together with the UKG Pro customer API key.

| Config key | Description |
|---|---|
| `username` | Web service account user name |
| `password` | Web service account password |
| `api_key` | User API key of the web service account, sent as the `US-Customer-Api-Key` header |
| `hostname` | Host of your UKG Pro tenant, for example `service.example.com` (an `https://` prefix is accepted; `http://` is rejected) |
| `start_date` | Default start date (RFC 3339) for incremental streams |


## Quick Start

1. Install

    Clone this repository, and then install using setup.py. We recommend using a virtualenv:

    ```bash
    > virtualenv -p python3 venv
    > source venv/bin/activate
    > python setup.py install
    OR
    > cd .../tap-ukg-pro-ultipro
    > pip install -e .
    ```
2. Dependent libraries. The following dependent libraries were installed.
    ```bash
    > pip install singer-python
    > pip install target-stitch
    > pip install target-json

    ```
    - [singer-tools](https://github.com/singer-io/singer-tools)
    - [target-stitch](https://github.com/singer-io/target-stitch)

3. Create your tap's `config.json` file.  The tap config file for this tap should include these entries:
   - `username`, `password` (string, required) - web service account credentials
   - `api_key` (string, required) - user API key of the web service account (sent as `US-Customer-Api-Key`)
   - `hostname` (string, required) - UKG Pro tenant host (for example `service.example.com`)
   - `start_date` (string, required) - the default value to use if no bookmark exists for an endpoint (rfc3339 date string)
   - `user_agent` (string, optional): Process and email for API logging purposes. Example: `tap-ukg_pro_ultipro <api_user_email@your_company.com>`
   - `request_timeout` (integer, optional): Max time in seconds for request to wait for response. Default: `300`

    ```json
    {
        "username": "<USERNAME>",
        "password": "<PASSWORD>",
        "api_key": "<USER_API_KEY>",
        "hostname": "<TENANT_HOSTNAME>",
        "start_date": "2019-01-01T00:00:00Z",
        "user_agent": "tap-ukg_pro_ultipro <api_user_email@your_company.com>",
        "request_timeout": 300
    }

    ```
    Optionally, also create a `state.json` file. `currently_syncing` is an optional attribute used for identifying the last object to be synced in case the job is interrupted mid-stream. The next run would begin where the last job left off.

    ```json
    {
        "currently_syncing": "dummy_stream1",
        "bookmarks": {
            "dummy_stream1": "2019-09-27T22:34:39.000000Z",
            "dummy_stream2": "2019-09-28T15:30:26.000000Z",
            "dummy_stream3": "2019-09-28T18:23:53Z"
        }
    }
    ```

4. Run the Tap in Discovery Mode
    This creates a catalog.json for selecting objects/fields to integrate:
    ```bash
    tap-ukg-pro-ultipro --config config.json --discover > catalog.json
    ```
   See the Singer docs on discovery mode
   [here](https://github.com/singer-io/getting-started/blob/master/docs/DISCOVERY_MODE.md#discovery-mode).

5. Run the Tap in Sync Mode (with catalog) and [write out to state file](https://github.com/singer-io/getting-started/blob/master/docs/RUNNING_AND_DEVELOPING.md#running-a-singer-tap-with-a-singer-target)

    For Sync mode:
    ```bash
    > tap-ukg-pro-ultipro --config tap_config.json --catalog catalog.json > state.json
    > tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
    ```
    To load to json files to verify outputs:
    ```bash
    > tap-ukg-pro-ultipro --config tap_config.json --catalog catalog.json | target-json > state.json
    > tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
    ```
    To pseudo-load to [Stitch Import API](https://github.com/singer-io/target-stitch) with dry run:
    ```bash
    > tap-ukg-pro-ultipro --config tap_config.json --catalog catalog.json | target-stitch --config target_config.json --dry-run > state.json
    > tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
    ```

6. Test the Tap
    While developing the UKG Pro tap, the following utilities were run in accordance with Singer.io best practices:
    Pylint to improve [code quality](https://github.com/singer-io/getting-started/blob/master/docs/BEST_PRACTICES.md#code-quality):
    ```bash
    > pylint tap_ukg_pro_ultipro -d missing-docstring -d logging-format-interpolation -d too-many-locals -d too-many-arguments
    ```
    Pylint test resulted in the following score:
    ```bash
    Your code has been rated at 9.67/10
    ```

    To [check the tap](https://github.com/singer-io/singer-tools#singer-check-tap) and verify working:
    ```bash
    > tap_ukg_pro_ultipro --config tap_config.json --catalog catalog.json | singer-check-tap > state.json
    > tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
    ```

    #### Unit Tests

    Unit tests may be run with the following.

    ```
    python -m pytest --verbose
    ```

    Note, you may need to install test dependencies.

    ```
    pip install -e .'[dev]'
    ```
---

Copyright &copy; 2019 Stitch
