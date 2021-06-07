from collections import OrderedDict


def get_data_from_plate_rows(rows):
    """
    Get flat readouts data from a list of rows from a plate design file (rectangular layout)
    Parameter
        - rows (list of list): list of rows from a plate design file (rectangular layout)
    Returns
        - data (list of OrderedDict): flat readouts data
    """
    data = []

    plate_id = None
    readout_num = 0

    rows_iter = iter(rows)
    for row in rows_iter:
        if row[0].startswith("Plate") and not "Plate layout" in row[0]:
            try:
                plate_id = row[0].split(":")[0]
            except:
                pass

        elif "123456789101112" in "".join(row):

            for _ in range(0, 8):
                row = next(rows_iter)
                for j in range(1, 13):
                    sample_id = row[j]

                    if sample_id in [None, "None", ""]:
                        continue

                    readout_num += 1
                    data.append(
                        OrderedDict(
                            {
                                "Readout ID": f"Readout {readout_num}",
                                "Sample ID": row[j],
                                "Plate ID": plate_id,
                                "Well ID": f"{row[0]}{j}",
                            }
                        )
                    )

    return data
