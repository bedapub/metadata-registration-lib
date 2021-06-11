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
            tre_id_to_sam_id = {}

            for _ in range(0, 8):
                row = next(rows_iter)
                for j in range(1, 13):
                    cell_content = row[j]

                    if not cell_content in [None, "None", ""]:
                        cell_split = [str(c).strip() for c in cell_content.split("//")]
                        comp_name = cell_split[0]
                        conc = cell_split[1] if len(cell_split) > 1 else ""
                        conc_unit = cell_split[2] if len(cell_split) > 2 else ""
                        treatment_id = " ".join(cell_split)

                        # Samples data
                        if not treatment_id in tre_id_to_sam_id:
                            sample_num += 1
                            sample_id = f"S{sample_num} - {treatment_id}"
                            tre_id_to_sam_id[treatment_id] = sample_id
                            data["samples"].append(
                                OrderedDict(
                                    {
                                        "Sample ID (SAM)": sample_id,
                                        "Individual ID (IND)": individual_id,
                                        "Compound name (TRE > SAM)": comp_name,
                                        "Concentration (TRE > SAM)": conc,
                                        "Concentration Unit (TRE > SAM)": conc_unit,
                                        "Treatment ID (TRE > SAM)": treatment_id,
                                    }
                                )
                            )

                        # Readouts data
                        readout_num += 1
                        data["readouts"].append(
                            OrderedDict(
                                {
                                    "Readout ID": f"Readout {readout_num}",
                                    "Sample ID": tre_id_to_sam_id[treatment_id],
                                    "Plate ID": plate_id,
                                    "Well ID": f"{row[0]}{j}",
                                }
                            )
                        )

                    else:
                        treatment_id = ""
                        tre_id_to_sam_id[treatment_id] = ""

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
                                "Name": treatment_id,
                                "Dilution": "",
                            }
                        )
                    )

            # Re-initialize these to make sure we see if these are not found for a certain plate
            plate_id = "NOT FOUND"
            individual_id = "NOT FOUND"

    return data
