from pyscan.positioner.vector import VectorPositioner
from pyscan.scan import scan
from pyscan.scan_parameters import epics_pv, bs_property, epics_monitor, bs_monitor, action_set_epics_pv, \
    action_restore, scan_settings

positioner = VectorPositioner([1, 2, 3, 4])

writables = [epics_pv("PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR1:GET"),
             epics_pv("PYSCAN:TEST:MOTOR2:SET", "PYSCAN:TEST:MOTOR2:GET")]

readables = [bs_property("CAMERA1:X"),
             bs_property("CAMERA1:y"),
             epics_pv("PYSCAN:TEST:OBS1")]

monitors = [epics_monitor("PYSCAN:TEST:VALID1", 10),
            bs_monitor("CAMERA1:VALID", 10)]

initialization = [action_set_epics_pv("PYSCAN:TEST:PRE1:SET", 1, "PYSCAN:TEST:PRE1:GET")]

finalization = [action_set_epics_pv("PYSCAN:TEST:PRE1:SET", 0, "PYSCAN:TEST:PRE1:GET"),
                action_restore()]

result = scan(positioner=positioner,
              writables=writables,
              readables=readables,
              monitors=monitors,
              initializations=initialization,
              finalizations=finalization,
              settings=scan_settings(measurement_interval=0.25,
                                     n_measurements=3))
