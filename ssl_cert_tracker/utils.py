#!/usr/bin/env python

from datetime import datetime

def validate(date_text):
    """check if date_text is a valid date  """
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except TypeError:
        return False
    except ValueError:
        return False