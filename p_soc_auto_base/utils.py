"""
.. _utils:

utility classes and functions for the p_soc_auto project

:module:    p_soc_auto.p_soc_auto_base.utils

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:update:    sep. 27, 2018

"""


def remove_duplicates(sequence=None):
    """
    remove duplicates from a sequence

    :arg sequence: the sequence that may be containing duplicates

    :returns: a ``list`` with no duplicate items
    """
    class IterableError(Exception):
        """
        raise when the input is not, or cannot be cast to, an iterable
        """

        def __init__(self, sequence):
            message = (
                '%s of type %s is not, or cannot be cast to, a sequence' %
                (sequence, type(sequence)))

            super().__init__(message)

    if sequence is None:
        raise IterableError(sequence)

    if not isinstance(sequence, (list, tuple)):
        try:
            sequence = [sequence]
        except Exception:
            raise IterableError(sequence)

    no_dup_sequence = []
    [no_dup_sequence.append(item)
     for item in sequence if item not in no_dup_sequence]

    return no_dup_sequence
