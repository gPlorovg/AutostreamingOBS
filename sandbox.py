import sys
import os


# path = input()
# print(path)

PYTHON_PATH = sys.executable.rstrip("python.exe")
WORK_DIRECTORY = os.getcwd() + "\\"
print(PYTHON_PATH)
print(WORK_DIRECTORY)
# escape_dict = {"\a": "\\a",
#                 "\b": "\\b",
#                 "\f": "\\f",
#                 "\n": "\\n",
#                 "\r": "\\r",
#                 "\t": "\\t",
#                 "\v": "\\v",
#                 "\0": "\\0",
#                 "\1": "\\1",
#                 "\2": "\\2",
#                 "\3": "\\3",
#                 "\4": "\\4",
#                 "\5": "\\5",
#                 "\6": "\\6",
#                 "\7": "\\7"}
#
# print(path.translate(escape_dict))