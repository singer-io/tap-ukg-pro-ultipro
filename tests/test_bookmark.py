from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.bookmark_test import BookmarkTest


class ukg_pro_ultiproBookMarkTest(BookmarkTest, ukg_pro_ultiproBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a
    stream."""
    bookmark_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    initial_bookmarks = {
        "bookmarks": {
            "dependent_deductions": {"dateTimeChanged": "2025-11-26T00:00:00Z"},
            "employee_extended_elements": {"dateTimeChanged": "2025-04-02T10:44:00Z"},
            "employment_details": {"dateTimeChanged": "2025-08-19T00:00:00Z"},
            "person_details": {"datetimeChanged": "2025-04-02T10:44:00Z"},
        }
    }

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_bookmark_test"

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

    def calculate_new_bookmarks(self):
        """Calculates new bookmarks by looking through sync 1 data to determine
        a bookmark that will sync 2 records in sync 2"""
        new_bookmarks = {
            "dependent_deductions": {"dateTimeChanged": "2025-12-02T08:57:00.577000Z"},
            "employee_extended_elements": {"dateTimeChanged": "2025-12-01T15:09:11.113000Z"},
            "employment_details": {"dateTimeChanged": "2025-12-01T19:08:03.080000Z"},
            "pay_group_payperiods": {"dateTimeChanged": "2025-03-03T12:05:11.710000Z"},
            "person_details": {"datetimeChanged": "2025-12-01T15:09:11.113000Z"},
        }

        return new_bookmarks
