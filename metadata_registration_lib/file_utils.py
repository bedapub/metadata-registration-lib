import csv
import datetime
import os
import re
import zipfile
from io import BytesIO

import openpyxl
import xlrd
import xlsxwriter
import xlwt


def write_file_from_denorm_data_2(f, data, file_format):
    """
    Write a file from the denorm_data_2 format (see fata_utils.py)
    Parameters
    - f = open file streat
    - data = data in denorm_data_2 format
    - file_format = format of the exported file (xlsx, tsv or csv)
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


#################################################
######## Read files as records
#################################################
def get_records_and_headers_from_csv(input_file, delimiter=","):
    """
    Returns a list of headers and a list of records {header:value}
    Columns with empty headers are ignored
    """
    lines = [l.decode("utf-8") for l in input_file.readlines()]

    # Read headers
    headers = next(csv.reader(lines, delimiter=delimiter))

    # Remove empty headers
    headers = [h for h in headers if h]

    # Read records
    reader = csv.DictReader(lines, delimiter=delimiter)

    records = []
    for record in reader:

        for rec_header in record.keys():
            # Remove values from columns with empty headers
            if not rec_header:
                record.pop(rec_header)
        records.append(record)

    return headers, records


def get_records_and_headers_from_excel(input_file):
    """
    Returns a list of headers and a list of records {header:value}
    Only the first sheet is read
    Columns with empty headers are ignored
    """
    workbook = openpyxl.load_workbook(
        filename=input_file, read_only=True, data_only=True
    )
    sheet = workbook.worksheets[0]

    # Read headers
    first_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
    headers = list(first_row)

    # Read records
    records = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        record = {}

        for col in range(len(headers)):
            # Ignore values from empty headers
            if headers[col]:
                raw_value = row[col]

                if type(raw_value) == datetime.datetime:
                    value = raw_value.isoformat()
                elif raw_value is None:
                    value = ""
                else:
                    value = str(raw_value)

                record[headers[col]] = value

        records.append(record)

    # Remove empty headers
    headers = [h for h in headers if h]

    workbook.close()

    return headers, records


#################################################
######## Read files as list of rows
#################################################
def get_rows_from_file(
    input_file,
    sheet_number=None,
    sheet_name=None,
    convert_to_str=True,
    unmerge_cells=True,
):
    """Extract records from file as a list of dicts"""
    try:
        workbook = openpyxl.load_workbook(
            filename=input_file, read_only=False, data_only=True
        )
        mode = "xlsx"
    except:
        input_file.seek(0, 0)
        workbook = xlrd.open_workbook(file_contents=input_file.read())
        mode = "xls"

    if sheet_number is not None:
        sheet = find_sheet_by_number(workbook, sheet_number, mode)
    elif sheet_name is not None:
        sheet = find_sheet_by_name(workbook, sheet_name, mode)
    else:
        sheet = find_sheet_by_number(workbook, 0, mode)

    # Handle merged cells
    if unmerge_cells:
        sheet = unmerge_cells_in_sheet(sheet, mode)

    # Read actual sample data
    rows = []
    for row in gen_rows_as_list(sheet, start_row=0, mode=mode):
        if convert_to_str:
            row = [str(v) for v in row]
        rows.append(row)

    if mode == "xlsx":
        workbook.close()

    return rows


def unmerge_cells_in_sheet(sheet, mode):
    """Un-merge cells and copy the same value to all sub-cells"""
    if mode == "xlsx":
        merged_cell_groups = [g for g in sheet.merged_cells.ranges]
        for cell_group in merged_cell_groups:
            min_col, min_row, max_col, max_row = openpyxl.utils.range_boundaries(
                str(cell_group)
            )
            top_left_cell_value = sheet.cell(row=min_row, column=min_col).value
            # print(cell_group, top_left_cell_value)
            sheet.unmerge_cells(str(cell_group))
            for row in sheet.iter_rows(
                min_col=min_col, min_row=min_row, max_col=max_col, max_row=max_row
            ):
                for cell in row:
                    cell.value = top_left_cell_value
    if mode == "xls":
        # TODO: Implement unmerge for xls
        raise NotImplementedError(
            "unmerge_cells_in_sheet not implemented for mode = 'xls'"
        )

    return sheet


def find_sheet_by_number(workbook, number, mode="xlsx"):
    """Find sheet in workbook by number"""
    try:
        if mode == "xlsx":
            sheet = workbook.worksheets[number]
        elif mode == "xls":
            sheet = workbook.sheet_by_index(number)
    except:
        raise Exception(f"Sheet number {number} not found")

    return sheet


def find_sheet_by_name(workbook, name, mode="xlsx", exact_match=False):
    """Find sheet in workbook by name"""
    name_an = re.sub(r"[\W_]+", "", name).lower()

    try:
        for sheet_name in get_sheet_names(workbook, mode):
            sheet_name_an = re.sub(r"[\W_]+", "", sheet_name).lower()

            if exact_match and name_an == sheet_name_an:
                return get_sheet_by_name(workbook, sheet_name, mode)
            elif not exact_match and name_an in sheet_name_an:
                return get_sheet_by_name(workbook, sheet_name, mode)

        else:
            raise Exception(f"Sheet name '{name}' not found")

    except:
        raise Exception(f"Sheet name '{name}' not found")


def get_sheet_names(workbook, mode):
    if mode == "xlsx":
        return workbook.sheetnames
    elif mode == "xls":
        return workbook.sheet_names()


def get_sheet_by_name(workbook, sheet_name, mode):
    if mode == "xlsx":
        return workbook[sheet_name]
    elif mode == "xls":
        return workbook.sheet_by_name(sheet_name)


def gen_rows_as_list(sheet, start_row, mode="xlsx"):
    """Generator that yields rows as list"""
    if mode == "xlsx":
        for row in sheet.iter_rows(min_row=start_row, values_only=True):
            yield list(row)

    elif mode == "xls":
        for row_num in range(start_row - 1, sheet.nrows):
            yield sheet.row_values(row_num)


def remove_empty_rows(rows, empty_values=[None, "", "None"]):
    clean_rows = []
    for row in rows:
        if not all(v in [None, ""] for v in row):
            clean_rows.append(row)
    return clean_rows


#################################################
######## Write files
#################################################
def write_dict_list_xlsx(file, data, headers):
    """
    Write XLSX files
    Parameters
        - file: open file stream
        - data: list of mappings
        - headers: list of strings (headers)
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
    Parameters
        - file: open file stream
        - data: list of mappings
        - headers: list of strings (headers)
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
    Parameters
        - output_dir = tempfile.TemporaryDirectory instance
        - file_names_to_zip = files to zip, names present at the root of output_dir
    Output
        - memory_zip_file = BytesIO() instance
    """
    memory_zip_file = BytesIO()
    with zipfile.ZipFile(memory_zip_file, "w") as zf:
        for file_name in file_names_to_zip:
            os.chdir(output_dir.name)
            zf.write(file_name, compress_type=zipfile.ZIP_DEFLATED)
    memory_zip_file.seek(0)
    return memory_zip_file
