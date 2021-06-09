from collections import OrderedDict


def get_all_data_from_wba_plate_rows(rows):
    """
    Get flat data from a list of rows from a plate design file (rectangular layout)
    Parameter
        - rows (list of list): list of rows from a plate design file (rectangular layout)
    Returns
        - data (dict of list of OrderedDict): flat data for different kind of outputs
    """
    data = {
        "samples": [],
        "readouts": [],
        "quanterix_plates": OrderedDict(),
    }

    existing_sample_ids = set()
    plate_id = "NOT FOUND"
    individual_id = "NOT FOUND"
    readout_num = 0

    rows_iter = iter(rows)
    for row in rows_iter:
        if row[0].lower().strip() == "plate":
            plate_id = row[1]
        elif row[0].lower().strip() == "donor":
            individual_id = row[1]

        elif "123456789101112" in "".join(row):

            for _ in range(0, 8):
                row = next(rows_iter)
                for j in range(1, 13):
                    sample_id = row[j]

                    # Readouts data
                    if not sample_id in [None, "None", ""]:
                        readout_num += 1
                        data["readouts"].append(
                            OrderedDict(
                                {
                                    "Readout ID": f"Readout {readout_num}",
                                    "Sample ID": sample_id,
                                    "Plate ID": plate_id,
                                    "Well ID": f"{row[0]}{j}",
                                }
                            )
                        )

                        # Samples data
                        if not sample_id in existing_sample_ids:
                            data["samples"].append(
                                OrderedDict(
                                    {
                                        "Sample ID (SAM)": sample_id,
                                        "Individual ID (IND)": individual_id,
                                        "Treatment ID (TRE > SAM)": sample_id,
                                    }
                                )
                            )
                            existing_sample_ids.add(sample_id)

                    # Quanterix template data
                    if not plate_id in data["quanterix_plates"]:
                        data["quanterix_plates"][plate_id] = {
                            "plate_id": plate_id,
                            "donor": individual_id,
                            "data": [],
                        }

                    if sample_id in [None, "None", ""]:
                        sample_id = ""

                    data["quanterix_plates"][plate_id]["data"].append(
                        OrderedDict(
                            {
                                "Row": row[0],
                                "Column": j,
                                "Name": sample_id,
                                "Dilution": "",
                            }
                        )
                    )

            # Re-initialize these to make sure we see if these are not found for a certain plate
            plate_id = "NOT FOUND"
            individual_id = "NOT FOUND"

    return data
