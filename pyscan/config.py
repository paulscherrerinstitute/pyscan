#########################
# General configuration #
#########################

# Minimum tolerance for comparing floats.
max_float_tolerance = 0.00001
# 1ms time tolerance for time critical measurements.
max_time_tolerance = 0.05

######################
# Scan configuration #
######################

# Default number of scans.
scan_default_n_measurements = 1
# Default interval between multiple measurements in a single position. Taken into account when n_measurements > 1.
scan_default_measurement_interval = 0
# Interval to sleep while the scan is paused.
scan_pause_sleep_interval = 0.1
# Maximum number of retries to read the channels to get valid data.
scan_acquisition_retry_limit = 3
# Delay between acquisition retries.
scan_acquisition_retry_delay = 1

############################
# BSREAD DAL configuration #
############################

# Queue size for collecting messages from bs_read.
bs_queue_size = 20
# Max time to wait until the bs read message we need arrives.
bs_read_timeout = 5
# Max time to wait for a message (if there is none). Important for stopping threads etc.
bs_receive_timeout = 1

# Default bs_read connection address.
bs_default_host = "localhost"
# Default bs_read connection port.
bs_default_port = 9999
# Default bs connection port.
bs_connection_mode = "sub"
# Default property value for bs properties missing in stream. Exception means to raise an Exception when this happens.
bs_default_missing_property_value = Exception

###########################
# EPICS DAL configuration #
###########################

# Default set and match timeout - how much time a PV has to reach the target value.
epics_default_set_and_match_timeout = 3
# After all motors have reached their destination (set_and_match), extra time to wait.
epics_default_settling_time = 0
