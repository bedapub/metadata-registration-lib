import csv
import xlsxwriter


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

