import copy
import os
import unittest
from datetime import datetime as dt
from datetime import timedelta

import dateutil.parser
import pytz
from tap_tester import connections, menagerie, runner
from tap_tester.logger import LOGGER
from tap_tester.base_suite_tests.base_case import BaseCase


class ukg_pro_ultiproBaseTest(BaseCase):
    """Setup expectations for test sub classes.

    Metadata describing streams. A bunch of shared methods that are used
    in tap-tester tests. Shared tap-specific methods (as needed).
    """
    start_date = "2019-01-01T00:00:00Z"
    PARENT_TAP_STREAM_ID = "parent-tap-stream-id"

    @staticmethod
    def tap_name():
        """The name of the tap."""
        return "tap-ukg_pro_ultipro"

    @staticmethod
    def get_type():
        """The name of the tap."""
        return "platform.ukg_pro_ultipro"

    @classmethod
    def expected_metadata(cls):
        """The expected streams and metadata about the streams."""
        return {
            "company_details": {
                cls.PRIMARY_KEYS: { "companyId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "earnings": {
                cls.PRIMARY_KEYS: { "earningCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "insurance_rates": {
                cls.PRIMARY_KEYS: { "deductionCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "job_groups": {
                cls.PRIMARY_KEYS: { "jobGroupCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "jobs": {
                cls.PRIMARY_KEYS: { "jobCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "locations": {
                cls.PRIMARY_KEYS: { "locationCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "option_rates": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "organization_reporting_category": {
                cls.PRIMARY_KEYS: { "code" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "position_reports": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "positions": {
                cls.PRIMARY_KEYS: { "integrationRecordId" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "shift_codes": {
                cls.PRIMARY_KEYS: { "shiftCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "tax_groups": {
                cls.PRIMARY_KEYS: { "taxCalcGroupIdCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "user_profile_details": {
                cls.PRIMARY_KEYS: { "userId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "org_levels": {
                cls.PRIMARY_KEYS: { "code", "level" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "award_type": {
                cls.PRIMARY_KEYS: { "code" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "career_provider": {
                cls.PRIMARY_KEYS: { "code" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "earnings_history_base_elements": {
                cls.PRIMARY_KEYS: { "companyId", "employeeId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "direct_deposits": {
                cls.PRIMARY_KEYS: { "accountRecordId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "general_ledgers": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "pay_register": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "pay_group_payperiods": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "payroll_deductions_history": {
                cls.PRIMARY_KEYS: { "recordId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "compensation_details": {
                cls.PRIMARY_KEYS: { "companyID", "employeeID" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_changes": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_cobra_details": {
                cls.PRIMARY_KEYS: { "personID" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "contacts": {
                cls.PRIMARY_KEYS: { "contactId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_contract_details": {
                cls.PRIMARY_KEYS: { "employeeId", "contractNumber" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_demographic_details": {
                cls.PRIMARY_KEYS: { "employeeId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_education": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_extended_elements": {
                cls.PRIMARY_KEYS: { "personID" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_job_history_details": {
                cls.PRIMARY_KEYS: { "employeeId", "jobEffectiveDate" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_multiple_jobs": {
                cls.PRIMARY_KEYS: { "employeeId", "jobCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_multi_phone_numbers": {
                cls.PRIMARY_KEYS: { "employeeId", "auditKey" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_multi_positions": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "national_documents": {
                cls.PRIMARY_KEYS: { "employeeId", "nationalDocumentId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_supervisor_details": {
                cls.PRIMARY_KEYS: { "employeeID" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_status": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employment_details": {
                cls.PRIMARY_KEYS: { "companyID", "employeeID" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_global_banks": {
                cls.PRIMARY_KEYS: { "bankId", "employeeId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_global_localization_elements": {
                cls.PRIMARY_KEYS: { "employeeId", "fieldId" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "created" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_pay_deduction_elements": {
                cls.PRIMARY_KEYS: { "employeeId", "payDeductionId" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "modifiedDate" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "international_employees": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "open_enrollment_employee_deductions": {
                cls.PRIMARY_KEYS: { "employeeId", "deductionCode" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "createDatetime" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_deductions": {
                cls.PRIMARY_KEYS: { "employeeID", "deductionCode" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "dependent_deductions": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "dateTimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "person_details": {
                cls.PRIMARY_KEYS: { "employeeId" },
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: { "datetimeCreated" },
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "pto_plans": {
                cls.PRIMARY_KEYS: { "employeeId", "companyId", "ptoPlan" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_user_defined_fields": {
                cls.PRIMARY_KEYS: { "employeeId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "employee_security_user_details": {
                cls.PRIMARY_KEYS: set(),
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "roles": {
                cls.PRIMARY_KEYS: { "rolID" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            },
            "user_details": {
                cls.PRIMARY_KEYS: { "userId" },
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100
            }
        }

    @staticmethod
    def get_credentials():
        """Authentication information for the test account."""
        credentials_dict = {}
        creds = {
            'username': 'TAP_UKG_PRO_ULTIPRO_USERNAME',
            'password': 'TAP_UKG_PRO_ULTIPRO_PASSWORD',
            'api_key': 'TAP_UKG_PRO_ULTIPRO_API_KEY',
            'hostname': 'TAP_UKG_PRO_ULTIPRO_HOSTNAME',
        }

        for cred in creds:
            credentials_dict[cred] = os.getenv(creds[cred])

        return credentials_dict

    def get_properties(self, original: bool = True):
        """Configuration of properties required for the tap."""
        return_value = {
            "start_date": "2022-07-01T00:00:00Z"
        }
        if original:
            return return_value

        return_value["start_date"] = self.start_date
        return return_value

    def expected_parent_tap_stream(self, stream=None):
        """return a dictionary with key of table name and value of parent stream"""
        parent_stream = {
            table: properties.get(self.PARENT_TAP_STREAM_ID, None)
            for table, properties in self.expected_metadata().items()}
        if not stream:
            return parent_stream
        return parent_stream[stream]
