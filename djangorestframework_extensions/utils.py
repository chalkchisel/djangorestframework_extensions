def user_passes_test(user, test):
    if test is None:  # A key of None serves as a 'catchall'
        return True
    elif isinstance(test, basestring):  # A string key indicates a group name
        if user.groups.filter(name=test).exists():
            return True
    elif callable(test):  # A callable implies a test to be run
        return test(user)
    return False
