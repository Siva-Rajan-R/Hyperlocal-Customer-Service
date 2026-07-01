from enum import Enum



class CustomerPaymentTermsEnums(str,Enum):
    SEVEN_DAYS="7_DAYS"

class CustomerOutstandingAddEnums(str,Enum):
    INCREMENT="INCREMENT"
    DECREMENT="DECREMENT"
    DIRECT="DIRECT"

class CustomerCreditHistoryEnums(str,Enum):
    SALES="SALES"
    UPDATED="UPDATED"

class CustomerOutstandingClearedPaymentMethods(str,Enum):
    UPI="UPI"
    CASH="CASH"
    CARD="CARD"
    BANK="BANK"
    RETURN="RETURN"

class PaymentMethodsEnums(str,Enum):
    UPI="UPI"
    CASH="CASH"
    CARD="CARD"
    BANK="BANK"

class StatsUpdateType(str, Enum):
    INCR = "incr"
    DECR = "decr"