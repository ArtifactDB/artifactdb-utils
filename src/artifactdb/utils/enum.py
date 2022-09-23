# pylint: disable=no-value-for-parameter
import enum

class MetaEnum(enum.EnumMeta):

    def __contains__(cls, x):
        try:
            cls(x)
            return True
        except ValueError:
            return False


class Enum(enum.Enum, metaclass=MetaEnum):
    pass
