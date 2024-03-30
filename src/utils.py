import string
from datetime import datetime


class Utils:

    MainLoopStep: float = 0.1

    @staticmethod
    def log(msg: string) -> None:
        print(str(datetime.now()) + " " + msg)
    
    @staticmethod
    def truncate(a_string: str, max_len:int):
        '''Truncates a string to a defined number of chars or returns "---" if its None'''
        if a_string is None:
            return '---'
        return (a_string[:max_len - 2] + '..') if len(a_string) > max_len else a_string