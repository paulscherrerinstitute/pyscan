[![Build Status](https://travis-ci.org/paulscherrerinstitute/pyscan.svg?branch=master)](https://travis-ci.org/paulscherrerinstitute/pyscan)
[![Build status](https://ci.appveyor.com/api/projects/status/9oq871y9281iw19y?svg=true)](https://ci.appveyor.com/project/simongregorebner/pyscan)

# Overview
**pyscan** is a Python scanning library for Channel Access and beam synchronous (SwissFEL) data. 

There are multiple interfaces available for backward compatibility, but new features are available only on 
the new interface, therefore using the new interface is strongly recommended. The old interfaces were developed 
to facilitate the migration to the new library. Only the new interface will be presented 
in this document. For information on how to use other interfaces, consult their original manual.

# Table of content
1. [Install](#install)
    1. [Conda setup](#conda_setup)
    2. [Local build](#local_build)
2. [Usage](#usage)
    1. [Positioners](#positioners)
        1. [Vector and Linear positioner](#vector_and_line_positioner)
        2. [Area positioner](#area_positioner)
        3. [Serial positioner](#serial_positioner)
        4. [Compound positioner](#compound_positioner)
    2. [Writables](#writables)
    3. [Readables](#readables)
    4. [Monitors](#monitors)
    5. [Initialization and Finalization](#init_and_fin)
    6. [Scan settings](#settings)
    7. [Scan result](#scan_results)
3. [Library configuration](#configuration)
4. [Common use cases](#common_use_cases)

<a id="install"></a>
# Install

<a id="conda_setup"></a>
## Conda setup
If you use conda, you can create an environment with the pyscan library by running:

```bash
conda create -c paulscherrerinstitute --name <env_name> pyscan
```

After that you can just source you newly created environment and start using the library.

<a id="local_build"></a>
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

<a id="usage"></a>
# Usage 

**Note**: All the examples in this README can also be found in the **tests/test_readme.py** file.

A sample scan, that uses the most common pyscan features, can be done by running:

```Python
from pyscan import *

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
- **Scan settings**: Settings of the scan and acquisition of data.
- **Scan result**: List of readables values at each scan position.

For common use cases, see the chapter at the end of this document.

<a id="positioners"></a>
## Positioners
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

<a id="vector_and_line_positioner"></a>
### Vector and Line positioner
This 2 positioners are the most common ones and they are interchangable. A Line positioner is just a different 
way of defining a vector positioner. In the example below, we will show how this 2 positioners work.

All the positioners specified in the code snippet below generate **exactly the same positions**.

```python
from pyscan import *

# Dummy value initialization.
x1, x2, x3, x4 = range(1, 5)
y1, y2, y3, y4 = range(1, 5)

# Move to positions x1,y1; then x2,y2; x3,y3; x4,y4.
vector_positioner = VectorPositioner(positions=[[x1, y1], [x2, y2], [x3, y3], [x4, y4]])

# Start at positions x1,y1; end at positions x4,y4; make 3 steps to reach the end.
line_positioner_n_steps = LinePositioner(start=[x1, y1], end=[x4, y4], n_steps=3)

# Start at position x1,y1; end at position x4,y4: make steps of size x2-x1 for x axis and y2-y1 for y axis.
line_positioner_step_size = LinePositioner(start=[x1, y1], end=[x4, y4], step_size=[x2-x1, y2-y1])
```

Positions generated by any of the positioners above can be visualised as:

![Vector positioner representation](/docs/images/vector.png?raw=true)

**Pn** denotes the point given by the positioner. In this case, the positions in ascending order are:

- P1 (x1, y1)
- P2 (x2, y2)
- P3 (x3, y3)
- P4 (x4, y4)

It is important to note:

- All axis are moved at the same time (x and y in this case).
- LinePositioner accepts either the number of steps (integer) or the step size (array of numbers, one for each axis). 
In case you specify the step size, **(end-start) / step_size** must be the same for all axis - because all axis are 
moved at the same time, the number of steps for each axis must be the same.

<a id="area_positioner"></a>
### Area positioner
The Area positioner is a multi dimensional variation of the LinePositioner. Instead of moving all axis at the same time, 
it moves one axis at the time, covering all positions that can be reached by combing the given axis. With a 2 axis scan,
you can imagine it as scanning line by line.

All the positioners specified in the code snippet below generate **exactly the same positions**. Furthermore, the input 
parameters for the AreaPositioner are very similar to the one used in the previous example for the LinePositioner to 
show the difference in output positions.

```python
from pyscan import *

# Dummy value initialization.
x1, x2, x3, x4 = range(1, 5)
y1, y2, y3, y4 = range(1, 5)

area_positioner_n_steps = AreaPositioner(start=[x1, y1], end=[x4, y4], n_steps=[3,3])
area_positioner_step_size = AreaPositioner(start=[x1, y1], end=[x4, y4], step_size=[x2-x1, y2-y1])
```

Positions generated by any of the positioners above can be visualised as:

![Area positioner representation](/docs/images/area.png?raw=true)

**Pn** denotes the point given by the positioner. In this case, the positions in ascending order are:

- P1 (x1, y1)
- P2 (x1, y2)
- P3 (x1, y3)
- P4 (x1, y4)
- ...
- P13 (x4, y1)
- P14 (x4, y2)
- P15 (x4, y3)
- P16 (x4, y4)

It is important to note:

- The first provided axis(x) is the slowest changing dimension, while the last provided axis(y) is 
the faster changing one.
- AreaPositioner accepts either the number of steps (array of numbers, one for each axis) or the step size 
(array of numbers, one for each axis). 

**Warning**: LinePositioner accepts an integer for n_steps, while AreaPositioners accepts an array 
of integers. This is due to the fact that the AreaPositioner can have a different number of steps for different axis,
while LinePositioner cannot. The same logic holds true for the step_size.

<a id="serial_positioner"></a>
### Serial positioner
![Serial positioner representation](/docs/images/serial.png?raw=true)

<a id="compound_positioner"></a>
### Compound positioner
A compound positioner allows you to combine multiple positioners together. This allows you to generate more complex 
motions without having to generate all the positions up front and passing them to the VectorPositioner.
The CompoundPositioner can be compared to the AreaPositioner in the sense that it combines multiple positioners in the 
same way as AreaPositioner combines multiple axis.

The CompoundPositioner concatenates all positioner values in a single output. It iterates over each given positioner,
one at the time, covering all possible permutations - In a 2D scan, you can imagine it as scanning line by line. The
last provided positioner is always the fastest changing one, while the first provided one is the slowest.

To better explain how it works, the following example demonstrates how to create an area positioner, 
the one we used in the example above, from 2 VectorPositioners.

```python
from pyscan import *

x1, x2, x3, x4 = range(1, 5)
y1, y2, y3, y4 = range(1, 5)

line_positioner = VectorPositioner([x1, x2, x3, x4])
column_positioner = VectorPositioner([y1, y2, y3, y4])

area_positioner = CompoundPositioner([line_positioner, column_positioner])
```

Positions generated by the positioner above can be visualised as:

![Area positioner representation](/docs/images/area.png?raw=true)

**Pn** denotes the point given by the positioner. In this case, the positions in ascending order are:

- P1 (x1, y1)
- P2 (x1, y2)
- P3 (x1, y3)
- P4 (x1, y4)
- ...
- P13 (x4, y1)
- P14 (x4, y2)
- P15 (x4, y3)
- P16 (x4, y4)

It is important to note:

- The first provided positioner is the slowest changing dimension, while the last provided positioner is 
the faster changing one.
- Compound positioner accept any number and type of positioners (including itself).
- Compound positioner combines the output of all provided positioners at every position, concatenating the individual 
positions provided by each positioners in the same order that they were specified when constructing the 
CompoundPositioner.

<a id="writables"></a>
## Writables
Writables are PVs that are used to move the motors. The positions generated by the positioner are passed to the 
writables. The position values are written to the writables with the **set_and_match** logic (discussed below).

**Warning**: The number of writables should always match the number of axis the positioner outputs. If we want to 
move 2 axis, the positioner has to output 2 values per position.

Writables can be a list or a single value of type EPICS_PV. EPICS_PV is a named tuple that can be generated 
by invoking the method **epics_pv()**:

```python
from pyscan.scan_parameters import epics_pv

# Define a writable, with set PV "PYSCAN:TEST:MOTOR1:SET" and readback PV "PYSCAN:TEST:MOTOR1:GET".
# When moving the motor, a tolerance of 0.01 should be used for positioning.
motor_1 = epics_pv(pv_name="PYSCAN:TEST:MOTOR1:GET",
                   readback_pv_name="PYSCAN:TEST:MOTOR1:SET",
                   tolerance=0.01)
                                 
# Define a writable, with PV "PYSCAN:TEST:MOTOR2" for both set and readback. Tolerance will be the default one.
motor_2 = epics_pv(pv_name="PYSCAN:TEST:MOTOR2")

# We would like to move both above defined motors in this scan.
writables = [motor_1, motor_2]
```

Only the **pv_name** argument is mandatory. If not provided, the readback_pv_name is the same as the pv_name, and 
tolerance is the library defined default one.

**set_and_match** is the logic used to set the writables PV values. 
We set a PV value and wait until the readback PV reaches the setpoint. If this does not happen in a defined
time (write_timeout setting, check chapter **Settings**), an exception is thrown.

<a id="readables"></a>
## Readables

<a id="monitors"></a>
## Monitors 

<a id="init_and_fin"></a>
## Initialization and Finalization

<a id="settings"></a>
## Scan settings
Settings allow to specify the scan parameters. They provide already some defaults which should work for the most 
common scans. The available settings are:

- **measurement_interval**
- **n_measurements**
- **write_timeout**
- **settling_time**
- **progress_callback** (Default: print progress to console): Callback function to be invoked for progress updates.

<a id="scan_results"></a>
## Scan result

<a id="configuration"></a>
# Library configuration
Common library settings can be set in the **pyscan/config.py** module, either at run time or when deployed. Runtime 
changes are preferable, since they do not affect other users.

For example, to change the bs_read connection address and port, execute:

```python
from pyscan import config
config.bs_default_host = "127.0.0.1"
config.bs_default_port = 9999
```

To get the list of available configuration check the module source or run:

```python
from pyscan import config
help(config)
```

**Warning**: Only in rare cases, if at all, this settings should be changed. Most strictly scan related parameters 
can be configured using the [Scan settings](#settings).

<a id="common_use_cases"></a>
# Common use cases