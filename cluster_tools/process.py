from exceptions import ProcessError

import subprocess


def call(args):
    process = subprocess.Popen(args=args,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if (0 == process.returncode):
        return out
    else:
        raise ProcessError(args, err, process.returncode)
