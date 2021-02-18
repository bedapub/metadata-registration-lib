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