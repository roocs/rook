from daops.data_utils.attr_utils import (
    edit_var_attrs,
    edit_global_attrs,
    remove_coord_attr,
)
from daops.data_utils.coord_utils import add_scalar_coord, add_coord
from daops.data_utils.var_utils import add_data_var

model_specific_global_attrs = {
    "CMCC-CM2-SR5": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",  # noqa
        "initialization_description": "hindcast initialized based on observations and using historical forcing",  # noqa
    },
    "EC-Earth3": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",  # noqa
        "initialization_description": "Atmosphere initialization based on full-fields from ERA-Interim (s1979-s2018) or ERA-40 (s1960-s1978); ocean/sea-ice initialization based on full-fields from NEMO/LIM assimilation run nudged towards ORA-S4 (s1960-s2018)",  # noqa
    },
    "HadGEM3-GC31-MM": {
        "forcing_description": "f2, CMIP6 v6.2.0 forcings; no ozone remapping",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",  # noqa
        "initialization_description": "hindcast initialized based on observations and using historical forcing",  # noqa
    },
    "MPI-ESM1-2-HR": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",  # noqa
        "initialization_description": "hindcast initialized based on observations and using historical forcing",  # noqa
    },
    "MPI-ESM1-2-LR": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",  # noqa
        "initialization_description": "hindcast initialized based on observations and using historical forcing",  # noqa
    },
}


def get_decadal_model_attr_from_dict(ds_id, ds, attr):
    # TODO: method taken from daops.fix_utils.decadal_utils.py
    # Add the model-specific global attr
    model = ds_id.split(".")[3]
    value = model_specific_global_attrs[model][attr]
    return value


def apply_decadal_fixes(ds_id, ds):
    ds_mod = decadal_fix_1(ds_id, ds)
    ds_mod = decadal_fix_2(ds_id, ds_mod)
    ds_mod = decadal_fix_3(ds_id, ds_mod)
    ds_mod = decadal_fix_4(ds_id, ds_mod)
    ds_mod = decadal_fix_5(ds_id, ds_mod)
    return ds_mod


def decadal_fix_1(ds_id, ds):
    operands = {"var_id": "time", "attrs": {"long_name": "valid_time"}}
    ds_mod = edit_var_attrs(ds_id, ds, **operands)
    return ds_mod


def decadal_fix_2(ds_id, ds):
    operands = {
        "attrs": {
            "forcing_description": get_decadal_model_attr_from_dict(
                ds_id, ds, "forcing_description"
            ),  # noqa
            "physics_description": get_decadal_model_attr_from_dict(
                ds_id, ds, "physics_description"
            ),  # noqa
            "initialization_description": get_decadal_model_attr_from_dict(
                ds_id, ds, "initialization_description"
            ),  # noqa
            "startdate": "derive: daops.fix_utils.decadal_utils.get_sub_experiment_id",
            "sub_experiment_id": "derive: daops.fix_utils.decadal_utils.get_sub_experiment_id",
        }
    }

    ds_mod = edit_global_attrs(ds_id, ds, **operands)
    return ds_mod


def decadal_fix_3(ds_id, ds):
    operands = {
        "var_id": "reftime",
        "value": "derive: daops.fix_utils.decadal_utils.get_reftime",
        "dtype": "datetime64[ns]",
        "attrs": {
            "long_name": "Start date of the forecast",
            "standard_name": "forecast_reference_time",
        },
        "encoding": {
            "dtype": "int32",
            "units": "days since 1850-01-01",
            "calendar": "derive: daops.fix_utils.decadal_utils.get_time_calendar",
        },
    }

    ds_mod = add_scalar_coord(ds_id, ds, **operands)
    return ds_mod


def decadal_fix_4(ds_id, ds):
    operands = {
        "var_id": "leadtime",
        "value": "derive: daops.fix_utils.decadal_utils.get_lead_times",
        "dim": ["time"],
        "dtype": "float64",
        "attrs": {
            "long_name": "Time elapsed since the start of the forecast",
            "standard_name": "forecast_period",
            "units": "days",
        },
        "encoding": {"dtype": "double"},
    }

    ds_mod = add_coord(ds_id, ds, **operands)
    return ds_mod


def decadal_fix_5(ds_id, ds):
    operands = {
        "var_id": "realization",
        "value": "1",
        "dtype": "int32",
        "attrs": {
            "long_name": "realization",
            "comment": "For more information on the ripf, refer to the variant_label, initialization_description, physics_description and forcing_description global attributes",  # noqa
        },
    }

    ds_mod = add_data_var(ds_id, ds, **operands)
    return ds_mod
