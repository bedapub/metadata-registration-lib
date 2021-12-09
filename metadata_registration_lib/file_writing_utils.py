import csv
import os
import zipfile
from io import BytesIO

import xlsxwriter


def write_file_from_denorm_data_2(f, data, file_format):
    """
    Write a file from the denorm_data_2 format (see fata_utils.py)

    Args:
        f (file): Input file (open stream)
        data (dict): data in denorm_data_2 format
        file_format (str): format of the exported file (xlsx, tsv or csv)

    Raises:
        Exception: Unsupported file_format
    """
    if file_format == "xlsx":
        wb = xlsxwriter.Workbook(f.name)
        bold = wb.add_format({"bold": True})
        ws = wb.add_worksheet()

        col_num = 0
        for header, data_list in data.items():
            ws.write(0, col_num, str(header), bold)

            for row_num, value in enumerate(data_list):
                ws.write(row_num + 1, col_num, str(value))

            col_num += 1

        wb.close()

    elif file_format in ["tsv", "csv"]:
        delimiters = {"tsv": "\t", "csv": ","}
        writer = csv.writer(
            f,
            delimiter=delimiters[file_format],
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writerow(data.keys())
        for row in zip(*data.values()):
            writer.writerow(row)

    else:
        raise Exception(f"Format '{file_format}' not supported")


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
