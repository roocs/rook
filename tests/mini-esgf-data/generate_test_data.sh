#!/bin/bash

# Define all collections of files to copy to "small" local files

Amon_files="/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/rcp85/mon/atmos/Amon/r1i1p1/latest/tas/tas_*.nc"
zostoga_files="/badc/cmip5/data/cmip5/output1/INM/inmcm4/rcp45/mon/ocean/Omon/r1i1p1/latest/zostoga/zostoga_*.nc"
Lmon_files="/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/land/Lmon/r1i1p1/latest/rh/*.nc"
zostoga_2_files="/badc/cmip5/data/cmip5/output1/MPI-M/MPI-ESM-LR/rcp45/mon/ocean/Omon/r1i1p1/latest/zostoga/zostoga_*.nc"

#update this for the files being created
files=$zostoga_2_files
#file_path=$(dirname "/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/rcp85/mon/atmos/Amon/r1i1p1/latest/tas/tas_*.nc")
file_path=$(dirname $(printf $files))
output_dir=test_data$(echo $file_path)
mkdir -p $output_dir

# Define files variable as the files to convert this time
for f in $files ; do
    fname=$(basename $f)
    var_id=$(echo $fname | cut -d_ -f1)
    output_file=$output_dir/$fname

    lat_selector="-d lat,,,100"
    lon_selector="-d lon,,,100"

    extra=""

    # Add extra args for some cases
    if [[ $fname =~ "piControl" ]]; then
        extra=""
    elif [[ $fname =~ "esmControl" ]]; then
        extra=""
    elif [[ $fname =~ "day" ]]; then
        extra="-d plev,,,8"
    fi

    if [[ $fname =~ "ssp24" ]]; then
        lon_selector=""
    fi

    if [[ $fname =~ "zostoga" ]]; then
        lon_selector=""
        lat_selector=""
#        extra="-d lev,,,8"
    fi

    cmd="ncks $extra $lat_selector $lon_selector -v $var_id $f $output_file"
    echo $var_id
    echo "Running: $cmd"
    $cmd
    echo "Wrote: $output_file"
done
