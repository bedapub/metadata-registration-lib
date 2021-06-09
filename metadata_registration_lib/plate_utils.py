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

    plate_id = "NOT FOUND"
    individual_id = "NOT FOUND"
    sample_num = 0
    readout_num = 0

    rows_iter = iter(rows)
    for row in rows_iter:
        if row[0].lower().strip() == "plate":
            plate_id = row[1]

        elif row[0].lower().strip() == "donor":
            individual_id = row[1]

        elif "123456789101112" in "".join(row):
            # Reset sample IDs for each plate as they are different samples
            sample_name_to_id = {}

            for _ in range(0, 8):
                row = next(rows_iter)
                for j in range(1, 13):
                    sample_name = row[j]

                    if not sample_name in [None, "None", ""]:

                        # Samples data
                        if not sample_name in sample_name_to_id:
                            sample_num += 1
                            sample_id = f"S{sample_num} - {sample_name}"
                            sample_name_to_id[sample_name] = sample_id
                            data["samples"].append(
                                OrderedDict(
                                    {
                                        "Sample ID (SAM)": sample_id,
                                        "Individual ID (IND)": individual_id,
                                        "Treatment ID (TRE > SAM)": sample_name,
                                    }
                                )
                            )

                        # Readouts data
                        readout_num += 1
                        data["readouts"].append(
                            OrderedDict(
                                {
                                    "Readout ID": f"Readout {readout_num}",
                                    "Sample ID": sample_name_to_id[sample_name],
                                    "Plate ID": plate_id,
                                    "Well ID": f"{row[0]}{j}",
                                }
                            )
                        )

                    else:
                        sample_name = ""
                        sample_name_to_id[sample_name] = ""

                    # Quanterix template data
                    if not plate_id in data["quanterix_plates"]:
                        data["quanterix_plates"][plate_id] = {
                            "plate_id": plate_id,
                            "donor": individual_id,
                            "data": [],
                        }

                    data["quanterix_plates"][plate_id]["data"].append(
                        OrderedDict(
                            {
                                "Row": row[0],
                                "Column": j,
                                "Name": sample_name,
                                "Dilution": "",
                            }
                        )
                    )

            # Re-initialize these to make sure we see if these are not found for a certain plate
            plate_id = "NOT FOUND"
            individual_id = "NOT FOUND"

    return data
