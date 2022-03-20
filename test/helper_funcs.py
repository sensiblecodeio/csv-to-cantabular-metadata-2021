import unittest.mock
import os
import io
import csv

def mock_open(*args, **kargs):
  f_open = unittest.mock.mock_open(*args, **kargs)
  f_open.return_value.__iter__ = lambda self : iter(self.readline, '')
  return f_open


BUILTINS_OPEN=open
def conditional_mock_open(filename, read_data):
    def func(*args, **kargs):
        if args and os.path.basename(args[0]) == filename:
            return mock_open(read_data=read_data)(*args, **kargs)
        return BUILTINS_OPEN(*args, **kargs)
    return func


def build_test_file(fieldnames, rows):
    csv_string = io.StringIO()
    writer = csv.DictWriter(csv_string, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return csv_string.getvalue()
