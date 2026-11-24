from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.start_date_test import StartDateTest


class ukg_pro_ultiproStartDateTest(StartDateTest, ukg_pro_ultiproBaseTest):
    """Instantiate start date according to the desired data set and run the
    test."""

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_start_date_test"

    def streams_to_test(self):
        streams_to_exclude = {
            # full table
            'award_type',
            'career_provider',
            'company_details',
            'compensation_details',
            'contacts',
            'direct_deposits',
            'earnings',
            'earnings_history_base_elements',
            'employee_changes',
            'employee_cobra_details',
            'employee_demographic_details',
            'employee_education',
            'employee_global_banks',
            'employee_global_localization_elements',
            'employee_job_history_details',
            'employee_multi_phone_numbers',
            'employee_multi_positions',
            'employee_multiple_jobs',
            'employee_security_user_details',
            'employee_status',
            'employee_supervisor_details',
            'employee_user_defined_fields',
            'general_ledgers',
            'insurance_rates',
            'job_groups',
            'jobs',
            'locations',
            'national_documents',
            'option_rates',
            'org_levels',
            'organization_reporting_category',
            'pay_register',
            'payroll_deductions_history',
            'pto_plans',
            'roles',
            'shift_codes',
            'tax_groups',
            'user_details',
            'user_profile_details',
            # No data available for these incremental streams
            'employee_contract_details',
            'employee_pay_deduction_elements',
            'position_reports',
            'positions',
        }
        return self.expected_stream_names().difference(streams_to_exclude)

    @property
    def start_date_1(self):
        return "2025-01-01T00:00:00Z"

    @property
    def start_date_2(self):
        return "2025-06-01T00:00:00Z"
