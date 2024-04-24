from utils.custom_logger import configure_logging
import logging
configure_logging()
logger = logging.getLogger(__name__)

def schools(schools):
    """
    Takes the sorted tsv data as param and checks if any data has been repeated.
    Throws critical error if found and terminates program.
    """
    seen_schools = set()
    seen_school_codes = set()
    duplicate_schools = list()  # using list because there might be multiple entries of the same school, duplicated. also, 2d list to view the scode and school name in logs (console)

    for school in schools:
        if len(school) > 0:
            school_scode = school["scode"].strip()
            school_name = school["name-address"].strip()

            # negating empty cells. could definitely be made stricter if needed for aggressive verification.
            if school_scode and school_name:
                # check for school names
                if school_scode in seen_school_codes or school_name in seen_schools:
                    duplicate_schools.append({"scode":school_scode,"name":school_name}) # dictionary used so that the code below has better readability
                else:
                    seen_schools.add(school_name)
                    
    if duplicate_schools:
        #DEBUG002 Else block to be uncommented if Info level logs stating no duplicates are found is required.
        logger.critical("Duplicate School Name or Code Found")
        for school in duplicate_schools:
            logger.warning("Duplicate School Code: "+school["scode"]+"\t | Name: "+school["name"])
        logger.info("Terminating further execution. Please fix issue in data first. Thank you.")
        exit()
    # else:
    #     logger.info("No duplicate school names found.")
        
def centers(centers):
    """
    Takes the sorted tsv data as param and checks if any data has been repeated.
    Throws critical error if found and terminates program. Works similar to
    schools function of this very file.
    """
    seen_centers = set()
    seen_center_codes = set()
    duplicate_centers = list()  # using list because there might be multiple entries of the same center, duplicated. also, 2d list to view the scode and center name in logs (console)

    for center in centers:
        if len(center) > 0:
            center_cscode = center["cscode"].strip()
            center_name = center["name"].strip()

            # negating empty cells. could definitely be made stricter if needed for aggressive verification.
            if center_cscode and center_name:
                # check for center names
                if center_cscode in seen_center_codes or center_name in seen_centers:
                    duplicate_centers.append({"cscode":center_cscode,"name":center_name}) # dictionary used so that the code below has better readability
                else:
                    seen_centers.add(center_name)
                    
    if duplicate_centers:
        #DEBUG002 Else block to be uncommented if Info level logs stating no duplicates are found is required.
        logger.critical("Duplicate center Name or Code Found")
        for center in duplicate_centers:
            logger.warning("Duplicate center Code: "+center["cscode"]+"\t | Name: "+center["name"])
        logger.info("Terminating further execution. Please fix issue in data first. Thank you.")
        exit()
    # else:
    #     logger.info("No duplicate center names found.")