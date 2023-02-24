import rawpy  # https://pypi.org/project/rawpy/
import imageio
import os
import py7zr
from tqdm import tqdm
from progressbar import Bar
import shutil

# DEFAULT_ARCHIVE_ROOT = "/Volumes/capturingtimephoto/Photos/Archives"
# DEFAULT_ARCHIVE_PREVIEW_ROOT = "/Volumes/capturingtimephoto/Photos/Archives/Previews"
DEFAULT_ARCHIVE_ROOT = "/mnt/d/archives"
DEFAULT_ARCHIVE_PREVIEW_ROOT = "/mnt/d/archives/Previews"
DEFAULT_TEMP_DIR = "/tmp"


def parse_path(path) -> dict:
    """parse path and file details from the provide file"""
    abs_path = os.path.abspath(path)
    path_part = os.path.dirname(abs_path)
    name_part = str(".").join(os.path.basename(abs_path).split(".")[0:-1])
    ext_part = os.path.basename(abs_path).split(".")[-1]
    return {
        "abs_path": abs_path,
        "file_name": f"{name_part}.{ext_part}",
        "path_part": path_part,
        "ext_part": ext_part,
        "name_part": name_part,
    }


def extract_tiff(file):
    """Extract and save as .tiff"""
    path = file
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess()
    imageio.imsave(f"{path}.tiff", rgb)


def extract_jpeg(file, dst: str = None):
    """Makes a copy of the embedded jpeg in the same dir (non-destructive)"""
    file_details = parse_path(file)
    abs_path = file_details["abs_path"]
    name_part = file_details["name_part"]
    path_part = file_details["path_part"]
    if not dst:
        dst = path_part
    jpeg_path = f"{dst}/{name_part}.jpeg"
    with rawpy.imread(abs_path) as raw:
        # raises rawpy.LibRawNoThumbnailError if thumbnail missing
        # raises rawpy.LibRawUnsupportedThumbnailError if unsupported format
        thumb = raw.extract_thumb()
    if thumb.format == rawpy.ThumbFormat.JPEG:
        # thumb.data is already in JPEG format, save as-is
        with open(jpeg_path, "wb") as f:
            f.write(thumb.data)
    elif thumb.format == rawpy.ThumbFormat.BITMAP:
        # thumb.data is an RGB numpy array, convert with imageio
        imageio.imsave(jpeg_path, thumb.data)


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


def dir_move(src, dst):
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    shutil.move(src, dst)


def extract_archive(archive_path):
    """extracts archive to same directory"""
    file_details = parse_path(archive_path)
    with py7zr.SevenZipFile(file_details["abs_path"], "r") as archive:
        dst = f"{file_details['path_part']}/{file_details['name_part']}"
        archive.extractall(path=f"{dst}/")
    return dst


def gen_preview_from_archive(archive_path, output_location):
    """Retrieves an archive and extracts all previews to
    Archives/Previews/{Archive_Name}/{Image_Name}
    """
    file_details = parse_path(archive_path)
    src = file_details["abs_path"]
    # dst = f"{DEFAULT_TEMP_DIR}/{file_details['file_name']}"
    # file_copy(src, dst)
    extracted_dir = extract_archive(src)
    file_list = os.listdir(extracted_dir)
    for f in file_list:
        f = f"{extracted_dir}/{f}"
        extract_jpeg(f)
        os.remove(f)

    preview_dst = f"{output_location}/{file_details['name_part']}"
    p_src, p_dst = dir_move(extracted_dir, preview_dst)
    return p_dst
