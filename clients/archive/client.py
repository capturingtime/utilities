import os
from datetime import datetime

BANNER = """
 #####                                                       #######
#     #   ##   #####  ##### #    # #####  # #    #  ####        #    # #    # ######
#        #  #  #    #   #   #    # #    # # ##   # #    #       #    # ##  ## #
#       #    # #    #   #   #    # #    # # # #  # #            #    # # ## # #####
#       ###### #####    #   #    # #####  # #  # # #  ###       #    # #    # #
#     # #    # #        #   #    # #   #  # #   ## #    #       #    # #    # #
 #####  #    # #        #    ####  #    # # #    #  ####        #    # #    # ######

######
#     # #    #  ####  #####  ####   ####  #####    ##   #####  #    # #   #
#     # #    # #    #   #   #    # #    # #    #  #  #  #    # #    #  # #
######  ###### #    #   #   #    # #      #    # #    # #    # ######   #
#       #    # #    #   #   #    # #  ### #####  ###### #####  #    #   #
#       #    # #    #   #   #    # #    # #   #  #    # #      #    #   #
#       #    #  ####    #    ####   ####  #    # #    # #      #    #   #
"""

VALID_DATEPARSE_FORMATS = [  # Attempted in top down order (Most specific -> Least)
    # https://strftime.org/
    "%Y%B%d",  # 2022September02
    "%Y%B%-d",  # 2022September2
    "%Y%b%d",  # 2022Sep02
    "%Y%b%-d",  # 2022Sep2
    "%y%B%d",  # 22September02
    "%y%B%-d",  # 22September2
    "%y%b%d",  # 22Sep02
    "%y%B%-d",  # 22Sep2
    "%Y%m%d",  # 20220902
    "%Y%m%-d",  # 2022092
    "%Y%-m%d",  # 2022902
    "%Y%-m%-d",  # 202292
    "%y%-m%-d",  # 2292
    "%x",  # 09/02/22 ~ 9/2/22
]
DEFAULT_OUTPUT_DATEPARSE_FMT = "%Y%b%d"  # YYYYSepDD (2022Sep15)

input_data = dict(
    {
        "shoot_date": datetime.now(),
        "session_path": str(),
        "customer_id": str(),
        "customer_name": str(),
        "session_name": str(),
        "archive_location": DEFAULT_ARCHIVE_ROOT,
    }
)


def get_term_len(print_line: bool = False, line_character: str = "-"):
    """ """
    term_len = os.get_terminal_size().columns
    if print_line:
        print(line_character * term_len)

    return term_len


def _verify_strptime_format(input_date_str: str = str()):
    """ """
    if not input_date_str:
        raise ValueError(
            f"input_date_str is a required param, recieved: '{input_date_str}'"
        )

    result = None
    for fmt in VALID_DATEPARSE_FORMATS:
        try:
            result = datetime.strptime(input_date_str, fmt)
        except (AttributeError, ValueError):
            continue

    return result


def capture_input(
    *args, msg: str = str(), default_value: str = str(), _type=str, **kwargs
):
    """ """
    if not msg:
        return None

    user_input = None

    # if default_value:
    #     msg = f"\n{msg}\n[default: {default_value}]"
    # else:
    #     msg = f"\n{msg}:"
    msg = f"{msg}:\n"
    # While loop ensures we always have something inputted
    while not user_input:
        if default_value:
            print(f"\n[default: {default_value}]")
        else:
            print("\n")
        user_raw_input = input(msg)

        if not user_raw_input:
            if default_value:
                user_raw_input = default_value
            else:
                print("Please supply a value")
                continue

        try:
            user_input = _type(user_raw_input, *args, **kwargs)

        except Exception:
            # TODO: Add logging and exception as err to capture
            print(
                f"The value you entered ({user_raw_input}) couldn't be parsed correctly. "
                "Please check your input and try again"
            )
            continue

    # String cleanup
    if isinstance(user_input, str):
        # A drag/drop folders into terminals will sometimes express as "/path/to/folder"
        # If captured as a string, this will be '"/path/to/folder"',
        # and the double quotes need to be stripped
        user_input = user_input.strip('"')

        # An escaped space needs to be replaced with a literal space
        user_input = user_input.replace("\\ ", " ")

    return user_input


def capture_date_input(**kwargs):
    """ """
    valid_input = False
    while not valid_input:
        user_input = capture_input(**kwargs)

        result = _verify_strptime_format(user_input)

        if not result:
            print(
                f"The value you entered ({user_input}) couldn't be parsed correctly. "
                "Please check your input and try again"
            )
            continue
        else:
            valid_input = True

    return result
