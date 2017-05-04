#########################
# general configuration #
#########################

# Minimum tolerance for comparing numbers.
min_tolerance = 0.00001

############################
# BSREAD DAL configuration #
############################

bs_default_n_measurements = 1
# Number of second
bs_default_waiting = 0
bs_default_queue_size = 20
bs_default_read_timeout = 5
bs_default_receive_timeout = 1

###########################
# EPICS DAL configuration #
###########################

epics_default_read_write_timeout = 3
epics_default_monitor_timeout = 3

#########################
# Scanner configuration #
#########################

# Interval to sleep while in pause.
pause_sleep_interval = 1
# Maximum number of times we wait to retry the acquisition.
acquisition_retry_limit = 3
# Delay between acquisition retries.
acquisition_retry_delay = 1
