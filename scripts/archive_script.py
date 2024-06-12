#!/usr/bin/env python3

"""
    Author:         Ian Price <ian@capturingtimephoto.net>
    Support:        CTP IT Team
    Description:    Handles initial creation process of photo archives
    Security:       No Current Security considerations need to be made
    Usage:          Execute the script, Follow the script prompts
"""
# https://stackoverflow.com/questions/61025973/how-to-avoid-arrow-key-values-in-python-input  # noqa: E501, F401
import os
import rawpy  # https://pypi.org/project/rawpy/
import imageio
import py7zr
import shutil

from datetime import datetime
from progressbar import Bar
from tqdm import tqdm
from helpers import extract_jpeg

"""
python3 -m pip install imageio==2.25.1 progressbar==2.5 py7zr==0.20.4 tqdm==4.64.1 rawpy==0.18.0
"""

DEFAULT_OUTPUT_DATEPARSE_FMT = "%Y%b%d"  # YYYYSepDD (2022Sep15)
DEFAULT_ARCHIVE_ROOT = "/Volumes/capturingtimephoto/Photos/Archives"
DEFAULT_ARCHIVE_PREVIEW_ROOT = "/Volumes/capturingtimephoto/Photos/Archives/Previews"
DEFAULT_TEMP_DIR = "/tmp"
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
DEFAULT_ARCHIVE_FORMAT = ".7z"
VALID_ARCHIVERS = ["7za"]

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
# input_data = dict(
#     {
#         "shoot_date": datetime.now(),
#         "session_path": str(
#             "/Users/capturingtimephotograpyllc/SynologyDrive/Photos/Private\\ Sessions/Windermere_0014/0014_2022Aug14_BonhamHouse/D/"
#         ),
#         "customer_id": "0014",
#         "customer_name": "Windermere",
#         "session_name": "BonhamHouse",
#         "archive_location": "/Volumes/capturingtimephoto/Photos/Archives",
#     }
# )


def file_copy(src, dst):
    # https://gist.github.com/gargolito/073dead3ed3daac2f93dcdc5d4274f18
    fsize = int(os.path.getsize(src))
    with open(src, "rb") as f:
        with open(dst, "ab") as n:
            with tqdm(
                ncols=60,
                total=fsize,
                bar_format="{l_bar}{bar} | Remaining: {remaining}",
            ) as pbar:
                buffer = bytearray()
                while True:
                    buf = f.read(8192)
                    n.write(buf)
                    if len(buf) == 0:
                        break
                    buffer += buf
                    pbar.update(len(buf))


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


def get_inputs(output_datep_fmt: str = DEFAULT_OUTPUT_DATEPARSE_FMT):
    """
    A Function that handles the display and capture of inputs
    """
    inputs_confirmed = False
    while not inputs_confirmed:
        # Date of Shoot
        msg = "What was the Date of this shoot?"

        default_value = None
        try:
            # Check if the current value can use the provided parse format
            default_value = input_data["shoot_date"].strftime(output_datep_fmt)
        except AttributeError:
            # Unable to parse Date string using provided format, overriding
            # TODO: Log the override
            print(f"DEBUG: The Shoot Date wasn't parseable with {output_datep_fmt}")
            output_datep_fmt = DEFAULT_OUTPUT_DATEPARSE_FMT
            default_value = input_data["shoot_date"].strftime(output_datep_fmt)
        finally:
            input_data["shoot_date"] = capture_date_input(
                msg=msg, default_value=default_value
            )

        # Source Location of RAW files
        msg = "What is the Source Location (abs) of the RAW files to be archived for this shoot?"
        input_data["session_path"] = capture_input(
            msg=msg, default_value=input_data["session_path"]
        )

        # Customer ID Number (4 digit, 0 padded)
        msg = "What is the Customer ID Number for this shoot?"
        input_data["customer_id"] = capture_input(
            msg=msg, default_value=input_data["customer_id"]
        )
        input_data["customer_id"] = input_data["customer_id"].zfill(4)

        # Customer Name
        msg = "What is the Customer Name for this shoot?"
        input_data["customer_name"] = capture_input(
            msg=msg, default_value=input_data["customer_name"]
        )
        input_data["customer_name"] = input_data["customer_name"].replace(" ", "-")

        # Session Name
        msg = "What is the Session Name for this shoot?"
        input_data["session_name"] = capture_input(
            msg=msg, default_value=input_data["session_name"]
        )
        input_data["session_name"] = input_data["session_name"].replace(" ", "-")

        # Final Archive destination
        msg = "Where should the archive be uploaded?"
        # input_data["session_name"] = capture_input(
        #     msg=msg, default_value=input_data["session_name"]
        # )
        # For now, statically set
        input_data["archive_location"] = DEFAULT_ARCHIVE_ROOT

        # Variables for printing
        # parse_additional_inputs()
        shoot_date_str = input_data["shoot_date"].strftime(output_datep_fmt)
        folder_name = "_".join([input_data["customer_id"], input_data["customer_name"]])
        session_archive_name = "_".join(
            [input_data["customer_id"], shoot_date_str, input_data["session_name"]]
        )
        archive_location = f"{input_data['archive_location']}/{folder_name}/"

        print("\n" * 2)
        get_term_len(print_line=True)  # Line Break
        print(f"Date of Shoot:\n\t{shoot_date_str}")
        print(f"Session RAW Files Location:\n\t{input_data['session_path']}")
        print(f"Customer ID Number:\n\t{input_data['customer_id']}")
        print(f"Customer Name:\n\t{input_data['customer_name']}")
        print(f"Session Name:\n\t{input_data['session_name']}")
        get_term_len(print_line=True)  # Line Break
        print(f"Customer folder name:\n\t{folder_name}")
        print(f"Archive Location:\n\t{archive_location}")
        print(
            f"Session archive name:\n\t{session_archive_name}{DEFAULT_ARCHIVE_FORMAT}"
        )
        get_term_len(print_line=True)  # Line Break
        print("\n" * 2)
        confirm = input("Does the above data look correct?: [Default: No]\n")

        if not confirm:
            confirm = "No"

        yes_values = ["y", "Y", "yes", "Yes", "YES"]
        if confirm in yes_values:
            inputs_confirmed = True
        else:
            continue

    return input_data


if __name__ == "__main__":
    print(f"\n{BANNER}")
    print("This application will help you create an archive for your recent shoot")
    print("Any default presented can be accepted by simply pressing enter\n")
    inputs = get_inputs()

    # parse_additional_inputs()
    session_path = inputs["session_path"].rstrip("/")
    folder_name = "_".join([inputs["customer_id"], inputs["customer_name"]])
    shoot_date_str = inputs["shoot_date"].strftime(DEFAULT_OUTPUT_DATEPARSE_FMT)
    session_archive_name = "_".join(
        [inputs["customer_id"], shoot_date_str, inputs["session_name"]]
    )

    final_archive_path = f"{inputs['archive_location']}/{folder_name}"
    archive_full_name = f"{session_archive_name}{DEFAULT_ARCHIVE_FORMAT}"
    temp_archive_loc = f"/tmp/{archive_full_name}"

    file_list = os.listdir(session_path)
    for f in file_list:
        p_dst = f"{DEFAULT_ARCHIVE_PREVIEW_ROOT}/{session_archive_name}"
        extract_jpeg(f, p_dst)

    # with py7zr.SevenZipFile(temp_archive_loc, "a") as archive:
    #     for file in file_list:
    #         file_abs_path = f"{session_path}/{file}"
    #         archive.write(file_abs_path)
    with py7zr.SevenZipFile(temp_archive_loc, "w") as archive:
        # archive.writeall(session_path, str())
        c = len(file_list)
        with Bar(
            "Archiving Files:",
            suffix="%(index)d/%(max)d ETA: %(eta)ds (Elapsed: %(elapsed)ds)",
            max=c,
        ) as bar:
            for file in file_list:
                file_abs_path = f"{session_path}/{file}"
                archive.write(
                    file_abs_path, file
                )  # 2nd arg = how much of path to include in archive
                bar.next()

    print(f"\nCopying {archive_full_name} to {final_archive_path}")
    src = temp_archive_loc
    dst = f"{final_archive_path}/{archive_full_name}"
    file_copy(src, dst)

    print("\nAll operations complete")
    print(f"Archive successfully created at:\n{dst}\n")
