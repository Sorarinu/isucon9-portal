

##############
# BenchQueue #
##############

class DuplicateJobError(Exception):
    """キューに重複してジョブが登録された際に発生する例外"""
    pass

class TeamServerDoesNotExistError(Exception):
    """チームのサーバが見つからない際に発生する例外"""
    pass

class JobDoesNotExistError(Exception):
    """指定されたjob_idのジョブが見つからない際に発生する例外"""
    pass
