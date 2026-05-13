from enum import Enum



class CustomerPaymentCycleEnums(str,Enum):
    SEVEN_DAYS="7_DAYS"


class CustomerCreditHistoryEnums(str,Enum):
    SALES="SALES"
    UPDATED="UPDATED"