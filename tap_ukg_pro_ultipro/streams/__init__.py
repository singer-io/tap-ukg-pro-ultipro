from tap_ukg_pro_ultipro.streams.company_details import CompanyDetails
from tap_ukg_pro_ultipro.streams.earnings import Earnings
from tap_ukg_pro_ultipro.streams.insurance_rates import InsuranceRates
from tap_ukg_pro_ultipro.streams.job_groups import JobGroups
from tap_ukg_pro_ultipro.streams.jobs import Jobs
from tap_ukg_pro_ultipro.streams.locations import Locations
from tap_ukg_pro_ultipro.streams.option_rates import OptionRates
from tap_ukg_pro_ultipro.streams.organization_reporting_category import OrganizationReportingCategory
from tap_ukg_pro_ultipro.streams.position_reports import PositionReports
from tap_ukg_pro_ultipro.streams.positions import Positions
from tap_ukg_pro_ultipro.streams.shift_codes import ShiftCodes
from tap_ukg_pro_ultipro.streams.tax_groups import TaxGroups
from tap_ukg_pro_ultipro.streams.user_profile_details import UserProfileDetails
from tap_ukg_pro_ultipro.streams.org_levels import OrgLevels
from tap_ukg_pro_ultipro.streams.award_type import AwardType
from tap_ukg_pro_ultipro.streams.career_provider import CareerProvider
from tap_ukg_pro_ultipro.streams.earnings_history_base_elements import EarningsHistoryBaseElements
from tap_ukg_pro_ultipro.streams.direct_deposits import DirectDeposits
from tap_ukg_pro_ultipro.streams.general_ledgers import GeneralLedgers
from tap_ukg_pro_ultipro.streams.pay_register import PayRegister
from tap_ukg_pro_ultipro.streams.pay_group_payperiods import PayGroupPayperiods
from tap_ukg_pro_ultipro.streams.payroll_deductions_history import PayrollDeductionsHistory
from tap_ukg_pro_ultipro.streams.compensation_details import CompensationDetails
from tap_ukg_pro_ultipro.streams.employee_changes import EmployeeChanges
from tap_ukg_pro_ultipro.streams.employee_cobra_details import EmployeeCobraDetails
from tap_ukg_pro_ultipro.streams.contacts import Contacts
from tap_ukg_pro_ultipro.streams.employee_contract_details import EmployeeContractDetails
from tap_ukg_pro_ultipro.streams.employee_demographic_details import EmployeeDemographicDetails
from tap_ukg_pro_ultipro.streams.employee_education import EmployeeEducation
from tap_ukg_pro_ultipro.streams.employee_extended_elements import EmployeeExtendedElements
from tap_ukg_pro_ultipro.streams.employee_job_history_details import EmployeeJobHistoryDetails
from tap_ukg_pro_ultipro.streams.employee_multiple_jobs import EmployeeMultipleJobs
from tap_ukg_pro_ultipro.streams.employee_multi_phone_numbers import EmployeeMultiPhoneNumbers
from tap_ukg_pro_ultipro.streams.employee_multi_positions import EmployeeMultiPositions
from tap_ukg_pro_ultipro.streams.national_documents import NationalDocuments
from tap_ukg_pro_ultipro.streams.employee_supervisor_details import EmployeeSupervisorDetails
from tap_ukg_pro_ultipro.streams.employee_status import EmployeeStatus
from tap_ukg_pro_ultipro.streams.employment_details import EmploymentDetails
from tap_ukg_pro_ultipro.streams.employee_global_banks import EmployeeGlobalBanks
from tap_ukg_pro_ultipro.streams.employee_global_localization_elements import EmployeeGlobalLocalizationElements
from tap_ukg_pro_ultipro.streams.employee_pay_deduction_elements import EmployeePayDeductionElements
from tap_ukg_pro_ultipro.streams.international_employees import InternationalEmployees
from tap_ukg_pro_ultipro.streams.open_enrollment_employee_deductions import OpenEnrollmentEmployeeDeductions
from tap_ukg_pro_ultipro.streams.employee_deductions import EmployeeDeductions
from tap_ukg_pro_ultipro.streams.dependent_deductions import DependentDeductions
from tap_ukg_pro_ultipro.streams.person_details import PersonDetails
from tap_ukg_pro_ultipro.streams.pto_plans import PtoPlans
from tap_ukg_pro_ultipro.streams.employee_user_defined_fields import EmployeeUserDefinedFields
from tap_ukg_pro_ultipro.streams.employee_security_user_details import EmployeeSecurityUserDetails
from tap_ukg_pro_ultipro.streams.roles import Roles
from tap_ukg_pro_ultipro.streams.user_details import UserDetails

STREAMS = {
    "company_details": CompanyDetails,
    "earnings": Earnings,
    "insurance_rates": InsuranceRates,
    "job_groups": JobGroups,
    "jobs": Jobs,
    "locations": Locations,
    "option_rates": OptionRates,
    "organization_reporting_category": OrganizationReportingCategory,
    "position_reports": PositionReports,
    "positions": Positions,
    "shift_codes": ShiftCodes,
    "tax_groups": TaxGroups,
    "user_profile_details": UserProfileDetails,
    "org_levels": OrgLevels,
    "award_type": AwardType,
    "career_provider": CareerProvider,
    "earnings_history_base_elements": EarningsHistoryBaseElements,
    "direct_deposits": DirectDeposits,
    "general_ledgers": GeneralLedgers,
    "pay_register": PayRegister,
    "pay_group_payperiods": PayGroupPayperiods,
    "payroll_deductions_history": PayrollDeductionsHistory,
    "compensation_details": CompensationDetails,
    "employee_changes": EmployeeChanges,
    "employee_cobra_details": EmployeeCobraDetails,
    "contacts": Contacts,
    "employee_contract_details": EmployeeContractDetails,
    "employee_demographic_details": EmployeeDemographicDetails,
    "employee_education": EmployeeEducation,
    "employee_extended_elements": EmployeeExtendedElements,
    "employee_job_history_details": EmployeeJobHistoryDetails,
    "employee_multiple_jobs": EmployeeMultipleJobs,
    "employee_multi_phone_numbers": EmployeeMultiPhoneNumbers,
    "employee_multi_positions": EmployeeMultiPositions,
    "national_documents": NationalDocuments,
    "employee_supervisor_details": EmployeeSupervisorDetails,
    "employee_status": EmployeeStatus,
    "employment_details": EmploymentDetails,
    "employee_global_banks": EmployeeGlobalBanks,
    "employee_global_localization_elements": EmployeeGlobalLocalizationElements,
    "employee_pay_deduction_elements": EmployeePayDeductionElements,
    # "international_employees": InternationalEmployees,
    # "open_enrollment_employee_deductions": OpenEnrollmentEmployeeDeductions,
    # "employee_deductions": EmployeeDeductions,
    "dependent_deductions": DependentDeductions,
    "person_details": PersonDetails,
    "pto_plans": PtoPlans,
    "employee_user_defined_fields": EmployeeUserDefinedFields,
    "employee_security_user_details": EmployeeSecurityUserDetails,
    "roles": Roles,
    "user_details": UserDetails,
}
