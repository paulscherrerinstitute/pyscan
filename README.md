[![Build Status](https://travis-ci.org/paulscherrerinstitute/pyscan.svg?branch=master)](https://travis-ci.org/paulscherrerinstitute/pyscan)
[![Build status](https://ci.appveyor.com/api/projects/status/9oq871y9281iw19y?svg=true)](https://ci.appveyor.com/project/simongregorebner/pyscan)

**pyscan** is a Python scanning library for Channel Access and beam synchronous (SwissFEL) data.

# Table of content
1. [Overview](#c_overview)
    1. [Minimal working example](#c_minimal_working_example)
    2. [Sample scan](#c_sample_scan)
    3. [Introduction](#c_introduction)
2. [Install](#c_install)
    1. [Conda setup](#c_conda_setup)
    2. [Local build](#c_local_build)
3. [Usage](#c_usage)
    1. [Positioners](#c_positioners)
        1. [Vector and Line positioner](#c_vector_and_line_positioner)
        2. [Area positioner](#c_area_positioner)
        3. [Serial positioner](#c_serial_positioner)
        4. [Compound positioner](#c_compound_positioner)
        5. [Time positioner](#c_time_positioner)
    2. [Writables](#c_writables)
    3. [Readables](#c_readables)
    4. [Conditions](#c_conditions)
    5. [Initialization and Finalization](#c_init_and_fin)
    6. [Before and after executor](#c_before_and_after)
    7. [Scan settings](#c_scan_settings)
    8. [Scan result](#c_scan_results)
4. [Library configuration](#c_configuration)
5. [Common use cases](#c_common_use_cases)
    1. [Scanning camera images from cam_server with camera_name](#c_scanning_images_from_cam)
    2. [Scanning with custom data sources](#c_scanning_custom_sources)
6. [Other interfaces](#c_other_interfaces)
    1. [pshell](#c_pshell)
    2. [Old pyScan](#c_old_pyscan)

<a id="c_overview"></a>
# Overview
There are multiple interfaces available, but new features are available only on
the new interface, therefore using the new interface is strongly recommended. The other interfaces were developed
to facilitate the migration to and integration of pyscan. Only the new interface will be presented
in this document. For information on how to use the other interfaces, consult their original manual. A few examples
are however available at the end of this document, under the [Other interfaces](#other_interfaces) chapter.

<a id="c_minimal_working_example"></a>
## Minimal working example
The following is the minimal working example you can run on your machine with only pyscan installed.

```python
from pyscan import *

# Collect 5 data points.
positioner = StaticPositioner(n_images=5)

# The function will count from 1 to 5 (it will be invoked 5 times, because n_images == 5).
def data_provider():
    data_provider.counter += 1
    return data_provider.counter
data_provider.counter = 0
    
# result == [[1], [2], [3], [4], [5]]
result = scan(positioner, data_provider)
```

<a id="c_sample_scan"></a>
## Sample scan

A sample scan, that uses the most common pyscan features, can be done by running:

```Python
# Import everything you need.
from pyscan import *

# Defines positions to move the motor to.
positions = [1, 2, 3, 4]
positioner = VectorPositioner(positions)

# Read "PYSCAN:TEST:OBS1" value at each position.
readables = [epics_pv("PYSCAN:TEST:OBS1")]

# Move MOTOR1 over defined positions.
writables = [epics_pv("PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR1:GET")]

# At each read of "PYSCAN:TEST:OBS1", check if "PYSCAN:TEST:VALID1" == 10
conditions = [epics_condition("PYSCAN:TEST:VALID1", 10)]

# Before the scan starts, set "PYSCAN:TEST:PRE1:SET" to 1.
initialization = [action_set_epics_pv("PYSCAN:TEST:PRE1:SET", 1, "PYSCAN:TEST:PRE1:GET")]

# After the scan completes, restore the original value of "PYSCAN:TEST:MOTOR1:SET".
finalization = [action_restore(writables)]

# At each position, do 4 readings of the readables with 10Hz (0.1 seconds between readings).
settings = scan_settings(measurement_interval=0.1, n_measurements=4)

# Execute the scan and get the result.
result = scan(positioner=positioner,
              readables=readables,
              writables=writables,
              conditions=conditions,
              initialization=initialization,
              finalization=finalization,
              settings=settings)
```

<a id="c_introduction"></a>
## Introduction
In this chapter we summarize the various objects described in detail in this document. To access the objects
documentation directly, you can consult the source code or simply execute, for example:
```python
from pyscan import *
help(epics_pv)
```
This will give you the documentation for **epics_pv**, but you can substitute this with any other bolded object in
this chapter.

### Positioners
How should we move the writables - in most cases motors - to the desired position.

- **VectorPositioner**: Move all the axis according to the supplied list of positions.
- **LinePositioner**: Move all the provided axis at once.
- **AreaPositioner**: Move all provided axis, one by one, covering all combinations.
- **SerialPositioner**: Move one axis at the time. Before moving the next axis, return the first to the original
position.
- **CompoundPositioner**: Combine multiple other positioners, with the AreaPositioner logic (all combinations).
- **TimePositioner**: Sample readables, without moving motors, at a specified interval.

### Writables
Which variables - motors in most cases - to write the values from the positioners.

- **epics_pv**: Write to epics process variable.
- **function_value**: Write to function you provide.

### Readables
Which variables to read at each position.

- **epics_pv**: Read an epics process variable.
- **bs_property**: Read a bsread property.
- **function_value**: Read from a function you provide.

### Conditions
Which values to check after each data acquisition. Useful to verify if the acquired data is valid.

- **epics_condition**: Verify that an epics PV has a certain value.
- **bs_condition**: Verify that a bsread property has a certain value.
- **function_condition**: Verify that a function you provide returns True.

### Actions
Action can be executed for initialization, finalization, before and after each data acquisition.

- initialization: Executed once, before the beginning of the scan.
- before_read: Executed every time before the measurements are taken.
- after_read: Executed every time after the measurements are taken.
- finalization: Executed once, at the end of the scan or when an exception is raise during the scan.

Available actions:

- **action_set_epics_pv**: Set an epics PV value.
- **action_restore**: Restore the original pre-scan values of specified PVs.
- Any method you provide. The method must be without arguments. Example:
```python
def do_something():
    pass
```

### Settings
Setup the various scan parameters.

- **scan\_settings**: All available parameters to set.

<a id="c_install"></a>
# Install

<a id="c_conda_setup"></a>
## Conda setup
If you use conda, you can create an environment with the pyscan library by running:

```bash
conda create -c paulscherrerinstitute --name <env_name> pyscan
```

After that you can just source you newly created environment and start using the library.

<a id="c_local_build"></a>
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

<a id="c_usage"></a>
# Usage

**Note**: All the examples in this README can also be found in the **tests/test_readme.py** file.

In the following chapters, each component will be explained in more details:

- **Positioner**: Generates positions, according to the input values, on which to place the writables.
- **Readables**: PVs or BS read properties to read at each position.
- **Writables**: PVs (motors, in most cases) to move according to the positioner values.
- **Conditions**: PVs or BS read properties used to validate the readables at each position.
- **Initialization**: Actions to execute before the scan.
- **Finalization**: Actions to execute after the scan is completed or when the scan is aborted.
- **Scan settings**: Settings of the scan and acquisition of data.
- **Scan result**: List of readables values at each scan position.

For common use cases, see the chapter at the end of this document.

<a id="c_positioners"></a>
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

<a id="c_vector_and_line_positioner"></a>
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

# Start at position x1,y1; end at position x4,y4: make steps of size x2-x1 for x axis and
# y2-y1 for y axis.
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

<a id="c_area_positioner"></a>
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

<a id="c_serial_positioner"></a>
### Serial positioner
A serial positioners moves one axis at the time, returning the previously moved axis back to its original position.

```python
from pyscan import *

# Dummy value initialization.
x0 = y0 = 0
x1, x2, x3, x4 = range(1, 5)
y1, y2, y3, y4 = range(1, 5)

serial_positioner = SerialPositioner(positions=[[x1, x2, x3, x4], [y1, y2, y3, y4]],
                                     initial_positions=[x0, y0])
```

The positions generated from the positioner above can be visualized as:

![Serial positioner representation](/docs/images/serial.png?raw=true)

**Pn** denotes the point given by the positioner. In this case, the positions in ascending order are:

- P1 (x1, y0)
- P2 (x2, y0)
- P3 (x3, y0)
- P4 (x4, y0)
- P5 (x0, y1)
- P6 (x0, y2)
- P7 (x0, y3)
- P8 (x0, y4)

**Warning**: Unlike other positioners, in the Serial positioner the first dimension is the one that changes first.
In the example above, this means that X gets iterated over first, and then Y.

<a id="c_compound_positioner"></a>
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

<a id="c_time_positioner"></a>
### Time positioner
This positioner is different from the others in the sense that it does not generate positions for the motors,
but time intervals at which to sample the readables. It is useful for acquisitions that recquire a time based
sampling without moving any motors. One such example you be to sample a bsread source with a certain interval.

Because this positioner does not move any motor, you should not specify any writables, as they will not be moved.

```python
from pyscan import *

# Sample the readables at 10Hz, acquire 30 samples.
time_positioner = TimePositioner(time_interval=0.1, n_intervals=30)
# Read "PYSCAN:TEST:OBS1" epics PV.
readables = [epics_pv("PYSCAN:TEST:OBS1")]

result = scan(positioner=time_positioner, readables=readables)
```

<a id="c_writables"></a>
## Writables
Writables are PVs that are used to move the motors. The positions generated by the positioner are passed to the
writables. The position values are written to the writables with the **set_and_match** logic (discussed below).

**Warning**: The number of writables should always match the number of axis the positioner outputs. If we want to
move 2 axis, the positioner has to output 2 values per position.

Writables can be a list or a single value of type EPICS_PV, or a function that accepts one parameter - position. 
EPICS_PV is a named tuple that can be generated by invoking the method **epics\_pv()**:

```python
from pyscan.scan_parameters import epics_pv

# Define a writable, with set PV "PYSCAN:TEST:MOTOR1:SET" and readback PV "PYSCAN:TEST:MOTOR1:GET".
# When moving the motor, a tolerance of 0.01 should be used for positioning.
motor_1 = epics_pv(pv_name="PYSCAN:TEST:MOTOR1:GET",
                   readback_pv_name="PYSCAN:TEST:MOTOR1:SET",
                   tolerance=0.01)

# Define a writable, with PV "PYSCAN:TEST:MOTOR2" for both set and readback. Tolerance will be the
# default one.
motor_2 = epics_pv(pv_name="PYSCAN:TEST:MOTOR2")

# We would like to move both above defined motors in this scan.
writables = [motor_1, motor_2]
```

Only the **pv_name** argument is mandatory. If not provided, the readback_pv_name is the same as the pv_name, and
tolerance is the library defined default one.

**set_and_match** is the logic used to set the writables PV values.
We set a PV value and wait until the readback PV reaches the setpoint. If this does not happen in a defined
time (write_timeout setting, check chapter **Settings**), an exception is thrown.

In addition to the epics_pv, you can provide your own writable function, which has to accept one positional argument
representing the next position your motor (or device) should move to.

FUNCTION_VALUE is a named tuple that can be generated by invoking the method **function\_value()**:
```python
from pyscan.scan_parameters import function_value

# Define a writable, with set PV "PYSCAN:TEST:MOTOR1:SET" and readback PV "PYSCAN:TEST:MOTOR1:GET".
# When moving the motor, a tolerance of 0.01 should be used for positioning.

def move_motor1(position):
    # Actually move the motor 2.
    pass
    
def move_motor2(position):
    # Actually move the motor 2.
    pass

# Define the motor 1 writable by providing the call function and the name.
motor_1 = function_value(call_function=move_motor1,
                         name="Motor1")

# You can also omit the call to the function_value: In this case you cannot specify the name of the writable.
# The name will be automatically assigned.
motor_2 = move_motor2

# We would like to move both above defined motors in this scan.
writables = [motor_1, motor_2]
```

### Alternative way for specifying writables
Instead of calling the variable definition methods as shown above (epics_pv(), bs_property(), function_value())
you can use the following conventions:

```python
# Direct epics value definition.
epics_motor = "ca://PYSCAN:TEST:OBS1"
# Direct function value definition
def set_position(position):
    pass

writables = [epics_motor, set_position]
```

If you use this alternative way of defining the writables, you do not have access to the readback_pv_name, 
tolerance, and readback_pv_value of the epics_pv. 

In this case the default values will be used:

- **readback\_pv\_name**: Same as the set PV name.
- **readback\_pv\_value**: Same as the setpoint.
- **tolerance**: As specified in **pyscan.config.max\_float\_tolerance** for float values.

<a id="c_readables"></a>
## Readables
This are variables you read at every scan position. The result of the read is saved as a list entry in the output.
You can have as many readables as you like, but at least 1 is mandatory (a scan without readables does not make much
sense).

Readables can be a list or a single value of types:

- **epics\_pv**: Epics process variable.
- **bs\_property**: BS read property.
- **function\_value**: You provide a function that retrieves the next value for this variable.

You can mix the 3 types in any order you like. The order in which you declare the variables will be the order in which
they appear in the result list.

```python
from pyscan import *
value1 = epics_pv("PYSCAN:TEST:OBS1")
value2 = bs_property("CAMERA1:OBS2")
value3 = epics_pv("PYSCAN:TEST:OBS3")

def get_random():
    # A fair dice was used to determine the value.
    return 4
value4 = function_value(get_random, "random_value")

# bs properties with default value 'None'. See notes on the bottom.
value5 = bs_property("CAMERA1:OBS4", None)

readables = [value1, value2, value3, value4, value5]
```

**Default values**
In some cases, not all bs read properties are present in each stream message. In this case, the default behaviour is 
to raise an Exception with the missing property. This behaviour can be changed using the *default\_value* 
parameter of bs_property. If specified, when values are missing the stream, the default value is used. The same 
logic applies to bs_condition.

You can change the default behaviour for all bs_read properties by changing the config:
```python
from pyscan import config
# Instead of raising an exception, the default value for missing bs read properties is None.
config.bs_default_missing_property_value = None
```

### Alternative way for specifying readables
Instead of calling the variable definition methods as shown above (epics_pv(), bs_property(), function_value())
you can use the following conventions:

```python
# Direct epics value definition.
epics_value = "ca://PYSCAN:TEST:OBS1"
# Direct bs_property value definition.
bs_property = "bs://CAMERA1:OBS2"
# Direct function value definition
def get_random():
    return 0

readables = [epics_value, bs_property, get_random]
```

<a id="c_conditions"></a>
## Conditions
This are variables you monitor after each data acquisition to be sure that they have a certain values. A typical
example would be to verify if the beam repetition rate is in the desired range. The library supports 
PVs, bsread properties, and function conditions.

Conditions can be created by invoking **epics\_condition** for PV condition, and **bs\_condition** for 
bsread conditions. 
Function conditions can be created by invoking **function_condition**, or simply passing the condition function 
directly.
```python
from pyscan import *
# Acquired data is valid when "PYSCAN:TEST:VALID1" == 10
condition1 = epics_condition("PYSCAN:TEST:VALID1", 10)
# Acquired data is valid when 4 < "CAMERA1:VALID1" < 6
condition2 = bs_condition("CAMERA1:VALID1", 5, tolerance=1)
# bs condition with default value. See notes at the bottom of this chapter.
condition3 = bs_condition("CAMERA1:VALID2", 5, default_value="5")

# Function conditions need to return a boolean to signal if the scan can continue or not.
def i_always_fail():
    return False

condition4 = function_condition(i_always_fail)

# In this case, the condition is not defined with the function_condition call, so the condition action is ABORT (default).
def i_always_work():
    return True

conditions = [condition1, condition2, condition3, condition4, i_always_work]
```

When any of the condition fail (the condition value not match the specified one, or the function condition returns 
False), the scan is aborted or the data acquisition is done again once the condition becomes valid (based on the 
specified condition action).

It is important to note:

- Conditions do not use the epics monitoring feature, but do a caget every time
the value is requested. This is to ensure the most recent possible value is available to the condition.
- bsread conditions match the pulse id of the acquisition data pulse id. This guarantees that the condition matches
the pulse of the data acquisition.
- function conditions have to return True (continue scan) or False (stop scan).

**Default values**
In some cases, not all bs read properties are present in each stream message. In this case, the default behaviour is 
to raise an Exception with the missing property. This behaviour can be changed using the *default\_value* 
parameter of bs_condition. If specified, when values are missing the stream, the default value is used. The same 
logic applies to bs_property.

You can change the default behaviour for all bs_read properties by changing the config:
```python
from pyscan import config
# Instead of raising an exception, the default value for missing bs read properties is None.
config.bs_default_missing_property_value = None
```

<a id="c_init_and_fin"></a>
## Initialization and Finalization
The initialization and finalization actions are executed, respectively, before the first writables move and after the
last data acquisition. The finalization actions are always executed, also in case of scan abort. This methods are
useful for setting up scan related attributes, and for example restoring the original variable values. The most
common actions are already available in pyscan, but you can also provide your own method. The method must be without
arguments.

```python
from pyscan import *
# Just for demonstrating the writables restore.
writables = epics_pv("PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR1:GET")

# Before starting the scan, move the SLIT1 into the beam.
set_slit = action_set_epics_pv(pv_name="PYSCAN:TEST:SLIT1", value=1)

# Just to demonstrate the possibility to execute any provided method.
def notify_user():
    print("Slit inserted..")
# Execute the notify_user method specified above.
notify_slit_inserted = notify_user

# When the scan is completed, restore the pre-scan SLIT1 values.
restore_slit = action_restore(epics_pv(pv_name="PYSCAN:TEST:SLIT1"))
# When the scan is completed, restore the pre-scan writables values.
restore_writables = action_restore(writables)

initialization = [set_slit, notify_slit_inserted]
finalization = [restore_slit, restore_writables]
```

It is important to note:

- Actions are executed in the order they are provided. You must be careful if there are any inter-dependent variables
that must be set in a specific order.
- Methods you provide must have no call arguments, they can however be closures if you need access to function external
variables.

<a id="c_before_and_after"></a>
## Before and after executors
The before and after move action are executed before each move and after the motors have moved and the settling time 
for the motors has passed.

The before and after read action are execute before each measurement (after the writables moved), and right
after the measurements are finished. This actions can be used for user notifications, various verifications or
data storage preparations (for example setting a measurement header etc.).

Apart from the execution points, the same actions and behaviours described in the
[Initialization and Finalization](#init_and_fin) chapter apply. Consult that chapter for more information on usage.

<a id="c_scan_settings"></a>
## Scan settings
Settings allow to specify the scan parameters. They provide already some defaults which should work for the most
common scans. The available settings are:

- **measurement_interval** (Default: 0): In case we have n_measurements > 1, how much time to wait between each
measurement at a specific location.
- **n_measurements** (Default: 1): How many measurements should be done in each position.
- **write_timeout** (Default: 3): Time the motors have to reach their destination. This usually needs to be set in
accordance with the scan needs.
- **settling_time** (Default: 0): Time to wait **after** the motors have reached their destination.
- **progress_callback** (Default: print progress to console): Callback function to be invoked for progress updates.
The callback function should accept 2 positional parameters: **callback(current\_position, total\_positions)**

Settings are a single value of type SCAN_SETTINGS. SCAN_SETTINGS is a named tuple that can be generated
by invoking the method **scan_settings()**. You can define only the desired settings, others will be set to the
default value.

```python
from pyscan import *

# In each scan position, do 3 measurements with 10Hz frequency.
example_settings_1 = scan_settings(measurement_interval=0.1,
                                   n_measurements=3)

# Give the motors 10 seconds to reach their position, and wait 2 additional seconds after the
# position is reached.
example_settings_2 = scan_settings(write_timeout=10,
                                   settling_time=2)

def scan_progress(current_position, total_positions):
    """
    Print % of scan completeness to console.
    :param current_position: Index (1 based) of current position. Value is 0 before scan starts.
    :param total_positions: Total number of positions in this scan.
    """
    completed_percentage = 100 * (current_position/total_positions)
    print("Scan: %.2f %% completed (%d/%d)" % (completed_percentage, current_position, total_positions))

# Call the scan_progress function at the beginning and after every position is the scan.
example_settings_3 = scan_settings(progress_callback=scan_progress)
```

**Note**: The progress_callback function is executed in the same thread as the scan. Your function should not be
a long running one - in case you need to, for example, do an UI update, you should provide the appropriate threading
model yourself. Your callback function will in fact be blocking the scan until it completes.

<a id="c_scan_results"></a>
## Scan result
The scan results are given as a flat list, with each value position corresponding to the positions
defined in the readables. In case of multiple measurements, they are grouped together inside another list.

```python
# Dummy value initialization.
x1, x2, x3 = [1] * 3
y1, y2, y3 = [2] * 3
z1, z2, z3 = [3] * 3

from pyscan import *
# Scan at position 1, 2, and 3.
positioner = VectorPositioner([1, 2, 3])
# Define 3 readables: X, Y, Z.
readables = [epics_pv("X"), epics_pv("Y"), epics_pv("Z")]
# Define 1 writable motor
writables = epics_pv("MOTOR")
# Perform the scan.
result = scan(positioner, readables, writables)

# The result is a list, with a list of measurement for each position.
result == [[x1, y1, z1],
           [x2, y2, z2],
           [x3, y3, z3]]

# In case we want to do 2 measurements at each position.
result = scan(positioner, readables, writables, settings=scan_settings(n_measurements=2))

# The result is a list, with a list for each position, which again has a list for each measurement.
result == [[[x1, y1, z1], [x1, y1, z1]],
           [[x2, y2, z2], [x2, y2, z2]],
           [[x3, y3, z3], [x3, y3, z3]]]

# In case you have a single readable.
readables = epics_pv("X")
result = scan(positioner, readables, writables)

# The measurements are still wrapped in a list (with a single element, this time).
result == [[x1], [x2], [x3]]

# Scan with only 1 position, 1 motor, 1 readable.
positioner = VectorPositioner(1)
writables = epics_pv("MOTOR")
readables = epics_pv("X")
result = scan(positioner, readables, writables)

# The result is still wrapped in 2 lists. The reason is described in the note below.
result == [[x1]]
```

**Note**: The measurement result is always wrapped in a list (even if only 1 variable is acquired). This is needed
because external, processing code, can always rely on the fact that there will be an iterable object available, no
matter what the readables are. For the same reason, in a scan with a single readable, single position,
and 1 measurement, the output will still be wrapped in 2 lists: **\[\[measurement_result\]\]**

<a id="c_configuration"></a>
# Library configuration
Common library settings can be set in the **pyscan/config.py** module, either at run time or when deployed. Runtime
changes are preferable, since they do not affect other users.

For example, to change the bs_read connection address and port, execute:

```python
from pyscan import config
config.bs_default_host = "127.0.0.1"
config.bs_default_port = 9999
```

To get the list of available configurations check the module source or run:

```python
from pyscan import config
help(config)
```

**Warning**: Only in rare cases, if at all, this settings should be changed. Most strictly scan related parameters
can be configured using the [Scan settings](#scan_settings).

<a id="c_common_use_cases"></a>
# Common use cases

<a id="c_scanning_images_from_cam"></a>
## Scanning camera images from cam_server with camera_name

```python
from pyscan import *

# Disable logging
import logging
logging.getLogger("mflow.mflow").setLevel(logging.ERROR)

# Get current stream of local cam instance
from cam_server import PipelineClient
from cam_server.utils import get_host_port_from_stream_address

# Get the pipeline client instance.
pipeline_client = PipelineClient("http://sf-daqsync-01:8889/")

# Camera name to connect to.
camera_name = "simulation"

# Get the camera stream host and port.
_, stream_address = pipeline_client.create_instance_from_config({"camera_name": camera_name})
stream_host, stream_port = get_host_port_from_stream_address(stream_address)

# Configure bsread
config.bs_default_host = stream_host
config.bs_default_port = stream_port

positioner = StaticPositioner(5)  # Read 5 images
# Read x_axis and y_axis from bs stream -> in case the data is missing in a bs stream message, use None as default.
readables = [bs_property("x_axis", None), bs_property('y_axis', None)]

value = scan(positioner, readables)

print(value[0][0])  # Get first value of first readable
```

<a id="c_scanning_custom_sources"></a>
## Scanning with custom data sources
In addition to using the provided EPICS and BS DAL, you can provide your own data sources for readables, writables and 
coditions. In this case, you need to pass the method for retrieving, writing or checking the data yourself. This 
makes it also easy to mock (for testing purposes for example) hardware that currently does not exist.

```python
from pyscan import *

# Provide a function for reading a custom source.
def read_custom_source():
    nonlocal counter
    counter += 1
    print("Reading custom counter %d" % counter)
    return counter
counter = 0

# Provide a function for moving a custom motor.
def write_custom_motor(position):
    print("Moving motor to position %s" % position)

# Provide a function to verify a custom condition.
def verify_custom_condition():
    print("Confirming..")
    return True

n_images = 5
positioner = StaticPositioner(n_images=n_images)
readables = read_custom_source
writables = write_custom_motor
conditions = verify_custom_condition

# result == [[1], [2], [3], [4], [5]]
result = scan(positioner, readables, writables, conditions)
```

<a id="c_other_interfaces"></a>
# Other interfaces
**TBD**

<a id="c_pshell"></a>
## pshell
**TBD**

<a id="c_old_pyscan"></a>
## pyScan
**TBD**
