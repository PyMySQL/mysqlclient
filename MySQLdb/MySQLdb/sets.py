"""sets module

This module provides some Set classes for dealing with MySQL data.
"""

class Set:

    """A simple class for handling sets. Sets are immutable in the same
    way numbers are."""
    
    def __init__(self, *values):
        """Use values to initialize the Set."""
        self._values = values

    def __contains__(self, value):
        return value in self._values and 1 or 0
    
    def __str__(self):
        """Returns the values as a comma-separated string."""
        return ','.join([ str(x) for x in self._values])

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, `self._values`)
    
    def __or__(self, other):
        """Union."""
        values = list(self._values)
        if isinstance(other, Set):
            for v in other._values:
                if v not in values:
                    values.append(v)
        elif other not in self._values:
            values.append(other)
        return self.__class__(*values)

    __add__ = __or__
    
    def __sub__(self, other):
        values = list(self._values)
        if isinstance(other, Set):
            for v in other._values:
                if v in values:
                    values.remove(v)
        elif other in self:
            values.remove(other)
        return self.__class__(*values)

    def __and__(self, other):
        "Intersection."
        values = []
        if isinstance(other, Set):
            for v in self._values:
                if v in other:
                    values.append(v)
        elif other in self:
            values.append(other)
        return self.__class__(*values)

    __mul__ = __and__
    
    def __xor__(self, other):
        "Intersection's complement."
        return (self|other)-(self&other)

    def __getitem__(self, n):
        return self._values[n]

    def __getslice__(self, n1, n2):
        return self._values[n1:n2]
    
    def __len__(self):
        return len(self._values)
    
    def __hash__(self):
        return hash(self._values)
    
    def __cmp__(self, other):
        if isinstance(other, Set):
            if not self ^ other:
                return 0
            elif self & other == self:
                return 1
            else:
                return -1
        elif other in self._values:
            return 0
        elif other > self._values:
            return 1
        else:
            return -1

    # rich comparison operators for Python 2.1 and up

    def __ne__(self, other):
        return self ^ other
    
    def __eq__(self, other):
        if not self != other:
            return self
        else:
            return self.__class__()
    
    def __le__(self, other):
        return self & other == self

    def __lt__(self, other):
        if self <= other and self ^ other:
            return self
        else:
            return self.__class__()

    def __ge__(self, other):
        return self & other == other

    def __gt__(self, other):
        if self >= other and self ^ other:
            return self
        else:
            return self.__class__()
    

class DBAPISet(Set):

    """A special type of set for which A == x is true if A is a
    DBAPISet and x is a member of that set."""

    # Note that Set.__cmp__ works perfectly well in this case, if
    # we are using < Python 2.1. It's just broken for <, >, etc.
    
    def __ne__(self, other):
        if isinstance(other, Set): # yes, Set
            return self % other
        elif other in self._values:
            return 0
        else:
            return 1

    def __eq__(self, other):
        if self != other:
            return self.__class__()
        else:
            return self
