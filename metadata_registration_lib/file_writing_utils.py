import csv
import os
import zipfile
from io import BytesIO

import xlsxwriter
import xlwt


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


def write_dict_list_wrapper(data, file_name, output_dir, format="xlsx"):
    headers = list(data[0].keys())

    file_path = os.path.join(output_dir.name, file_name)
    f = open(file_path, "w")
    if format == "xlsx":
        write_dict_list_xlsx(f, data, headers)
    elif format == "xls":
        write_dict_list_xls(f, data, headers)
    else:
        raise Exception(f"Format '{format}'' not implemented")
    f.close()


def write_dict_list_xlsx(file, data, headers):
    """
    Write XLSX files

    Args:
        file (file): Open file stream
        data (list): Data to write as list of mappings
        headers (list): list of strings (headers)
    """
    wb = xlsxwriter.Workbook(file.name)
    ws = wb.add_worksheet()

    # Formats
    f_header = wb.add_format({"bold": True})

    # Write headers
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, f_header)

    # Write data
    for row_num, data_dict in enumerate(data, 1):

        for col_num, header in enumerate(headers):
            ws.write(row_num, col_num, data_dict.get(header, ""))

    # Resize columns
    for num_col, header in enumerate(headers):
        width = len(header) * 0.95 if len(header) > 10 else len(header)
        ws.set_column(num_col, num_col, width + 3)

    wb.close()


def write_dict_list_xls(file, data, headers):
    """
    Write XLS (old) files

    Args:
        file (file): Open file stream
        data (list): Data to write as list of mappings
        headers (list): list of strings (headers)
    """
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sheet 1")

    # Formats
    f_header = xlwt.easyxf("font: bold True;")

    # Write headers
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, f_header)

    # Write data
    for row_num, data_dict in enumerate(data, 1):

        for col_num, header in enumerate(headers):
            ws.write(row_num, col_num, data_dict.get(header, ""))

    # Resize columns
    for num_col, header in enumerate(headers):
        width = len(header) * 0.95 if len(header) > 10 else len(header)
        ws.col(num_col).width = int((width + 3) * 400)

    wb.save(file.name)


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
