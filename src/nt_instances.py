import ntcore
import constants

nt_instance = ntcore.NetworkTableInstance.create()
if constants.DO_SIM:
    nt_instance_sim = ntcore.NetworkTableInstance.create()