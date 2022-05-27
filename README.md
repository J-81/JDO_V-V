# V-V Scripts #

### What is this repository for? ###

V-V Scripts for RNASeq raw and processed data processed through the GeneLab RNASeq consensus
pipeline.

This project will seek to implement two kinds of V-V.  First, one that can be performed
on a standard file directory after processing.  Second, functions that are run as part of
the Nextflow implementation of the RNASeq consensus pipeline.

### How do I get set up? ###


* Summary of set up

If on the LBL server, I've already installed the latest release of this program to a conda environment on the /data2 partition.
Activate conda environment:
> conda activate /data2/JO_Internship_2021/conda/rnaseq_v1.0_modify

If on a different machine, you can install the program by downloading the release and running this inside the source code directory:
> pip install .

At this time, the dependencies are not included so this method will need additional steps to get it running.

### Usage ###

The following command should be available and print the help menu:
> V-V_Program

Testing Against Subsampled GLDS-194 with Default Parameters
> V-V_Program RNASeq --config oberyn_subsampled.config

Creating a custom parameters file called "copy_of_parameters.py".
> V-V_Program Params --copy_module_param_file

This file can be adjusted like any python file.
I've included an example of an adjusted file called 'strict_parameters.py' that has the "STRICT" parameter with all outlier deviations cut in half compared to the "DEFAULT" set.

This can be run as follows:
> V-V_Program RNASeq --config oberyn_subsampled.config --parameter_file strict_parameters.py --parameter_set STRICT

If you want to see the parameter sets available in a parameter file.
To see the module packaged parameter file's sets
> V-V_Program Params --list_parameter_sets

To see other parameter file sets (example using the custom made strict_parameters.py file)
> V-V_Program Params --list_parameter_sets strict_parameters.py

### Documentation (NOT UPDATED) ###
* Documentation For Top Level Functions

This is located in the docs folder.  Specifically, if you download the docs folder and open the index.html file, you should see the docs as generated by Sphinx. **Note: Along with the rest of the dev branch, these should be considered a work in progress and may not reflect the code exactly (although this is the goal)**

### Who do I talk to? ###

Admin: Jonathan Oribello
Email: Jonathan.D.Oribello@gmail.com
