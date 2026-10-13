"""Test tap discovery mode and metadata."""
from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest
from tap_tester import menagerie


class ukg_pro_ultiproDiscoveryTest(DiscoveryTest, ukg_pro_ultiproBaseTest):
    """Test tap discovery mode and metadata conforms to standards."""
    orphan_streams = {
        configuration_company_details,
        personnel_dep_deductions,
        payroll_earnings_history_base_elements,
        personnel_emp_deductions_benefit_option_change_date,
        personnel_employee_global_localization_elements,
        personnel_employee_changes,
        personnel_employee_cobra_details,
        personnel_employee_contract_details,
        personnel_employee_education,
        personnel_employee_extended_elements,
        personnel_employee_global_banks,
        personnel_employee_global_banks_employeeglobalbankv2_getv2,
        personnel_employee_job_history_details,
        personnel_employee_multi_phone_numbers,
        personnel_employee_pay_deduction_elements,
        personnel_employee_supervisor_details,
        personnel_empl_multiple_positions,
        payroll_general_ledger,
        configuration_code_tables,
        configuration_earnings,
        configuration_option_rate,
        configuration_organization_reporting_category,
        configuration_positions,
        configuration_shift_codes,
        configuration_tax_groups,
        payroll_direct_deposit,
        personnel_compensation_details,
        personnel_contacts,
        personnel_deduction_history_effective_change_dates,
        personnel_emp_deductions,
        personnel_empl_multiple_jobs,
        personnel_employee_demographic_details,
        personnel_employment_details,
        personnel_integration_kronos_business_structure_status,
        personnel_integration_kronos_employee_profiles,
        personnel_open_enrollment_dep_deductions,
        personnel_person_details,
        personnel_pto_plans,
        personnel_user_defined_fields,
        personnel_user_preferences,
        personnel_user_profile_details,
        configuration_code_tables_allergy,
        configuration_code_tables_awardtype,
        configuration_code_tables_careerprovider,
        configuration_code_tables_childsupporttype,
        configuration_code_tables_cobrastatus,
        configuration_code_tables_companyproperty,
        configuration_code_tables_coursecategory,
        configuration_code_tables_coursedeliverymet,
        configuration_code_tables_coursesubcategory,
        configuration_code_tables_disability,
        configuration_code_tables_employeetype,
        configuration_code_tables_jobfamily,
        configuration_jobs,
        configuration_jobs_getjobslist_v1,
        configuration_code_tables_licensetype,
        configuration_code_tables_loantype,
        configuration_locations,
        configuration_code_tables_maritalstatus,
        configuration_code_tables_militarybranches,
        configuration_code_tables_militaryera,
        configuration_code_tables_nameprefix,
        configuration_org_levels,
        configuration_code_tables_otherphonetypes,
        configuration_code_tables_project,
        configuration_code_tables_school,
        configuration_code_tables_skillproficiencylevel,
        configuration_code_tables_skills,
        configuration_code_tables_termtype,
        configuration_code_tables_waivereason,
        configuration_insurance_rate,
        personnel_international_employees,
        configuration_jobgroup,
        personnel_integration_kronos_employee_status,
        personnel_national_documents,
        personnel_open_enrollment_emp_deductions,
        payroll_paygroup_payperiods,
        payroll_pay_register,
        payroll_payroll_deductions_history,
        personnel_position_report,
        services_payroll_payroll_pending_items_deductions,
        services_payroll_payroll_pending_items_earnings,
        personnel_employee_employment_details,
    }

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_discovery_test"

    def streams_to_test(self):
        return self.expected_stream_names()

    def test_parent_stream(self):
        """
        Test that each stream's metadata correctly includes the expected parent tap stream ID.

        For each stream in `streams_to_test`, this test:
        - Retrieves the expected parent tap stream ID from test expectations.
        - Retrieves the actual metadata from the found catalog.
        - Verifies that the metadata contains the `PARENT_TAP_STREAM_ID` key (except for the orphans stream).
        - Confirms that the actual parent tap stream ID matches the expected value.
        """
        for stream in self.streams_to_test():
            with self.subTest(stream=stream):

                expected_parent_tap_stream_id = self.expected_parent_tap_stream(stream)


                catalog = [catalog for catalog in self.found_catalogs
                           if catalog["stream_name"] == stream][0]
                metadata = menagerie.get_annotated_schema(
                    self.conn_id, catalog['stream_id'])["metadata"]
                stream_properties = [item for item in metadata if item.get("breadcrumb") == []]
                actual_parent_tap_stream_id = \
                    stream_properties[0].get("metadata", {}).get(self.PARENT_TAP_STREAM_ID, None)


                self.assertIn("metadata", stream_properties[0])
                stream_metadata = stream_properties[0]["metadata"]


                if stream not in self.orphan_streams:
                    self.assertIn(self.PARENT_TAP_STREAM_ID, stream_metadata)
                    self.assertTrue(isinstance(actual_parent_tap_stream_id, str))


                with self.subTest(msg="validating parent tap stream id"):
                    self.assertEqual(expected_parent_tap_stream_id, actual_parent_tap_stream_id,
                                        logging=f"verify {expected_parent_tap_stream_id} "
                                                f"is saved in metadata as a parent-tap-stream-id")

