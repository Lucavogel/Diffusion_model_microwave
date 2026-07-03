# generated from rosidl_generator_py/resource/_idl.py.em
# with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_OnRobotRGInput(type):
    """Metaclass of message 'OnRobotRGInput'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('onrobot_rg_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'onrobot_rg_msgs.msg.OnRobotRGInput')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__on_robot_rg_input
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__on_robot_rg_input
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__on_robot_rg_input
            cls._TYPE_SUPPORT = module.type_support_msg__msg__on_robot_rg_input
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__on_robot_rg_input

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class OnRobotRGInput(metaclass=Metaclass_OnRobotRGInput):
    """Message class 'OnRobotRGInput'."""

    __slots__ = [
        '_g_fof',
        '_g_gwd',
        '_g_sta',
        '_g_wdf',
        '_sta_fing_l',
        '_sta_fing_r',
        '_sta_prox_l',
        '_sta_prox_r',
        '_busy',
        '_grip_det',
        '_prox_off_l',
        '_prox_off_r',
        '_fx_l',
        '_fy_l',
        '_fz_l',
        '_tx_l',
        '_ty_l',
        '_tz_l',
        '_fx_r',
        '_fy_r',
        '_fz_r',
        '_tx_r',
        '_ty_r',
        '_tz_r',
        '_prox_l',
        '_prox_r',
        '_grip_width',
        '_in_zero',
    ]

    _fields_and_field_types = {
        'g_fof': 'uint16',
        'g_gwd': 'uint16',
        'g_sta': 'uint16',
        'g_wdf': 'uint16',
        'sta_fing_l': 'uint16',
        'sta_fing_r': 'uint16',
        'sta_prox_l': 'uint16',
        'sta_prox_r': 'uint16',
        'busy': 'uint16',
        'grip_det': 'uint16',
        'prox_off_l': 'uint16',
        'prox_off_r': 'uint16',
        'fx_l': 'int32',
        'fy_l': 'int32',
        'fz_l': 'int32',
        'tx_l': 'int32',
        'ty_l': 'int32',
        'tz_l': 'int32',
        'fx_r': 'int32',
        'fy_r': 'int32',
        'fz_r': 'int32',
        'tx_r': 'int32',
        'ty_r': 'int32',
        'tz_r': 'int32',
        'prox_l': 'int32',
        'prox_r': 'int32',
        'grip_width': 'int32',
        'in_zero': 'int8',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.g_fof = kwargs.get('g_fof', int())
        self.g_gwd = kwargs.get('g_gwd', int())
        self.g_sta = kwargs.get('g_sta', int())
        self.g_wdf = kwargs.get('g_wdf', int())
        self.sta_fing_l = kwargs.get('sta_fing_l', int())
        self.sta_fing_r = kwargs.get('sta_fing_r', int())
        self.sta_prox_l = kwargs.get('sta_prox_l', int())
        self.sta_prox_r = kwargs.get('sta_prox_r', int())
        self.busy = kwargs.get('busy', int())
        self.grip_det = kwargs.get('grip_det', int())
        self.prox_off_l = kwargs.get('prox_off_l', int())
        self.prox_off_r = kwargs.get('prox_off_r', int())
        self.fx_l = kwargs.get('fx_l', int())
        self.fy_l = kwargs.get('fy_l', int())
        self.fz_l = kwargs.get('fz_l', int())
        self.tx_l = kwargs.get('tx_l', int())
        self.ty_l = kwargs.get('ty_l', int())
        self.tz_l = kwargs.get('tz_l', int())
        self.fx_r = kwargs.get('fx_r', int())
        self.fy_r = kwargs.get('fy_r', int())
        self.fz_r = kwargs.get('fz_r', int())
        self.tx_r = kwargs.get('tx_r', int())
        self.ty_r = kwargs.get('ty_r', int())
        self.tz_r = kwargs.get('tz_r', int())
        self.prox_l = kwargs.get('prox_l', int())
        self.prox_r = kwargs.get('prox_r', int())
        self.grip_width = kwargs.get('grip_width', int())
        self.in_zero = kwargs.get('in_zero', int())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.g_fof != other.g_fof:
            return False
        if self.g_gwd != other.g_gwd:
            return False
        if self.g_sta != other.g_sta:
            return False
        if self.g_wdf != other.g_wdf:
            return False
        if self.sta_fing_l != other.sta_fing_l:
            return False
        if self.sta_fing_r != other.sta_fing_r:
            return False
        if self.sta_prox_l != other.sta_prox_l:
            return False
        if self.sta_prox_r != other.sta_prox_r:
            return False
        if self.busy != other.busy:
            return False
        if self.grip_det != other.grip_det:
            return False
        if self.prox_off_l != other.prox_off_l:
            return False
        if self.prox_off_r != other.prox_off_r:
            return False
        if self.fx_l != other.fx_l:
            return False
        if self.fy_l != other.fy_l:
            return False
        if self.fz_l != other.fz_l:
            return False
        if self.tx_l != other.tx_l:
            return False
        if self.ty_l != other.ty_l:
            return False
        if self.tz_l != other.tz_l:
            return False
        if self.fx_r != other.fx_r:
            return False
        if self.fy_r != other.fy_r:
            return False
        if self.fz_r != other.fz_r:
            return False
        if self.tx_r != other.tx_r:
            return False
        if self.ty_r != other.ty_r:
            return False
        if self.tz_r != other.tz_r:
            return False
        if self.prox_l != other.prox_l:
            return False
        if self.prox_r != other.prox_r:
            return False
        if self.grip_width != other.grip_width:
            return False
        if self.in_zero != other.in_zero:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def g_fof(self):
        """Message field 'g_fof'."""
        return self._g_fof

    @g_fof.setter
    def g_fof(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'g_fof' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'g_fof' field must be an unsigned integer in [0, 65535]"
        self._g_fof = value

    @builtins.property
    def g_gwd(self):
        """Message field 'g_gwd'."""
        return self._g_gwd

    @g_gwd.setter
    def g_gwd(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'g_gwd' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'g_gwd' field must be an unsigned integer in [0, 65535]"
        self._g_gwd = value

    @builtins.property
    def g_sta(self):
        """Message field 'g_sta'."""
        return self._g_sta

    @g_sta.setter
    def g_sta(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'g_sta' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'g_sta' field must be an unsigned integer in [0, 65535]"
        self._g_sta = value

    @builtins.property
    def g_wdf(self):
        """Message field 'g_wdf'."""
        return self._g_wdf

    @g_wdf.setter
    def g_wdf(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'g_wdf' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'g_wdf' field must be an unsigned integer in [0, 65535]"
        self._g_wdf = value

    @builtins.property
    def sta_fing_l(self):
        """Message field 'sta_fing_l'."""
        return self._sta_fing_l

    @sta_fing_l.setter
    def sta_fing_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'sta_fing_l' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'sta_fing_l' field must be an unsigned integer in [0, 65535]"
        self._sta_fing_l = value

    @builtins.property
    def sta_fing_r(self):
        """Message field 'sta_fing_r'."""
        return self._sta_fing_r

    @sta_fing_r.setter
    def sta_fing_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'sta_fing_r' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'sta_fing_r' field must be an unsigned integer in [0, 65535]"
        self._sta_fing_r = value

    @builtins.property
    def sta_prox_l(self):
        """Message field 'sta_prox_l'."""
        return self._sta_prox_l

    @sta_prox_l.setter
    def sta_prox_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'sta_prox_l' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'sta_prox_l' field must be an unsigned integer in [0, 65535]"
        self._sta_prox_l = value

    @builtins.property
    def sta_prox_r(self):
        """Message field 'sta_prox_r'."""
        return self._sta_prox_r

    @sta_prox_r.setter
    def sta_prox_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'sta_prox_r' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'sta_prox_r' field must be an unsigned integer in [0, 65535]"
        self._sta_prox_r = value

    @builtins.property
    def busy(self):
        """Message field 'busy'."""
        return self._busy

    @busy.setter
    def busy(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'busy' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'busy' field must be an unsigned integer in [0, 65535]"
        self._busy = value

    @builtins.property
    def grip_det(self):
        """Message field 'grip_det'."""
        return self._grip_det

    @grip_det.setter
    def grip_det(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'grip_det' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'grip_det' field must be an unsigned integer in [0, 65535]"
        self._grip_det = value

    @builtins.property
    def prox_off_l(self):
        """Message field 'prox_off_l'."""
        return self._prox_off_l

    @prox_off_l.setter
    def prox_off_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'prox_off_l' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'prox_off_l' field must be an unsigned integer in [0, 65535]"
        self._prox_off_l = value

    @builtins.property
    def prox_off_r(self):
        """Message field 'prox_off_r'."""
        return self._prox_off_r

    @prox_off_r.setter
    def prox_off_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'prox_off_r' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'prox_off_r' field must be an unsigned integer in [0, 65535]"
        self._prox_off_r = value

    @builtins.property
    def fx_l(self):
        """Message field 'fx_l'."""
        return self._fx_l

    @fx_l.setter
    def fx_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fx_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fx_l' field must be an integer in [-2147483648, 2147483647]"
        self._fx_l = value

    @builtins.property
    def fy_l(self):
        """Message field 'fy_l'."""
        return self._fy_l

    @fy_l.setter
    def fy_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fy_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fy_l' field must be an integer in [-2147483648, 2147483647]"
        self._fy_l = value

    @builtins.property
    def fz_l(self):
        """Message field 'fz_l'."""
        return self._fz_l

    @fz_l.setter
    def fz_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fz_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fz_l' field must be an integer in [-2147483648, 2147483647]"
        self._fz_l = value

    @builtins.property
    def tx_l(self):
        """Message field 'tx_l'."""
        return self._tx_l

    @tx_l.setter
    def tx_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'tx_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'tx_l' field must be an integer in [-2147483648, 2147483647]"
        self._tx_l = value

    @builtins.property
    def ty_l(self):
        """Message field 'ty_l'."""
        return self._ty_l

    @ty_l.setter
    def ty_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'ty_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'ty_l' field must be an integer in [-2147483648, 2147483647]"
        self._ty_l = value

    @builtins.property
    def tz_l(self):
        """Message field 'tz_l'."""
        return self._tz_l

    @tz_l.setter
    def tz_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'tz_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'tz_l' field must be an integer in [-2147483648, 2147483647]"
        self._tz_l = value

    @builtins.property
    def fx_r(self):
        """Message field 'fx_r'."""
        return self._fx_r

    @fx_r.setter
    def fx_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fx_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fx_r' field must be an integer in [-2147483648, 2147483647]"
        self._fx_r = value

    @builtins.property
    def fy_r(self):
        """Message field 'fy_r'."""
        return self._fy_r

    @fy_r.setter
    def fy_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fy_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fy_r' field must be an integer in [-2147483648, 2147483647]"
        self._fy_r = value

    @builtins.property
    def fz_r(self):
        """Message field 'fz_r'."""
        return self._fz_r

    @fz_r.setter
    def fz_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'fz_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'fz_r' field must be an integer in [-2147483648, 2147483647]"
        self._fz_r = value

    @builtins.property
    def tx_r(self):
        """Message field 'tx_r'."""
        return self._tx_r

    @tx_r.setter
    def tx_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'tx_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'tx_r' field must be an integer in [-2147483648, 2147483647]"
        self._tx_r = value

    @builtins.property
    def ty_r(self):
        """Message field 'ty_r'."""
        return self._ty_r

    @ty_r.setter
    def ty_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'ty_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'ty_r' field must be an integer in [-2147483648, 2147483647]"
        self._ty_r = value

    @builtins.property
    def tz_r(self):
        """Message field 'tz_r'."""
        return self._tz_r

    @tz_r.setter
    def tz_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'tz_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'tz_r' field must be an integer in [-2147483648, 2147483647]"
        self._tz_r = value

    @builtins.property
    def prox_l(self):
        """Message field 'prox_l'."""
        return self._prox_l

    @prox_l.setter
    def prox_l(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'prox_l' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'prox_l' field must be an integer in [-2147483648, 2147483647]"
        self._prox_l = value

    @builtins.property
    def prox_r(self):
        """Message field 'prox_r'."""
        return self._prox_r

    @prox_r.setter
    def prox_r(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'prox_r' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'prox_r' field must be an integer in [-2147483648, 2147483647]"
        self._prox_r = value

    @builtins.property
    def grip_width(self):
        """Message field 'grip_width'."""
        return self._grip_width

    @grip_width.setter
    def grip_width(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'grip_width' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'grip_width' field must be an integer in [-2147483648, 2147483647]"
        self._grip_width = value

    @builtins.property
    def in_zero(self):
        """Message field 'in_zero'."""
        return self._in_zero

    @in_zero.setter
    def in_zero(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'in_zero' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'in_zero' field must be an integer in [-128, 127]"
        self._in_zero = value
