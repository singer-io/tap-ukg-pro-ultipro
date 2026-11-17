from tap_tester.base_suite_tests.pagination_test import PaginationTest
from base import ukg_pro_ultiproBaseTest


class ukg_pro_ultiproPaginationTest(PaginationTest, ukg_pro_ultiproBaseTest):
    """
    Ensure tap can replicate multiple pages of data for streams that use pagination.
    """

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_pagination_test"

    def streams_to_test(self):
        # Include streams with multiple pages and unique primary keys.
        # Excluded streams have duplicate keys, no data, no pagination, or fit on one page.
        return {
            'compensation_details',
            'contacts',
            'dependent_deductions',
            'direct_deposits',
            'employee_cobra_details',
            'employee_demographic_details',
            'employee_extended_elements',
            'employee_security_user_details',
            'employee_user_defined_fields',
            'employment_details',
            'jobs',
            'org_levels',
            'person_details',
            'pto_plans',
            'user_details',
        }
