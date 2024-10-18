from dateutil.relativedelta import relativedelta

PENDING = "PENDING"
APPROVED = "APPROVED"
REJECTED = "REJECTED"

UNAPPROVED = "UNAPPROVED"
TODO = "TODO"
WORKING = "WORKING"
COMPLETED = "COMPLETED"
CONFIRMED = "CONFIRMED"


APPROVAL_STATUS = [
    (PENDING, "Pending"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected"),
]


# inspection task satus
SATISFIED = "SATISFIED"
UNSATISFIED = "UNSATISFIED"
PENDING = "PENDING"
NEED_REVIEW = "NEED_REVIEW"

INSPECTION_STATUS = [
    (PENDING, "Pending"),
    (UNSATISFIED, "Unsatisfied"),
    (NEED_REVIEW, "Need review"),
    (SATISFIED, "Satisfied"),
]

# inspection task types
NEW = "NEW"
LAST_MONTH_BACKLOG = "LAST_MONTH_BACKLOG"
BACKLOGGED = "BACKLOGGED"

TASK_TYPE = [
    (NEW, "New"),
    (LAST_MONTH_BACKLOG, "Backlog from last month"),
    (BACKLOGGED, "Backlogged"),
]

# security group ids
CEO = "group_ship_ceo"
HEAD_MANAGER = "group_ship_head_of_manager"
VICE_CAPTAIN_HEAD_MACHINERY = "group_ship_vice_captain_head_machinery"
CAPTAIN = "group_ship_captain"
VICE_CAPTAIN = "group_ship_vice_captain"
HEAD_DEPARTMENT = "group_ship_head_of_department"
HEAD_MACHINERY = "group_ship_head_of_machinery"
TECHNICAL_EXPERT = "group_ship_technical_expert"
MATERIAL_EXPERT = "group_ship_material_expert"
CREW = "group_ship_ship_crew"
SUPPLIER = "group_ship_supplier"

# states
PREPARE = "PREPARE"
MATERIAL_EXPERT_AFTER_PRICE = "group_ship_material_expert_after_price"
HEAD_AFTER_PRICE = "group_ship_head_of_department_after_price"
HEAD_MANAGER_AFTER_PRICE = "group_ship_head_of_manager_after_price"
CEO_AFTER_PRICE = "group_ship_ceo_after_price"
CREATE_QUOTE = "CREATE_QUOTE"
CREATE_SUPPLIER_QUOTE = "CREATE_SUPPLIER_QUOTE"

PREVIOUS_MATERIAL_PAINT_QUOTES_REQUEST_STATE = {
    PREPARE: PREPARE,
    VICE_CAPTAIN_HEAD_MACHINERY: PREPARE,
    CAPTAIN: VICE_CAPTAIN_HEAD_MACHINERY,
    TECHNICAL_EXPERT: CAPTAIN,
    MATERIAL_EXPERT: TECHNICAL_EXPERT,
    SUPPLIER: MATERIAL_EXPERT,
    MATERIAL_EXPERT_AFTER_PRICE: MATERIAL_EXPERT,
    HEAD_AFTER_PRICE: MATERIAL_EXPERT_AFTER_PRICE,
    HEAD_MANAGER_AFTER_PRICE: HEAD_AFTER_PRICE,
    CEO_AFTER_PRICE: HEAD_MANAGER_AFTER_PRICE,
    APPROVED: HEAD_MANAGER_AFTER_PRICE,
    REJECTED: HEAD_MANAGER_AFTER_PRICE,
}

MATERIAL_PAINT_QUOTES_REQUEST_STATES = [
    (PREPARE, "Prepare Request"),
    (VICE_CAPTAIN_HEAD_MACHINERY, "Vice Captain And Head Machinery"),
    (CAPTAIN, "Captain"),
    (TECHNICAL_EXPERT, "Technical Expert"),
    (MATERIAL_EXPERT, "Material Expert"),
    (SUPPLIER, "Supplier"),
    (MATERIAL_EXPERT_AFTER_PRICE, "Material Expert"),
    (HEAD_AFTER_PRICE, "Head of Department"),
    (HEAD_MANAGER_AFTER_PRICE, "Head Manager"),
    (CEO_AFTER_PRICE, "Ceo"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected"),
]

REQUEST_STATES_THAT_NOT_ALLOW_EDIT_THE_PRICE = [
    SUPPLIER,
    MATERIAL_EXPERT_AFTER_PRICE,
    HEAD_AFTER_PRICE,
    HEAD_MANAGER_AFTER_PRICE,
    CEO_AFTER_PRICE,
    APPROVED,
    REJECTED,
]

SEND_SUPPLIER_MATERIAL_PAINT_QUOTES = [
    SUPPLIER,
    MATERIAL_EXPERT_AFTER_PRICE,
    HEAD_AFTER_PRICE,
    HEAD_MANAGER_AFTER_PRICE,
    CEO_AFTER_PRICE,
    APPROVED,
    REJECTED,
]

material_paint_quotes_request_request_state_to_group_xml_ids = {
    PREPARE: [],
    VICE_CAPTAIN_HEAD_MACHINERY: [],
    CAPTAIN: [VICE_CAPTAIN_HEAD_MACHINERY],
    TECHNICAL_EXPERT: [VICE_CAPTAIN_HEAD_MACHINERY, CAPTAIN],
    MATERIAL_EXPERT: [VICE_CAPTAIN_HEAD_MACHINERY, CAPTAIN, TECHNICAL_EXPERT],
    SUPPLIER: [VICE_CAPTAIN_HEAD_MACHINERY, CAPTAIN, TECHNICAL_EXPERT, MATERIAL_EXPERT],
    MATERIAL_EXPERT_AFTER_PRICE: [
        VICE_CAPTAIN_HEAD_MACHINERY,
        CAPTAIN,
        TECHNICAL_EXPERT,
    ],
    HEAD_AFTER_PRICE: [
        VICE_CAPTAIN_HEAD_MACHINERY,
        CAPTAIN,
        TECHNICAL_EXPERT,
        MATERIAL_EXPERT,
    ],
    HEAD_MANAGER_AFTER_PRICE: [
        VICE_CAPTAIN_HEAD_MACHINERY,
        CAPTAIN,
        TECHNICAL_EXPERT,
        MATERIAL_EXPERT,
        HEAD_DEPARTMENT,
    ],
    CEO_AFTER_PRICE: [
        VICE_CAPTAIN_HEAD_MACHINERY,
        CAPTAIN,
        TECHNICAL_EXPERT,
        MATERIAL_EXPERT,
        HEAD_DEPARTMENT,
        HEAD_MANAGER,
    ],
    APPROVED: [
        VICE_CAPTAIN_HEAD_MACHINERY,
        CAPTAIN,
        TECHNICAL_EXPERT,
        MATERIAL_EXPERT,
        HEAD_DEPARTMENT,
        HEAD_MANAGER,
    ],
    REJECTED: [
        VICE_CAPTAIN_HEAD_MACHINERY,
        CAPTAIN,
        TECHNICAL_EXPERT,
        MATERIAL_EXPERT,
        HEAD_DEPARTMENT,
        HEAD_MANAGER,
    ],
}

material_paint_quotes_request_request_state_to_group_xml_id = {
    PREPARE: None,
    VICE_CAPTAIN_HEAD_MACHINERY: VICE_CAPTAIN_HEAD_MACHINERY,
    CAPTAIN: CAPTAIN,
    TECHNICAL_EXPERT: TECHNICAL_EXPERT,
    MATERIAL_EXPERT: MATERIAL_EXPERT,
    SUPPLIER: None,
    MATERIAL_EXPERT_AFTER_PRICE: MATERIAL_EXPERT,
    HEAD_AFTER_PRICE: HEAD_DEPARTMENT,
    HEAD_MANAGER_AFTER_PRICE: HEAD_MANAGER,
    CEO_AFTER_PRICE: CEO,
    APPROVED: None,
    REJECTED: None,
}

job_quote_request_state_to_group_xml_ids = {
    PREPARE: [],
    SUPPLIER: [CREW],
    TECHNICAL_EXPERT: [CREW],
    HEAD_DEPARTMENT: [CREW, TECHNICAL_EXPERT],
    HEAD_MANAGER: [CREW, TECHNICAL_EXPERT, HEAD_DEPARTMENT],
    CEO: [CREW, TECHNICAL_EXPERT, HEAD_DEPARTMENT, HEAD_MANAGER],
    APPROVED: [CREW, TECHNICAL_EXPERT, HEAD_DEPARTMENT, HEAD_MANAGER],
    REJECTED: [CREW, TECHNICAL_EXPERT, HEAD_DEPARTMENT, HEAD_MANAGER],
}

job_quote_request_state_to_group_xml_id = {
    PREPARE: None,
    SUPPLIER: None,
    TECHNICAL_EXPERT: TECHNICAL_EXPERT,
    HEAD_DEPARTMENT: HEAD_DEPARTMENT,
    HEAD_MANAGER: HEAD_MANAGER,
    CEO: CEO,
    APPROVED: None,
    REJECTED: None,
}

PREVIOUS_JOB_QUOTE_REQUEST_STATE = {
    PREPARE: PREPARE,
    SUPPLIER: PREPARE,
    TECHNICAL_EXPERT: PREPARE,
    HEAD_DEPARTMENT: TECHNICAL_EXPERT,
    HEAD_MANAGER: HEAD_DEPARTMENT,
    CEO: HEAD_MANAGER,
    APPROVED: HEAD_MANAGER,
    REJECTED: HEAD_MANAGER,
}

JOB_QUOTE_REQUEST_STATES = [
    (PREPARE, "Prepare Request"),
    (SUPPLIER, "Supplier"),
    (TECHNICAL_EXPERT, "Technical Expert"),
    (HEAD_DEPARTMENT, "Head of Department"),
    (HEAD_MANAGER, "Head of Manager"),
    (CEO, "Ceo"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected"),
]

ACCESS_TOKEN_LENGTH = 64
DATE = "DATE"
STR = "STR"
CURRENT_WEEK = "CURRENT_WEEK"
NEXT_WEEK = "NEXT_WEEK"
PREVIOUS_WEEK = "PREVIOUS_WEEK"

THIRTY_DAYS = 30
SEVEN_DAYS = 7

WEEKLY = "WEEKLY"
ONE_MONTH = "ONE_MONTH"
TWO_MONTH = "TWO_MONTH"
THREE_MONTH = "THREE_MONTH"
FOUR_MONTH = "FOUR_MONTH"
FIVE_MONTH = "FIVE_MONTH"
SIX_MONTH = "SIX_MONTH"
SEVEN_MONTH = "SEVEN_MONTH"
EIGHT_MONTH = "EIGHT_MONTH"
NINE_MONTH = "NINE_MONTH"
TEN_MONTH = "TEN_MONTH"
ELEVEN_MONTH = "ELEVEN_MONTH"
ONE_YEAR = "ONE_YEAR"
TWO_YEARS = "TWO_YEARS"
TWO_AND_A_HALF_YEARS = "TWO_AND_A_HALF_YEARS"
THREE_YEARS = "THREE_YEARS"
FOUR_YEARS = "FOUR_YEARS"
FIVE_YEARS = "FIVE_YEARS"

MAINTENANCE_INTERVAL = {
    WEEKLY: relativedelta(days=7),
    ONE_MONTH: relativedelta(months=1),
    TWO_MONTH: relativedelta(months=2),
    THREE_MONTH: relativedelta(months=3),
    FOUR_MONTH: relativedelta(months=4),
    FIVE_MONTH: relativedelta(months=5),
    SIX_MONTH: relativedelta(months=6),
    SEVEN_MONTH: relativedelta(months=7),
    EIGHT_MONTH: relativedelta(months=8),
    NINE_MONTH: relativedelta(months=9),
    TEN_MONTH: relativedelta(months=10),
    ELEVEN_MONTH: relativedelta(months=11),
    ONE_YEAR: relativedelta(years=1),
    TWO_YEARS: relativedelta(years=2),
    TWO_AND_A_HALF_YEARS: relativedelta(years=2) + relativedelta(months=6),
    THREE_YEARS: relativedelta(years=3),
    FOUR_YEARS: relativedelta(years=4),
    FIVE_YEARS: relativedelta(years=5),
}

MAINTENANCE_INTERVAL_SELECTION = [
    (WEEKLY, "Weekly"),
    (ONE_MONTH, "One Month"),
    (TWO_MONTH, "Two Months"),
    (THREE_MONTH, "Three Months"),
    (FOUR_MONTH, "Four Months"),
    (FIVE_MONTH, "Five Months"),
    (SIX_MONTH, "Six Months"),
    (SEVEN_MONTH, "Seven Months"),
    (EIGHT_MONTH, "Eight Months"),
    (NINE_MONTH, "Nine Months"),
    (TEN_MONTH, "Ten Months"),
    (ELEVEN_MONTH, "Eleven Months"),
    (ONE_YEAR, "1 Year"),
    (TWO_YEARS, "2 Year"),
    (TWO_AND_A_HALF_YEARS, "2,5 Year"),
    (THREE_YEARS, "3 Year"),
    (FOUR_YEARS, "4 Year"),
    (FIVE_YEARS, "5 Year"),
]

MAINTENANCE_DAYS_SELECTION = [
    (str(SEVEN_DAYS), "Weekly"),
    (str(THIRTY_DAYS), "One Month"),
    (str(THIRTY_DAYS * 2), "Two Months"),
    (str(THIRTY_DAYS * 3), "Three Months"),
    (str(THIRTY_DAYS * 4), "Four Months"),
    (str(THIRTY_DAYS * 5), "Five Months"),
    (str(THIRTY_DAYS * 6), "Six Months"),
    (str(THIRTY_DAYS * 7), "Seven Months"),
    (str(THIRTY_DAYS * 8), "Eight Months"),
    (str(THIRTY_DAYS * 9), "Nine Months"),
    (str(THIRTY_DAYS * 10), "Ten Months"),
    (str(THIRTY_DAYS * 11), "Eleven Months"),
    (str(THIRTY_DAYS * 12), "Twelve Months"),
    (str(THIRTY_DAYS * 24), "2 Years"),
    (str(THIRTY_DAYS * 30), "2,5 Years"),
    (str(THIRTY_DAYS * 36), "3 Years"),
    (str(THIRTY_DAYS * 48), "4 Years"),
    (str(THIRTY_DAYS * 60), "5 Years"),
]

MAINTENANCE_INTERVAL_CONVERTER = {
    str(SEVEN_DAYS): WEEKLY,
    str(THIRTY_DAYS): ONE_MONTH,
    str(THIRTY_DAYS * 2): TWO_MONTH,
    str(THIRTY_DAYS * 3): THREE_MONTH,
    str(THIRTY_DAYS * 4): FOUR_MONTH,
    str(THIRTY_DAYS * 5): FIVE_MONTH,
    str(THIRTY_DAYS * 6): SIX_MONTH,
    str(THIRTY_DAYS * 7): SEVEN_DAYS,
    str(THIRTY_DAYS * 8): EIGHT_MONTH,
    str(THIRTY_DAYS * 9): NINE_MONTH,
    str(THIRTY_DAYS * 10): TEN_MONTH,
    str(THIRTY_DAYS * 11): ELEVEN_MONTH,
    str(THIRTY_DAYS * 12): ONE_YEAR,
    str(THIRTY_DAYS * 24): TWO_YEARS,
    str(THIRTY_DAYS * 30): TWO_AND_A_HALF_YEARS,
    str(THIRTY_DAYS * 36): THREE_YEARS,
    str(THIRTY_DAYS * 48): FOUR_YEARS,
    str(THIRTY_DAYS * 60): FIVE_YEARS,
}

JOB_STATES = [
    (UNAPPROVED, "Unapproved"),
    (TODO, "Todo"),
    (WORKING, "Working"),
    (COMPLETED, "Completed"),
    (CONFIRMED, "Confirmed"),
]

WAITING_FOR_DOCKING = "WAITING_FOR_DOCKING"

JOB_STATES_FOR_SHIP = [
    (WAITING_FOR_DOCKING, "Waiting for docking"),
    (UNAPPROVED, "Unapproved"),
    (TODO, "Todo"),
    (WORKING, "Working"),
    (COMPLETED, "Completed"),
    (CONFIRMED, "Confirmed"),
]

UNDUE = "UNDUE"
TODAY = "TODAY"
OVERDUE = "OVERDUE"
BLANK = "BLANK"


SCHEDULE_STATES = [
    (UNDUE, "Undue"),
    (TODAY, "Today"),
    (OVERDUE, "Over due"),
    (BLANK, "Blank"),
]

SHIP_MATERIAL_PAINT_QUOTES_REQUEST = "SHIP_MATERIAL_PAINT_QUOTES_REQUEST"
SHIP_JOB_QUOTE = "SHIP_JOB_QUOTE"
MAINTENANCE_SCOPE_REPORT = "MAINTENANCE_SCOPE_REPORT"

DEADLINE = "DEADLINE"
VALID_APPROVAL_DATE = "VALID_APPROVAL_DATE"

DEADLINE_VALUE = 7
VALID_APPROVAL_DATE_VALUE = 14


DEFAULT_VALUE_RECORDS = [
    (SHIP_MATERIAL_PAINT_QUOTES_REQUEST, DEADLINE, DEADLINE_VALUE),
    (SHIP_JOB_QUOTE, DEADLINE, DEADLINE_VALUE),
    (SHIP_JOB_QUOTE, VALID_APPROVAL_DATE, VALID_APPROVAL_DATE_VALUE),
]


MATERIAL = "MATERIAL"
PAINT = "PAINT"
JOB = "JOB"

VAT_TU = "Vật tư"
SON = "Sơn"
CONG_VIEC = "Công việc"

CLASSIFY_RECORDS = [
    (VAT_TU, "Material"),
    (SON, "Paint"),
    (CONG_VIEC, "Job"),
]

LOW = "LOW"
HIGH = "HIGH"

PRIORITY_SELECTION = [
    (LOW, "Low"),
    (HIGH, "High"),
]

RED_CODE = 285
YELLOW_CODE = 255
GREEN_CODE = 250

VALUE_TO_NAME = {
    PREPARE: "",
    SUPPLIER: "bởi Nhà cung cấp",
    TECHNICAL_EXPERT: "bởi Chuyên viên kỹ thuật",
    HEAD_DEPARTMENT: "bởi Trưởng kỹ thuật & trưởng pháp chế",
    HEAD_MANAGER: "bởiTrưởng quản lý tàu",
    CEO: "bởi Ceo",
    APPROVED: "",
    REJECTED: "",
}

ADD_ACTION = "add"
MINUS_ACTION = "minus"
ACTIONS = [
    (ADD_ACTION, "Add"),
    (MINUS_ACTION, "Minus"),
]

CONSUMABLE_MATERIAL = "CONSUMABLE_MATERIAL"
SPARE_PART = "SPARE_PART"

MATERIAL_TYPE = [
    (MATERIAL, "Material"),
    (CONSUMABLE_MATERIAL, "Consumable Material"),
    (SPARE_PART, "Spare part"),
]

THRESHOLD = "THRESHOLD"
ARISE = "ARISE"
CONSUMPTION = "CONSUMPTION"

MAINTENANCE_TYPE = [
    (ARISE, "Arise"),
    (THRESHOLD, "Threshold"),
    (CONSUMPTION, "Consumption"),
]

EACH_ENTITY = "EACH_ENTITY"
GROUP_ENTITY = "GROUP_ENTITY"


STORE_TYPE = [
    (EACH_ENTITY, "Each Entity"),
    (GROUP_ENTITY, "Group Entity"),
]

MACHINERY = "MACHINERY"
BOONG = "BOONG"

DEPARTMENT_IN_CHARGE = [
    (MACHINERY, "Machinery"),
    (BOONG, "Boong"),
]

NONE = "NONE"
DAY = "DAY"
WEEK = "WEEK"
MONTH = "MONTH"
TIME_TYPE = [
    (NONE, "None"),
    (DAY, "Day"),
    (WEEK, "Week"),
    (MONTH, "Month"),
]
FUEL_QUOTES_REQUEST_STATES = [
    (PREPARE, "Prepare Request"),
    (MATERIAL_EXPERT, "Material Expert"),
    (HEAD_DEPARTMENT, "Head Department"),
    (HEAD_MANAGER, "Head Manager"),
    (CEO, "Ceo"),
    (SUPPLIER, "Supplier"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected"),
]

PREVIOUS_FUEL_QUOTES_REQUEST_STATE = {
    PREPARE: PREPARE,
    MATERIAL_EXPERT: PREPARE,
    HEAD_DEPARTMENT: MATERIAL_EXPERT,
    HEAD_MANAGER: HEAD_DEPARTMENT,
    CEO: HEAD_MANAGER,
    SUPPLIER: CEO,
    APPROVED: HEAD_MANAGER,
    REJECTED: HEAD_MANAGER,
}

FUEL_QUOTES_REQUEST_STATES_2 = [
    (PREPARE, "Prepare Request"),
    (MATERIAL_EXPERT, "Material Expert"),
    (HEAD_MANAGER, "Head Manager"),
    (MATERIAL_EXPERT_AFTER_PRICE, "Material Expert"),
    (CEO, "Ceo"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected"),
    (SUPPLIER, "Supplier"),
]
PREVIOUS_FUEL_QUOTES_REQUEST_STATE_2 = {
    PREPARE: PREPARE,
    MATERIAL_EXPERT: PREPARE,
    HEAD_MANAGER: MATERIAL_EXPERT,
    MATERIAL_EXPERT_AFTER_PRICE: HEAD_MANAGER,
    CEO: HEAD_MANAGER,
    SUPPLIER: MATERIAL_EXPERT,
}

# PREVIOUS_FUEL_QUOTES_REQUEST_EXTERNAL_STATE = {
#    PREPARE: PREPARE,
#    CAPTAIN: PREPARE,
#    MATERIAL_EXPERT: CAPTAIN,
#    HEAD_DEPARTMENT: MATERIAL_EXPERT,
#    CEO: HEAD_DEPARTMENT,
#    HEAD_MANAGER_AFTER_PRICE: CEO,
# }
# FUEL_QUOTES_REQUEST_EXTERNAL_STATES = [
#    (PREPARE, "Prepare Request"),
#    (MATERIAL_EXPERT, "Material Expert"),
#    (HEAD_MANAGER, "Head Manager"),
#    (CEO, "Ceo"),
#    (HEAD_MANAGER_AFTER_PRICE, "Head Manager"),
#    (APPROVED, "Approved"),
#    (REJECTED, "Rejected"),
# ]

FUEL_QUOTES_REQUEST_EXTERNAL_STATES = [
    ("prepare", "Prepare Request"),
    ("material_expert", "Material Expert"),
    ("head_manager", "Head Manager"),
    ("ceo", "CEO"),
    ("approve", "Approved"),
]

PREVIOUS_FUEL_QUOTES_REQUEST_EXTERNAL_STATE = {
    "prepare": "prepare",
    "material_expert": "prepare",
    "head_manager": "material_expert",
    "ceo": "head_manager",
    "approve": "ceo",
}

SEND_SUPPLIER_FUEL_QUOTES = [SUPPLIER]

APPROVAL_FLOW_TYPE_SURVEY = "survey-approval-flow"
APPROVAL_FLOW_TYPE_JOB_QUOTE = "job-quote-approval-flow"
APPROVAL_FLOW_TYPE_MATERIAL_QUOTE = "material-quote-approval-flow"
APPROVAL_FLOW_TYPE_EXPECTED_COST_REPORT = "expected-cost-report-approval-flow"
APPROVAL_FLOW_TYPE_SCOPE_REPORT = "maintenance-scope-report-approval-flow"
APPROVAL_FLOW_TYPE_CONTRACT = "contract-flow"
APPROVAL_FLOW_TYPE_PROPOSED_LIQUIDATION = "proposed-liquidation-flow"
APPROVAL_FLOW_TYPE_COST_SETTLEMENT_REPORT = "cost-settlement-report-flow"

APPROVAL_FLOW_TYPES = [
    (APPROVAL_FLOW_TYPE_SURVEY, "Survey approval flow"),
    (APPROVAL_FLOW_TYPE_JOB_QUOTE, "Job quote approval flow"),
    (APPROVAL_FLOW_TYPE_MATERIAL_QUOTE, "Material/Paint quote approval flow"),
    (APPROVAL_FLOW_TYPE_EXPECTED_COST_REPORT, "Expected cost report approval flow"),
    (APPROVAL_FLOW_TYPE_SCOPE_REPORT, "Maintenance scope report approval flow"),
    (APPROVAL_FLOW_TYPE_CONTRACT, "Contract approval flow"),
    (APPROVAL_FLOW_TYPE_PROPOSED_LIQUIDATION, "Proposed liquidation approval flow"),
    (APPROVAL_FLOW_TYPE_COST_SETTLEMENT_REPORT, "Cost settlement report approval flow"),
]

NORMAL = "NORMAL"

QUOTE_STATE = [
    (NORMAL, "Normal"),
    (REJECTED, "Rejected"),
]

FUEL = "FUEL"
CURRENT_FO = "CURRENT_FO"
CURRENT_DO = "CURRENT_DO"

PAINT_HISTORY = "PAINT_HISTORY"
MATERIAL_HISTORY = "MATERIAL_HISTORY"
ESSENTIAL_MATERIAL = "ESSENTIAL_MATERIAL"
LASHING_MATERIAL = "LASHING_MATERIAL"
MEDICINE_REPORT = "MEDICINE_REPORT"
REPORT_TYPE = [
    (PAINT_HISTORY, "Paint history"),
    (MATERIAL_HISTORY, "Material history"),
    (ESSENTIAL_MATERIAL, "Essential material"),
    (LASHING_MATERIAL, "Lashing material"),
    (MEDICINE_REPORT, "Medicine report"),
]

TOOL = "TOOL"
WAREHOUSES = [
    (MACHINERY, "Machinery"),
    (BOONG, "Boong"),
    (TOOL, "Tool"),
]

CHECK_TO_BERTHING = "CHECK_TO_BERTHING"
CHECK_TO_TRANSFER = "CHECK_TO_TRANSFER"

CHECK_TYPE = [
    (CHECK_TO_BERTHING, "Check to berthing"),
    (CHECK_TO_TRANSFER, "Check to transfer"),
]

EMPTY = "EMPTY.EMPTY"

TANK_NAME_SELECTION = [
    ("F.O.T NO.2 P", "F.O.T NO.2 P"),
    ("F.O.T NO.2 S", "F.O.T NO.2 S"),
    ("F.O.T NO.1 P", "F.O.T NO.1 P"),
    ("F.O.T NO.1 S", "F.O.T NO.1 S"),
    ("D.O.T NO.1 P", "D.O.T NO.1 P"),
    ("D.O.T NO.1 S", "D.O.T NO.1 S"),
]

MAX_IMAGE_UPLOAD_WIDTH = 1040
MAX_IMAGE_UPLOAD_HEIGHT = 1386

INTERNAL_AUDIT_PURPOSE = "INTERNAL_AUDIT_PURPOSE"
INSPECTION_PURPOSE = "INSPECTION_PURPOSE"
DEPARTMENT_AUDIT_PURPOSE = "DEPARTMENT_AUDIT_PURPOSE"

INTERNAL_AUDIT_CHECKLIST_PURPOSE = [
    (INTERNAL_AUDIT_PURPOSE, "Internal audit"),
    (INSPECTION_PURPOSE, "Inspection"),
    (DEPARTMENT_AUDIT_PURPOSE, "Department audit"),
]

AUDIT_CHECKLIST_YES = "AUDIT_CHECKLIST_YES"
AUDIT_CHECKLIST_NO = "AUDIT_CHECKLIST_NO"
AUDIT_CHECKLIST_NOT_SATISFIED = "AUDIT_CHECKLIST_NOT_SATISFIED"

CHECKLIST_YES_NO = [
    (AUDIT_CHECKLIST_YES, "Yes"),
    (AUDIT_CHECKLIST_NO, "No"),
    (AUDIT_CHECKLIST_NOT_SATISFIED, "Not satisfied"),
]
