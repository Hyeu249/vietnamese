DOCKING_MATERIAL_QUOTE = "docking.material.quote"
DOCKING_JOB_QUOTE = "docking.job.quote"

SUPPLIER = "group_ship_supplier"
TECHNICAL_EXPERT = "group_ship_technical_expert"
MATERIAL_EXPERT = "group_ship_material_expert"


PENDING = "PENDING"
APPROVED = "APPROVED"
REJECTED = "REJECTED"

APPROVAL_STATES = [
    (APPROVED, "Approved"),
    (PENDING, "Pending"),
    (REJECTED, "Rejected"),
]

MATERIAL = "MATERIAL"
SPARE_PART = "SPARE_PART"
PAINT = "PAINT"

MATERIAL_TYPE = [
    (MATERIAL, "Material"),
    (SPARE_PART, "Spare part"),
    (PAINT, "Paint"),
]

MACHINERY = "MACHINERY"
BOONG = "BOONG"

DEPARTMENT_IN_CHARGE = [
    (MACHINERY, "Machinery"),
    (BOONG, "Boong"),
]

UNAPPROVED = "UNAPPROVED"
TODO = "TODO"
WORKING = "WORKING"
COMPLETED = "COMPLETED"
CONFIRMED = "CONFIRMED"


WORK_STATES = [
    (UNAPPROVED, "Unapproved"),
    (TODO, "Todo"),
    (WORKING, "Working"),
    (COMPLETED, "Completed"),
    (CONFIRMED, "Confirmed"),
]

APPROVAL_FLOW_TYPE_SURVEY = "survey-approval-flow"
APPROVAL_FLOW_TYPE_JOB_QUOTE = "job-quote-approval-flow"
APPROVAL_FLOW_TYPE_MATERIAL_QUOTE = "material-quote-approval-flow"
APPROVAL_FLOW_TYPE_EXPECTED_COST_REPORT = "expected-cost-report-approval-flow"
APPROVAL_FLOW_TYPE_SCOPE_REPORT = "maintenance-scope-report-approval-flow"
APPROVAL_FLOW_TYPE_CONTRACT = "contract-flow"
APPROVAL_FLOW_TYPE_COST_SETTLEMENT_REPORT = "cost-settlement-report-flow"

APPROVAL_FLOW_TYPES = [
    (APPROVAL_FLOW_TYPE_SURVEY, "Survey approval flow"),
    (APPROVAL_FLOW_TYPE_JOB_QUOTE, "Job quote approval flow"),
    (APPROVAL_FLOW_TYPE_MATERIAL_QUOTE, "Material/Paint quote approval flow"),
    (APPROVAL_FLOW_TYPE_EXPECTED_COST_REPORT, "Expected cost report approval flow"),
    (APPROVAL_FLOW_TYPE_SCOPE_REPORT, "Maintenance scope report approval flow"),
    (APPROVAL_FLOW_TYPE_CONTRACT, "Contract approval flow"),
    (APPROVAL_FLOW_TYPE_COST_SETTLEMENT_REPORT, "Cost settlement report approval flow"),
]

USER_FOR_NOTIFICATION = "USER_FOR_NOTIFICATION"
USER_NOTIFICATION_FOR_CHANGING_INSPECTION_DATE = (
    "USER_NOTIFICATION_FOR_CHANGING_INSPECTION_DATE"
)
EXPECT_START_DATE = "EXPECT_START_DATE"
HTML_VALUE = "HTML_VALUE"
DEFAULT_TYPES = [
    (USER_FOR_NOTIFICATION, "User For Notification"),
    (
        USER_NOTIFICATION_FOR_CHANGING_INSPECTION_DATE,
        "Notification for changing inspection date",
    ),
    (EXPECT_START_DATE, "Expected Start Date"),
    (HTML_VALUE, "Html Value"),
]

PAYMENT_STATUS = [
    (PENDING, "Pending"),
    (COMPLETED, "Completed"),
]

NORMAL = "NORMAL"
ARISE = "ARISE"

ARISE_SELECTION = [
    (NORMAL, "Normal"),
    (ARISE, "Arise"),
]

LOW = "LOW"
HIGH = "HIGH"

PRIORITY_SELECTION = [
    (LOW, "Low"),
    (HIGH, "High"),
]

MAX_IMAGE_UPLOAD_WIDTH = 1040
MAX_IMAGE_UPLOAD_HEIGHT = 1386
