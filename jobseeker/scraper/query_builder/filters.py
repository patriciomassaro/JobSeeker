from enum import Enum

class FilterEnum(Enum):
    # This method can now be used by any Enum inheriting from ParamEnum
    @classmethod
    def get_param(cls,value, param_name):
        for item in cls:
            if item.value == value:
                return f"{param_name}{item.value}" if item.value is not None else ""
        return ""


class FilterTime(FilterEnum):
    ANY_TIME = None
    PAST_24_HOURS = 86400
    PAST_WEEK = 604800
    PAST_MONTH = 2592000
    
    
    # Specific implementation for TimeFilter
    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_TPR=r")

class FilterSalaryRange(FilterEnum):
    RANGE_ANY = None
    RANGE_40K_PLUS = 1
    RANGE_60K_PLUS = 2
    RANGE_80K_PLUS = 3
    RANGE_100K_PLUS = 4
    RANGE_120K_PLUS = 5
    RANGE_140K_PLUS = 6
    RANGE_160K_PLUS = 7
    RANGE_180K_PLUS = 8
    RANGE_200K_PLUS = 9
    

    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_SB2=")

class FilterExperienceLevel(FilterEnum):
    ANY_EXPERIENCE_LEVEL = None
    INTERNSHIP = 1
    ENTRY_LEVEL = 2
    ASSOCIATE = 3
    MID_SENIOR_LEVEL = 4
    DIRECTOR = 5
    EXECUTIVE = 6
    

    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_E=")

def build_company_search_url(company_id:int = None):
    return f"f_C={company_id}" if company_id is not None else ""

class FilterRemoteModality(FilterEnum):
    ANY_MODALITY = None
    ON_SITE = 1
    REMOTE = 2
    HYBRID =3
    

    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_WT=")