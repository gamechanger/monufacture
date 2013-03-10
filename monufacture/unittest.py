from monufacture import cleanup

def enable_factories(testcase):
    testcase.addCleanup(cleanup)
