
from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.interrupted_sync_test import InterruptedSyncTest


class ukg_pro_ultiproInterruptedSyncTest(InterruptedSyncTest, ukg_pro_ultiproBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a
    stream."""

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_interrupted_sync_test"

    def streams_to_test(self):
        # Exclude large-data-volume streams to avoid excessively slow test runs.
        return self.expected_stream_names().difference(self.LARGE_DATA_STREAMS)


    def manipulate_state(self):
        return {
            "currently_syncing": "prospects",
            "bookmarks": {
                "personnel_dep_deductions": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "personnel_employee_global_localization_elements": { "created" : "2020-01-01T00:00:00Z"},
                "personnel_employee_changes": { "hireDate" : "2020-01-01T00:00:00Z"},
                "personnel_employee_contract_details": { "dateTimeCreated" : "2020-01-01T00:00:00Z"},
                "personnel_employee_extended_elements": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "personnel_employee_global_banks": { "dateModified" : "2020-01-01T00:00:00Z"},
                "personnel_employee_global_banks_employeeglobalbankv2_getv2": { "dateModified" : "2020-01-01T00:00:00Z"},
                "personnel_employee_job_history_details": { "dateTimeCreated" : "2020-01-01T00:00:00Z"},
                "personnel_employee_pay_deduction_elements": { "modifiedDate" : "2020-01-01T00:00:00Z"},
                "personnel_empl_multiple_positions": { "dateTimeCreated" : "2020-01-01T00:00:00Z"},
                "payroll_general_ledger": { "glRunDateTime" : "2020-01-01T00:00:00Z"},
                "configuration_option_rate": { "effectiveDate" : "2020-01-01T00:00:00Z"},
                "configuration_positions": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "configuration_tax_groups": { "dateFinalWagesPaid" : "2020-01-01T00:00:00Z"},
                "payroll_direct_deposit": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "personnel_compensation_details": { "dateLastPaid" : "2020-01-01T00:00:00Z"},
                "personnel_contacts": { "statusAsOfDate" : "2020-01-01T00:00:00Z"},
                "personnel_employment_details": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "personnel_integration_kronos_employee_profiles": { "lastModifiedDate" : "2020-01-01T00:00:00Z"},
                "personnel_open_enrollment_dep_deductions": { "changeDatetime" : "2020-01-01T00:00:00Z"},
                "personnel_person_details": { "datetimeChanged" : "2020-01-01T00:00:00Z"},
                "personnel_open_enrollment_emp_deductions": { "changeDatetime" : "2020-01-01T00:00:00Z"},
                "payroll_paygroup_payperiods": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "payroll_pay_register": { "payDate" : "2020-01-01T00:00:00Z"},
                "payroll_payroll_deductions_history": { "employeeDeductionLastPaid" : "2020-01-01T00:00:00Z"},
                "personnel_position_report": { "dateTimeChanged" : "2020-01-01T00:00:00Z"},
                "services_payroll_payroll_pending_items_earnings": { "roePayDate" : "2020-01-01T00:00:00Z"},
                "personnel_employee_employment_details": { "dateTimeCreated" : "2020-01-01T00:00:00Z"},
        }
    }

