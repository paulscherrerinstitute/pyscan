[![Build Status](https://travis-ci.org/paulscherrerinstitute/pyscan.svg?branch=master)](https://travis-ci.org/paulscherrerinstitute/pyscan)
[![Build status](https://ci.appveyor.com/api/projects/status/9oq871y9281iw19y?svg=true)](https://ci.appveyor.com/project/simongregorebner/pyscan)

# Overview
**pyscan** is a Python scanning library for Channel Access and beam synchronous (SwissFEL) data. 

There are multiple interfaces available for backward compatibility, but new features are available only on 
the new interface, therefore using the new interface is strongly recommended. The old interfaces were developed 
to facilitate the migration to the new library. Only the new interface will be presented 
in this document. For information on how to use other interfaces, consult their original manual.

# Install

## Conda setup
If you use conda, you can create an environment with the pyscan library by running:

```bash
conda create -c paulscherrerinstitute --name <env_name> pyscan
```

After that you can just source you newly created environment and start using the library.

## Local build
You can build the library by running the setup script in the root folder of the project:

```bash
python setup.py install
```

or by using the conda also from the root folder of the project:

```bash
conda build conda-recipe
conda install --use-local pyscan
```

### Requirements
The library relies on the following packages:

- python
- numpy
- pyepics
- bsread

In case you are using conda to install the packages, you might need to add the **paulscherrerinstitute** channel to 
your conda config:

```bash
conda config --add channels paulscherrerinstitute
```

# Usage

A sample scan, that uses the most common pyscan features, can be done by running:

```Python
from pyscan.positioner.vector import VectorPositioner
from pyscan.scan_parameters import epics_pv, epics_monitor, scan_settings
from pyscan.dal.epics_utils import action_set_epics_pv, action_restore
from pyscan.scan import scan

# Defines positions to move the motor to.
positions = [1, 2, 3, 4]
positioner = VectorPositioner(positions)

# Move MOTOR1 over defined positions.
writables = [epics_pv("PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR1:GET")]

# Read "PYSCAN:TEST:OBS1" value at each position.
readables = [epics_pv("PYSCAN:TEST:OBS1")]

# At each read of "PYSCAN:TEST:OBS1", check if "PYSCAN:TEST:VALID1" == 10
monitors = [epics_monitor("PYSCAN:TEST:VALID1", 10)]

# Before the scan starts, set "PYSCAN:TEST:PRE1:SET" to 1.
initialization = [action_set_epics_pv("PYSCAN:TEST:PRE1:SET", 1, "PYSCAN:TEST:PRE1:GET")]

# After the scan completes, restore the original value of "PYSCAN:TEST:MOTOR1:SET".
finalization = [action_restore(writables)]

# At each position, do 4 readings of the readables with 4Hz (0.25 seconds between readings).
settings = scan_settings(measurement_interval=0.25, n_measurements=4)

# Execute the scan and get the result.
result = scan(positioner=positioner, 
              writables=writables, 
              readables=readables,
              monitors=monitors,
              initialization=initialization,
              finalization=finalization,
              settings=settings)
```

In the following chapters, each component will be explained in more details:

- **Positioner**: Generates positions, according to the input values, on which to place the writables.
- **Writables**: PVs (motors, in most cases) to move according to the positioner values.
- **Readables**: PVs or BS read properties to read at each position.
- **Monitors**: PVs or BS read properties used to validate the readables at each position.
- **Initialization**: Actions to execute before the scan.
- **Finalization**: Actions to execute after the scan is completed or when the scan is aborted.
- **Settings**: Settings of the scan and acquisition of data.
- **Scan result**: List of readables values at each scan position.

For common use cases, see the chapter at the end of this document.


## Positioner
Positioners generate positions based on the input data received and the type of positioner selected. In case a 
complex scan is required, more positioners can be chained together. Alternatively, the user can generate the list of 
positions, and just use a Vector positioner (it just moved the motor to the provided positions).

We have different positioners for different use cases:

- **Vector positioner**: Scan over the provided positions, one by one. The most simple and flexible positioner.
- **Line positioner**: Define start, end position, and number of steps. Step values will be automatically generated.
- **Area positioner**: Like line positioner, but in multiple dimensions, varying one dimension at the time.
- **Serial positioner**: Like vector positioner, but varying one motor at the time, 
returning other motors at their initial position
- **Compound positioner**: Combine multiple positioners together, generating the desired positions.

It is recommended to start your scanning with the **Vector positioner**, as it is the most simple to use, 
and in most cases it is powerful enough.

### Vector and Line positioner
![Vector positioner representation](/docs/images/vector.png?raw=true)

### Area positioner
![Area positioner representation](/docs/images/area.png?raw=true)

### Serial positioner
![Serial positioner representation](/docs/images/serial.png?raw=true)

### Compound positioner

## Writables

## Readables

## Monitors

## Initialization and Finalization

## Settings

## Scan result

# Common use cases