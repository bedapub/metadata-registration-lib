from collections import OrderedDict
import abc
import uuid
import json
import re
import copy

from metadata_registration_lib.other_utils import str_to_bool


###################################################
####### Entity classes
###################################################
class Entity:
    def __init__(self, uuid=None, data={}):
        self.uuid = uuid
        self.data = data


class Treatment(Entity):
    def __init__(self, id=None, *args, **kwargs):
        self.id = id
        super().__init__(*args, **kwargs)


class TreatableEntity(Entity):
    def __init__(self, treatment=None, *args, **kwargs):
        self.treatment = treatment
        super().__init__(*args, **kwargs)


class Individual(TreatableEntity):
    def __init__(self, id=None, *args, **kwargs):
        self.id = id
        super().__init__(*args, **kwargs)

    def get_default_form_format(self):
        return {
            "individual_id": "no_individual",
            "sex": "na",
            "organism": "not_applicable",
            "uuid": str(uuid.uuid1()),
        }


class Sample(TreatableEntity):
    def __init__(self, id=None, individual=None, *args, **kwargs):
        self.id = id
        self.individual = individual
        super().__init__(*args, **kwargs)


class Readout(Entity):
    def __init__(self, id=None, samples=[], *args, **kwargs):
        self.id = id
        self.samples = samples
        super().__init__(*args, **kwargs)


###################################################
####### Set classes
###################################################
class EntitySet:
    def __init__(
        self, prop_names=None, jexcel_data=[], id_to_form_format=OrderedDict()
    ):
        self.prop_names = prop_names
        self.jexcel_data = jexcel_data
        self.id_to_form_format = id_to_form_format

    def validate_against_form(self, form, form_name):
        """
        Performs validation of data (form format) against form
        id_to_form_format = {tmp_id: form_format_entity}
        Returns
            - validate_all (bool)
            - errors_html (list of HTML strings): one per entity that did not validate
        """
        validate_all = True
        errors_html = []
        for tmp_id, entity_dict in self.id_to_form_format.items():
            validate_entity = True
            field_error_list = []

            # Update entity format (ex: transform strings to booleans when needed)
            # Conversion the other way around to fill JExcel in build_xxx_session_from_form_format
            for field in form:
                if field.name in entity_dict:
                    if field.type == "BooleanField":
                        entity_dict[field.name] = str_to_bool(entity_dict[field.name])

            form.process(data=entity_dict)

            # Validate field by field
            for field in form:
                condition_1 = field.flags.required and not field.validate(form)
                condition_2 = field.name in entity_dict and not field.validate(form)

                if condition_1 or condition_2:
                    field_error_list.append(
                        f"Field '<b>{field.name}</b>' did not validate: {field.errors}"
                    )
                    validate_entity = False
                    validate_all = False

            if not validate_entity:
                message = f"<b>{tmp_id}</b> did not validate against form '{form_name}'<ul style='margin-bottom:0;'>"
                for field_error in field_error_list:
                    message += f"<li>{field_error}</li>"
                message += f"</ul>"
                errors_html.append(message)

        return validate_all, errors_html


class TreatmentSet(EntitySet):
    def __init__(self, treatments=[], *args, **kwargs):
        self.entity_class = Treatment
        self.treatments = treatments
        super().__init__(*args, **kwargs)


class IndividualSet(EntitySet):
    def __init__(self, individuals=[], *args, **kwargs):
        self.entity_class = Individual
        self.individuals = individuals
        super().__init__(*args, **kwargs)


class SampleSet(EntitySet):
    def __init__(self, samples=[], *args, **kwargs):
        self.entity_class = Sample
        self.samples = samples
        super().__init__(*args, **kwargs)


class ReadoutSet(EntitySet):
    def __init__(self, readouts=[], sample_set=None, *args, **kwargs):
        self.entity_class = Readout
        self.readouts = readouts
        self.sample_set = sample_set
        if self.sample_set is None:
            self.sample_set = SampleSet()

        super().__init__(*args, **kwargs)


###################################################
####### Step classes
###################################################
class Step(metaclass=abc.ABCMeta):
    def __init__(self, **kwargs):
        self.json_str_prop = "user_defined_json_data"
        self.previous_step = kwargs.get("previous_step")
        self.next_step = kwargs.get("next_step")
        self.id_to_uuid = kwargs.get("id_to_uuid", {})

        # Mainly to avoid linting errors
        self.name = getattr(self, "name", kwargs.get("name"))
        self.entity_set = getattr(self, "entity_set", kwargs.get("entity_set"))
        self.nested_steps = getattr(
            self, "nested_steps", kwargs.get("nested_steps", [])
        )
        self.prop_name_for_tmp_id = getattr(
            self, "prop_name_for_tmp_id", kwargs.get("prop_name_for_tmp_id")
        )
        self.prop_names_multiple = getattr(
            self, "prop_names_multiple", kwargs.get("prop_names_multiple", [])
        )

    def reset_entity_set(self):
        self.entity_set.__init__()

    def get_tmp_id(self, entity):
        """
        Step requires "prop_name_for_tmp_id" and "name"
        """
        try:
            prop_name = self.prop_name_for_tmp_id
            return f"{entity[prop_name]}"
        except:
            raise Exception(
                f"{self.prop_name_for_tmp_id} is required for each {self.name}."
            )

    def get_jexcel_ref_column(self, multiple=False):
        """Add a dropdown column for referencing a previously stored object via a tmp id"""
        obj_label = self.name.capitalize()
        source = []
        for id in self.entity_set.id_to_form_format.keys():
            source.append({"id": id, "name": id})

        return {
            "name": self.name,
            "title": obj_label,
            "width": "150",
            "type": "dropdown",
            "source": source,
            "multiple": multiple,
        }

    def set_id_form_format_from_jexcel_data(self, form_fields, sample_steps):
        """
        Convert JExel data to form format (see register_samples_post docstring)
        Also generates UUIDs for each entity
        Parameters:
            - form_fields: Allowed form fields, any property not here will be stored in self.json_str_prop
        """
        id_to_form_format = OrderedDict()
        for entity_as_list in self.entity_set.jexcel_data:
            entity_dict = {}
            user_json = {}
            for prop_name, value in zip(self.entity_set.prop_names, entity_as_list):

                if prop_name in self.prop_names_multiple:
                    value = [v.strip() for v in re.split(";|,", value)]

                # Nest referenced objects (using TMP ID)
                if prop_name in [s.name for s in self.nested_steps]:
                    nested_step = sample_steps.get_step_by_name(prop_name)
                    nested_id_to_form = nested_step.entity_set.id_to_form_format

                    if not value in nested_id_to_form:
                        if not nested_step.optional:
                            raise Exception(
                                f"<b>{prop_name}</b> is requiered for each {self.name}"
                            )
                    else:
                        entity_dict[nested_step.prop_name_in_db] = nested_id_to_form[
                            value
                        ]

                # List property
                elif type(value) == list and len(value) > 0:
                    entity_dict[prop_name] = value

                # Regular property
                elif value != "":
                    if prop_name in form_fields:
                        entity_dict[prop_name] = value
                    else:
                        user_json[prop_name] = value

            # Generates self.json_str_prop field
            if len(user_json) > 0:
                entity_dict[self.json_str_prop] = json.dumps(user_json)

            # Generates TMP ID
            tmp_id = self.get_tmp_id(entity_dict)

            # Generates UUID or take it from existing samples
            id_prop = self.prop_name_for_tmp_id
            if len(self.id_to_uuid) > 0 and entity_dict[id_prop]:
                entity_dict["uuid"] = self.id_to_uuid.get(
                    entity_dict[id_prop], str(uuid.uuid1())
                )
            else:
                entity_dict["uuid"] = str(uuid.uuid1())

            id_to_form_format[tmp_id] = entity_dict

        self.entity_set.id_to_form_format = id_to_form_format

    def set_id_form_format_from_form_format(self, data):
        """data: list of dict in form format"""
        id_to_form_format = OrderedDict()
        for entity_dict in data:
            tmp_id = self.get_tmp_id(entity_dict)
            id_to_form_format[tmp_id] = entity_dict

        self.entity_set.id_to_form_format = id_to_form_format


class StepTreatmentsInd(Step):
    def __init__(self, *args, **kwargs):
        self.number = 1
        self.name = "treatment_ind"
        self.prop_name_in_db = "treatment"
        self.prop_name_for_tmp_id = "treatment_id"
        self.label = "Treatment(s) on individual(s)"
        self.entity_set = TreatmentSet()
        self.form_name = "treatment"
        self.nested_steps = []
        self.name_prefix = "treatment_individual"
        self.label_prefix = "TRE > IND"
        self.select_option_group_label = "*** TREATMENT on an INDIVIDUAL ***"
        self.optional = True
        self.explanation_html = [
            """In this step, please register the <span class='i-roche-blue'>treatments</span> applied to the
            <span class='i-roche-blue'>individuals</span> (even controls).""",
            """The <code>Treatment ID</code> is required for each <span class='i-roche-blue'>treatment</span>
            and must be unique within your <span class='i-roche-blue'>treatments</span>.""",
            """In the next step, you'll be able to link each <span class='i-roche-blue'>individual</span> to
            a <span class='i-roche-blue'>treatment</span>.""",
            """<span class='font-weight-bold'>This step is optional.</span> Leave <span class='text-danger
            font-italic'>everything blank</span> if you don't have any
            <span class='i-roche-blue'>treatment</span> for <span class='i-roche-blue'>individuals</span>.""",
        ]
        self.is_final = False
        self.prop_names_multiple = []
        super().__init__(*args, **kwargs)


class StepIndividuals(Step):
    def __init__(self, *args, **kwargs):
        self.number = 2
        self.name = "individual"
        self.prop_name_in_db = "individual"
        self.prop_name_for_tmp_id = "individual_id"
        self.label = "Individual(s)"
        self.entity_set = IndividualSet()
        self.form_name = "individual"
        self.nested_steps = [StepTreatmentsInd()]
        self.name_prefix = "individual"
        self.label_prefix = "IND"
        self.select_option_group_label = "*** INDIVIDUAL ***"
        self.optional = True
        self.explanation_html = [
            """In this step, please register the <span class='i-roche-blue'>individuals</span> that your
            <span class='i-roche-blue'>samples</span> are coming from.""",
            """The <code>Individual ID</code> is required for each <span class='i-roche-blue'>individual</span>
            and must be unique within your <span class='i-roche-blue'>individuals</span>.""",
            """In the last step, you'll be able to link each <span class='i-roche-blue'>sample</span> to
            an <span class='i-roche-blue'>individual</span>.""",
            """<span class='font-weight-bold'>This step is optional but strongly recommended.</span> Only
            ignore it if you're really sure you don't need it (i.e. individual and specimen don't make sense at all
            in your study). Note that you can still use "pool" or "dummy" <span class='i-roche-blue'>individual</span>.""",
        ]
        self.is_final = False
        self.prop_names_multiple = []
        super().__init__(*args, **kwargs)

    def set_default_entity_set(self):
        form_format = self.entity_set.entity_class().get_default_form_format()
        self.set_id_form_format_from_form_format([form_format])

        jexcel_list = []
        self.entity_set.prop_names = []
        for prop_name, value in form_format.items():
            self.entity_set.prop_names.append(prop_name)
            jexcel_list.append(value)

        self.entity_set.jexcel_data = [jexcel_list]


class StepTreatmentsSam(Step):
    def __init__(self, *args, **kwargs):
        self.number = 3
        self.name = "treatment_sam"
        self.prop_name_in_db = "treatment"
        self.prop_name_for_tmp_id = "treatment_id"
        self.label = "Treatment(s) on sample(s)"
        self.entity_set = TreatmentSet()
        self.form_name = "treatment"
        self.nested_steps = []
        self.name_prefix = "treatment_sample"
        self.label_prefix = "TRE > SAM"
        self.select_option_group_label = "*** TREATMENT on a SAMPLE ***"
        self.optional = True
        self.explanation_html = [
            """In this step, please register the <span class='i-roche-blue'>treatments</span> applied to the
            <span class='i-roche-blue'>samples</span> (even controls).""",
            """The <code>Treatment ID</code> is required for each <span class='i-roche-blue'>treatment</span>
            and must be unique within your <span class='i-roche-blue'>treatments</span>.""",
            """In the next step, you'll be able to link each <span class='i-roche-blue'>sample</span> to
            a <span class='i-roche-blue'>treatment</span>.""",
            """<span class='font-weight-bold'>This step is optional.</span> Leave <span class='text-danger
            font-italic'>everything blank</span> if you don't have any
            <span class='i-roche-blue'>treatment</span> for <span class='i-roche-blue'>samples</span>.""",
        ]
        self.is_final = False
        self.prop_names_multiple = []
        super().__init__(*args, **kwargs)


class StepSamples(Step):
    def __init__(self, *args, **kwargs):
        self.number = 4
        self.name = "sample"
        self.prop_name_in_db = "samples"
        self.prop_name_for_tmp_id = "sample_id"
        self.label = "Sample(s)"
        self.entity_set = SampleSet()
        self.form_name = "sample"
        self.nested_steps = [StepTreatmentsSam(), StepIndividuals()]
        self.name_prefix = "sample"
        self.label_prefix = "SAM"
        self.select_option_group_label = "*** SAMPLE ***"
        self.optional = False
        self.explanation_html = [
            """In this step, please register the <span class='i-roche-blue'>samples</span>.""",
            """The <code>Sample ID</code> is required for each <span class='i-roche-blue'>sample</span>
            and must be unique within your <span class='i-roche-blue'>samples</span>.""",
            """The <code>Sample ID</code> will be used to reference your <span class='i-roche-blue'>samples</span>
            when you'll register the <span class='i-roche-blue'>readouts</span> in your
            <span class='i-roche-blue'>dataset</span>.""",
            """<span class='font-weight-bold'>This step is required.</span>""",
        ]
        self.is_final = True
        self.prop_names_multiple = ["parent_sample_id"]
        super().__init__(*args, **kwargs)


class StepReadouts(Step):
    def __init__(self, *args, **kwargs):
        self.name = "readout"
        self.prop_name_in_db = "readouts"
        self.form_name = "readout"
        self.prop_name_for_tmp_id = "readout_id"
        self.label = "Readout(s)"
        self.entity_set = ReadoutSet()
        self.name_prefix = "readout"
        self.label_prefix = "RDT"
        self.select_option_group_label = "*** READOUTS ***"
        self.optional = False
        self.explanation_html = []
        self.nest_obj_required = []
        self.obj_uuid_required = ["samples"]

        self.entity_name_to_db_name = {"samples": "samples", "readout": "readouts"}
        self.prop_names_multiple = ["samples"]
        super().__init__(*args, **kwargs)

    def set_id_form_format_from_jexcel_data(self, form_fields):
        """
        Convert JExel data to form format (see register_samples_post docstring)
        Also generates UUIDs for each entity
        INFO: JExcel concatenates string values with ";" for dropdowns with multiple choices
        Parameters:
            - form_fields: Allowed form fields, any property not here will be stored in self.json_str_prop
        """
        id_to_form_format = OrderedDict()

        related_id_to_obj = {}
        for prop_name in self.entity_set.prop_names:
            if prop_name in self.nest_obj_required + self.obj_uuid_required:
                # Ex: ReadoutSet must have a "sample_set" attribute that is a SampleSet
                if prop_name == "samples":
                    entity_set_attr = "sample_set"
                else:
                    entity_set_attr = prop_name
                entity_set = getattr(self.entity_set, entity_set_attr)
                related_id_to_obj[prop_name] = entity_set.id_to_form_format

        for entity_as_list in self.entity_set.jexcel_data:
            entity_dict = {}
            user_json = {}
            for j in range(len(entity_as_list)):
                prop_name = self.entity_set.prop_names[j]
                value = entity_as_list[j]

                if prop_name in self.prop_names_multiple:
                    value = [v.strip() for v in re.split(";|,", value)]

                # Nest referenced objects (using TMP ID)
                if prop_name in self.nest_obj_required + self.obj_uuid_required:
                    prop_name_in_db = self.entity_name_to_db_name[prop_name]

                    if type(value) == list:
                        if not all([v in related_id_to_obj[prop_name] for v in value]):
                            raise Exception(
                                f"<b>{prop_name}</b> missing or wrong for at least one {self.name}"
                            )

                        # Nest full object or take UUID only
                        if prop_name in self.nest_obj_required:
                            entity_dict[prop_name_in_db] = [
                                related_id_to_obj[prop_name][v] for v in value
                            ]
                        elif prop_name in self.obj_uuid_required:
                            entity_dict[prop_name_in_db] = [
                                related_id_to_obj[prop_name][v]["uuid"] for v in value
                            ]
                    else:
                        if not value in related_id_to_obj[prop_name]:
                            raise Exception(
                                f"<b>{prop_name}</b> missing or wrong for at least one {self.name}"
                            )

                        # Nest full object or take UUID only
                        if prop_name in self.nest_obj_required:
                            entity_dict[prop_name_in_db] = related_id_to_obj[prop_name][
                                value
                            ]
                        elif prop_name in self.obj_uuid_required:
                            entity_dict[prop_name_in_db] = related_id_to_obj[prop_name][
                                value
                            ]["uuid"]

                # List property
                elif type(value) == list and len(value) > 0:
                    entity_dict[prop_name] = value

                # Regular property
                elif value != "":
                    if prop_name in form_fields:
                        entity_dict[prop_name] = value
                    else:
                        user_json[prop_name] = value

            # Generates self.json_str_prop field
            if len(user_json) > 0:
                entity_dict[self.json_str_prop] = json.dumps(user_json)

            # Generates UUID and TMP ID
            tmp_id = self.get_tmp_id(entity_dict)
            entity_dict["uuid"] = str(uuid.uuid1())
            id_to_form_format[tmp_id] = entity_dict

        self.entity_set.id_to_form_format = id_to_form_format


class StepsSamples:
    def __init__(self, *args, **kwargs):
        """Initialize steps in correct oreder and set "previous_step" and "next_step" attributes"""
        self.treatment_ind = StepTreatmentsInd()
        self.individual = StepIndividuals(previous_step=self.treatment_ind)
        self.treatment_sam = StepTreatmentsSam(previous_step=self.individual)
        self.sample = StepSamples(previous_step=self.treatment_sam)

        self.treatment_ind.next_step = self.individual
        self.individual.next_step = self.treatment_sam
        self.treatment_sam.next_step = self.sample

        self.individual.nested_steps = [self.treatment_ind]
        self.sample.nested_steps = [self.treatment_sam, self.individual]

        # Used to iterate and to identify steps by numbers
        self.steps = [
            self.treatment_ind,
            self.individual,
            self.treatment_sam,
            self.sample,
        ]

    def get_step_by_number(self, number):
        if number < 1 or number > len(self.steps):
            raise Exception(f"Step number '{number}' not in correct range")

        for step in self.steps:
            if step.number == number:
                return self.steps[number - 1]

        raise Exception(f"Step number '{number}' not found in steps")

    def get_step_by_name(self, name):
        step = getattr(self, name, None)
        if step is None:
            raise Exception(f"Step name '{name}' was not found")

        return step

    def get_step_by_name_prefix(self, name_prefix):
        for step in self.steps:
            if step.name_prefix == name_prefix:
                return step
        raise Exception(f"Step name prefix '{name_prefix}' was not found")


###################################################
####### Other functions
###################################################
def get_step_entity_from_form_format(entity, step):
    """
    Input: entity in form format + step object
    Output: sub-entity in form format without parent or nested entity
    """
    bare_entity = copy.deepcopy(entity)
    if step.name == "sample":
        bare_entity.pop("individual", None)
        bare_entity.pop("treatment", None)

    elif step.name == "treatment_sam":
        bare_entity = bare_entity.get("treatment", None)

    elif step.name == "individual":
        bare_entity = bare_entity.get("individual", None)
        if bare_entity is not None:
            bare_entity.pop("treatment", None)

    elif step.name == "treatment_ind":
        bare_entity = bare_entity.get("individual", {}).get("treatment", None)

    # For readouts, nothing to do

    return bare_entity


def update_sample_step_uuid(sample, step, step_uuid):
    if step.name == "sample":
        sample["uuid"] = step_uuid

    elif step.name == "treatment_sam":
        sample["treatment"]["uuid"] = step_uuid

    elif step.name == "individual":
        sample["individual"]["uuid"] = step_uuid

    elif step.name == "treatment_ind":
        sample["individual"]["treatment"]["uuid"] = step_uuid

    return sample


def unify_sample_entities_uuids(existing_samples, new_samples):
    """
    Goal: Re-use UUIDs from existing entities if they are identic
    Parameters:
        - existing_samples: list of dict (form format)
        - new_samples: list of dict (form format)
    Output:
        - new_samples_updated: list of dict (form format)
    """
    new_samples_updated = []

    # Structure to store and retrieve unique entities by UUID
    unique_entities = []
    index_to_uuid = {}

    # Store existing entities with UUIDs
    for sample in existing_samples:
        for step in StepsSamples().steps:
            bare_entity = get_step_entity_from_form_format(sample, step)

            if bare_entity is None:
                continue

            if not bare_entity in unique_entities and "uuid" in bare_entity:
                tmp_uuid = bare_entity.pop("uuid")
                unique_entities.append(bare_entity)
                index = len(index_to_uuid)
                index_to_uuid[index] = tmp_uuid

    # Update or create UUIDs of new samples
    for sample in new_samples:
        for step in StepsSamples().steps:
            bare_entity = get_step_entity_from_form_format(sample, step)

            if bare_entity is None:
                continue

            potential_uuid = bare_entity.pop("uuid", None)

            if bare_entity in unique_entities:
                index = unique_entities.index(bare_entity)
                step_uuid = index_to_uuid[index]
            else:
                if potential_uuid is None:
                    step_uuid = str(uuid.uuid1())
                else:
                    step_uuid = potential_uuid

                unique_entities.append(bare_entity)
                index = len(index_to_uuid)
                index_to_uuid[index] = step_uuid

            sample = update_sample_step_uuid(sample, step, step_uuid)

        new_samples_updated.append(sample)

    return new_samples_updated


def validate_sample_against_form(sample, validate_dict, forms):
    """
    Performs validation of a sample (and its nested entities in form format) against forms
    Returns
        - validate (bool)
        - error
    """
    validate = True
    errors = []

    for step in StepsSamples().steps:
        validate_step = True
        errors_step = []
        bare_entity = get_step_entity_from_form_format(sample, step)

        if bare_entity is None or not validate_dict[step.name]:
            continue

        form = forms[step.name]()

        # Update entity format (ex: transform strings to booleans when needed)
        # Conversion the other way around to fill JExcel in build_xxx_session_from_form_format
        for field in form:
            if field.name in bare_entity:
                if field.type == "BooleanField":
                    bare_entity[field.name] = str_to_bool(bare_entity[field.name])

        form.process(data=bare_entity)

        # Validate field by field
        for field in form:
            condition_1 = field.flags.required and not field.validate(form)
            condition_2 = field.name in bare_entity and not field.validate(form)

            if condition_1 or condition_2:
                errors_step.append(
                    f"Field '{field.name}' did not validate: {field.errors}"
                )
                validate_step = False
                validate = False

        if not validate_step:
            error = f"Step '{step.name}' did not validate: {' / '.join(errors_step)}"
            errors.append(error)
    if not validate:
        error_string = "ERR: " + " ERR: ".join(errors)
        raise Exception(f"Sample {sample['uuid']} did not validate: {error_string}")

    return validate, errors