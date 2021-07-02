from collections import OrderedDict


def get_all_data_from_wba_plate_rows(rows):
    """
    *** WBA 96 well plates ***
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
                for col_num in range(1, 13):
                    cell_content = row[col_num]
                    well_id = f"{row[0]}{col_num}"

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
                                    "Well ID": well_id,
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
                                "Column": col_num,
                                "Name": treatment_id,
                                "Dilution": "",
                            }
                        )
                    )

            # Re-initialize these to make sure we see if these are not found for a certain plate
            plate_id = "NOT FOUND"
            individual_id = "NOT FOUND"

    return data


def get_all_data_from_qpcr_plate_rows(rows):
    """
    *** qPCR 384 well plates ***
    Get flat data from a list of rows from a plate design file (rectangular layout)
    Parameter
        - rows (list of list): list of rows from a plate design file (rectangular layout)
    Returns
        - data (dict of list of OrderedDict): flat data for different kind of outputs
    """
    data = {
        "samples": [],
        "readouts": [],
        "quantstudio_plates": OrderedDict(),
    }

    plate_id = "NOT FOUND"
    plate_num = 0
    sample_num = 0
    readout_num = 0
    plate_well_num = 0

    # No need to reset samples for each plate
    sample_name_to_id = {}

    rows_iter = iter(rows)
    for row in rows_iter:
        if row[0].lower().strip() == "qpcr plate layout":
            plate_num += 1
            plate_id = str(plate_num)
            col_num_to_target_name = {}

        if row[0].lower().strip() == "target name":
            for col_num in range(1, 25):
                col_num_to_target_name[col_num] = row[col_num]

        # Plate start
        elif "161718192021222324" in "".join(row) or "9101112131415" in "".join(row):

            for _ in range(0, 16):
                row = next(rows_iter)
                for col_num in range(1, 25):
                    plate_well_num += 1
                    cell_content = row[col_num]
                    well_id = f"{row[0]}{col_num}"
                    target_name = col_num_to_target_name[col_num]

                    if not cell_content in [None, "None", ""]:
                        sample_name = cell_content

                        # Samples data
                        if not sample_name in sample_name_to_id:
                            sample_num += 1
                            sample_id = sample_name
                            sample_name_to_id[sample_name] = sample_id
                            data["samples"].append(
                                OrderedDict(
                                    {
                                        "Sample ID (SAM)": sample_id,
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
                                    "Well ID": well_id,
                                }
                            )
                        )

                    else:
                        sample_name = ""
                        sample_name_to_id[sample_name] = ""

                    # QuantStudio template data
                    if not plate_id in data["quantstudio_plates"]:
                        data["quantstudio_plates"][plate_id] = {
                            "plate_id": plate_id,
                            "data": [],
                        }

                    data["quantstudio_plates"][plate_id]["data"].append(
                        OrderedDict(
                            {
                                "": plate_well_num,
                                "Well": well_id,
                                "Sample Name": sample_name if sample_name else "",
                                "Sample Color": "",
                                "Biogroup Name": "",
                                "Biogroup Color": "",
                                "Target Name": target_name if sample_name else "",
                                "Target Color": "",
                                "Task": "",
                                "Reporter": "",
                                "Quencher": "",
                                "Quantity": "",
                                "Comments": "",
                            }
                        )
                    )

            # Re-initialize these to make sure we see if these are not found for a certain plate
            plate_id = "NOT FOUND"

    return data
