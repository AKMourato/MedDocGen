""" A collection of dictionaries needed for measurments JSONs.
"""

def measurement_collection_dict(value, timestamp):
    """
    """
    measurement_collectiondict = {
        "datetime_creation": None,
        "patient_id": None,
        "measurement_id": None,
        "value": value,
        "timestamp": timestamp,
    }
    return measurement_collectiondict


def measurement_type_dict(version, name, unit, is_categorical, is_time_dependent):
    """
    """
    measurement_typedict = {
        "datetime_creation": None,
        "version": version,
        "measurement_list_id": None,
        "measurement_category_id": None,
        "name": name,
        "unit": unit,
        "is_categorical": is_categorical,
        "is_time_dependent": is_time_dependent 
    }

    return measurement_typedict


def measurement_category_dict(version, name):
    """
    """
    measurment_categorydict = {
        "datetime_creation": None,
        "version": version,
        "name": name,        
        "parent_category_id": None
    }
    return measurment_categorydict


def meaurement_list_dict(short_name):
    """
    """
    measurement_listdict = {
        "short_name": short_name,
        "header": None,
        "contained_param": None,
        "detailed_info": None,
        "images": [],
        "pathologies": []
    }

    return measurement_listdict