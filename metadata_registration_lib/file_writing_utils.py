import csv
import os
import zipfile
from io import BytesIO

import xlsxwriter


def get_memory_zip(output_dir, file_names_to_zip):
    """
    Creates a ZIP file in memory with the given files in output_dir

    Args:
        output_dir (tempfile.TemporaryDirectory): Output directory
        file_names_to_zip (iterable): Relative file names to zip inside output_dir

    Returns:
        BytesIO: ZIPed file in memory
    """
    memory_zip_file = BytesIO()
    with zipfile.ZipFile(memory_zip_file, "w") as zf:
        for file_name in file_names_to_zip:
            os.chdir(output_dir.name)
            zf.write(file_name, compress_type=zipfile.ZIP_DEFLATED)
    memory_zip_file.seek(0)
    return memory_zip_file
