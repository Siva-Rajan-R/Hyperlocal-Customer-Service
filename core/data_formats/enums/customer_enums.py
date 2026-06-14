from enum import Enum



class CustomerPaymentCycleEnums(str,Enum):
    SEVEN_DAYS="7_DAYS"


class CustomerCreditHistoryEnums(str,Enum):
    SALES="SALES"
    UPDATED="UPDATED"

class CustomerOutstandingClearedPaymentMethods(str,Enum):
    UPI="UPI"
    CASH="CASH"
    CARD="CARD"
    BANK="BANK"
    RETURN="RETURN"