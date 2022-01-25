from libc.stdint cimport *
from libc.string cimport *

from pyrobuf_list cimport *
from pyrobuf_util cimport *

import base64
import json
import warnings

class DecodeError(Exception):
    pass

cdef class Token:

    def __cinit__(self):
        self._listener = noop_listener

    

    def __init__(self, **kwargs):
        self.reset()
        if kwargs:
            for field_name, field_value in kwargs.items():
                try:
                    setattr(self, field_name, field_value)
                except AttributeError:
                    raise ValueError('Protocol message has no "%s" field.' % (field_name,))
        return

    def __str__(self):
        fields = [
                          'user_id',
                          'project_id',
                          'methods',
                          'exp',]
        components = ['{0}: {1}'.format(field, getattr(self, field)) for field in fields]
        messages = []
        for message in messages:
            components.append('{0}: {{'.format(message))
            for line in str(getattr(self, message)).split('\n'):
                components.append('  {0}'.format(line))
            components.append('}')
        return '\n'.join(components)

    
    cpdef _user_id__reset(self):
        self._user_id = 0
        self.__field_bitmap0 &= ~1
    cpdef _project_id__reset(self):
        self._project_id = 0
        self.__field_bitmap0 &= ~2
    cpdef _methods__reset(self):
        self._methods = ""
        self.__field_bitmap0 &= ~4
    cpdef _exp__reset(self):
        self._exp = 0
        self.__field_bitmap0 &= ~8

    cpdef void reset(self):
        # reset values and populate defaults
    
        self._user_id__reset()
        self._project_id__reset()
        self._methods__reset()
        self._exp__reset()
        return

    
    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        self.__field_bitmap0 |= 1
        self._user_id = value
        self._Modified()
    
    @property
    def project_id(self):
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        self.__field_bitmap0 |= 2
        self._project_id = value
        self._Modified()
    
    @property
    def methods(self):
        return self._methods

    @methods.setter
    def methods(self, value):
        self.__field_bitmap0 |= 4
        if isinstance(value, bytes):
            self._methods = value.decode('utf-8')
        elif isinstance(value, str):
            self._methods = value
        else:
            raise TypeError("%r has type %s, but expected one of: (%s, %s)" % (value, type(value), bytes, str))
        self._Modified()
    
    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, value):
        self.__field_bitmap0 |= 8
        self._exp = value
        self._Modified()
    

    cdef int _protobuf_deserialize(self, const unsigned char *memory, int size, bint cache):
        cdef int current_offset = 0
        cdef int64_t key
        cdef int64_t field_size
        while current_offset < size:
            key = get_varint64(memory, &current_offset)
            # user_id
            if key == 8:
                self.__field_bitmap0 |= 1
                self._user_id = get_varint32(memory, &current_offset)
            # project_id
            elif key == 16:
                self.__field_bitmap0 |= 2
                self._project_id = get_varint32(memory, &current_offset)
            # methods
            elif key == 26:
                self.__field_bitmap0 |= 4
                field_size = get_varint64(memory, &current_offset)
                self._methods = str(memory[current_offset:current_offset + field_size], 'utf-8')
                current_offset += <int>field_size
            # exp
            elif key == 33:
                self.__field_bitmap0 |= 8
                self._exp = (<double *>&memory[current_offset])[0]
                current_offset += sizeof(double)
            # Unknown field - need to skip proper number of bytes
            else:
                assert skip_generic(memory, &current_offset, size, key & 0x7)

        self._is_present_in_parent = True

        return current_offset

    cpdef void Clear(self):
        """Clears all data that was set in the message."""
        self.reset()
        self._Modified()

    cpdef void ClearField(self, field_name):
        """Clears the contents of a given field."""
        self._clearfield(field_name)
        self._Modified()

    cdef void _clearfield(self, field_name):
        if field_name == 'user_id':
            self._user_id__reset()
        elif field_name == 'project_id':
            self._project_id__reset()
        elif field_name == 'methods':
            self._methods__reset()
        elif field_name == 'exp':
            self._exp__reset()
        else:
            raise ValueError('Protocol message has no "%s" field.' % field_name)

    cpdef void CopyFrom(self, Token other_msg):
        """
        Copies the content of the specified message into the current message.

        Params:
            other_msg (Token): Message to copy into the current one.
        """
        if self is other_msg:
            return
        self.reset()
        self.MergeFrom(other_msg)

    cpdef bint HasField(self, field_name) except -1:
        """
        Checks if a certain field is set for the message.

        Params:
            field_name (str): The name of the field to check.
        """
        if field_name == 'user_id':
            return self.__field_bitmap0 & 1 == 1
        if field_name == 'project_id':
            return self.__field_bitmap0 & 2 == 2
        if field_name == 'methods':
            return self.__field_bitmap0 & 4 == 4
        if field_name == 'exp':
            return self.__field_bitmap0 & 8 == 8
        raise ValueError('Protocol message has no singular "%s" field.' % field_name)

    cpdef bint IsInitialized(self):
        """
        Checks if the message is initialized.

        Returns:
            bool: True if the message is initialized (i.e. all of its required
                fields are set).
        """

    

        return True

    cpdef void MergeFrom(self, Token other_msg):
        """
        Merges the contents of the specified message into the current message.

        Params:
            other_msg: Message to merge into the current message.
        """

        if self is other_msg:
            return

    
        if other_msg.__field_bitmap0 & 1 == 1:
            self._user_id = other_msg._user_id
            self.__field_bitmap0 |= 1
        if other_msg.__field_bitmap0 & 2 == 2:
            self._project_id = other_msg._project_id
            self.__field_bitmap0 |= 2
        if other_msg.__field_bitmap0 & 4 == 4:
            self._methods = other_msg._methods
            self.__field_bitmap0 |= 4
        if other_msg.__field_bitmap0 & 8 == 8:
            self._exp = other_msg._exp
            self.__field_bitmap0 |= 8

        self._Modified()

    cpdef int MergeFromString(self, data, size=None) except -1:
        """
        Merges serialized protocol buffer data into this message.

        Params:
            data (bytes): a string of binary data.
            size (int): optional - the length of the data string

        Returns:
            int: the number of bytes processed during serialization
        """
        cdef int buf
        cdef int length

        length = size if size is not None else len(data)

        buf = self._protobuf_deserialize(data, length, False)

        if buf != length:
            raise DecodeError("Truncated message: got %s expected %s" % (buf, size))

        self._Modified()

        return buf

    cpdef int ParseFromString(self, data, size=None, bint reset=True, bint cache=False) except -1:
        """
        Populate the message class from a string of protobuf encoded binary data.

        Params:
            data (bytes): a string of binary data
            size (int): optional - the length of the data string
            reset (bool): optional - whether to reset to default values before serializing
            cache (bool): optional - whether to cache serialized data

        Returns:
            int: the number of bytes processed during serialization
        """
        cdef int buf
        cdef int length

        length = size if size is not None else len(data)

        if reset:
            self.reset()

        buf = self._protobuf_deserialize(data, length, cache)

        if buf != length:
            raise DecodeError("Truncated message")

        self._Modified()

        if cache:
            self._cached_serialization = data

        return buf

    @classmethod
    def FromString(cls, s):
        message = cls()
        message.MergeFromString(s)
        return message

    cdef void _protobuf_serialize(self, bytearray buf, bint cache):
        # user_id
        if self.__field_bitmap0 & 1 == 1:
            set_varint64(8, buf)
            set_varint32(self._user_id, buf)
        # project_id
        if self.__field_bitmap0 & 2 == 2:
            set_varint64(16, buf)
            set_varint32(self._project_id, buf)
        # methods
        cdef bytes methods_bytes
        if self.__field_bitmap0 & 4 == 4:
            set_varint64(26, buf)
            methods_bytes = self._methods.encode('utf-8')
            set_varint64(len(methods_bytes), buf)
            buf += methods_bytes
        # exp
        if self.__field_bitmap0 & 8 == 8:
            set_varint64(33, buf)
            buf += (<unsigned char *>&self._exp)[:sizeof(double)]

    cpdef void _Modified(self):
        self._is_present_in_parent = True
        self._listener()
        self._cached_serialization = None

    

    cpdef bytes SerializeToString(self, bint cache=False):
        """
        Serialize the message class into a string of protobuf encoded binary data.

        Returns:
            bytes: a byte string of binary data
        """

    

        if self._cached_serialization is not None:
            return self._cached_serialization

        cdef bytearray buf = bytearray()
        self._protobuf_serialize(buf, cache)
        cdef bytes out = bytes(buf)

        if cache:
            self._cached_serialization = out

        return out

    cpdef bytes SerializePartialToString(self):
        """
        Serialize the message class into a string of protobuf encoded binary data.

        Returns:
            bytes: a byte string of binary data
        """
        if self._cached_serialization is not None:
            return self._cached_serialization

        cdef bytearray buf = bytearray()
        self._protobuf_serialize(buf, False)
        return bytes(buf)

    def SetInParent(self):
        """
        Mark this an present in the parent.
        """
        self._Modified()

    def ParseFromJson(self, data, size=None, reset=True):
        """
        Populate the message class from a json string.

        Params:
            data (str): a json string
            size (int): optional - the length of the data string
            reset (bool): optional - whether to reset to default values before serializing
        """
        if size is None:
            size = len(data)
        d = json.loads(data[:size])
        self.ParseFromDict(d, reset)

    def SerializeToJson(self, **kwargs):
        """
        Serialize the message class into a json string.

        Returns:
            str: a json formatted string
        """
        d = self.SerializeToDict()
        return json.dumps(d, **kwargs)

    def SerializePartialToJson(self, **kwargs):
        """
        Serialize the message class into a json string.

        Returns:
            str: a json formatted string
        """
        d = self.SerializePartialToDict()
        return json.dumps(d, **kwargs)

    def ParseFromDict(self, d, reset=True):
        """
        Populate the message class from a Python dictionary.

        Params:
            d (dict): a Python dictionary representing the message
            reset (bool): optional - whether to reset to default values before serializing
        """
        if reset:
            self.reset()

        assert type(d) == dict
        try:
            self.user_id = d["user_id"]
        except KeyError:
            pass
        try:
            self.project_id = d["project_id"]
        except KeyError:
            pass
        try:
            self.methods = d["methods"]
        except KeyError:
            pass
        try:
            self.exp = d["exp"]
        except KeyError:
            pass

        self._Modified()

        return

    def SerializeToDict(self):
        """
        Translate the message into a Python dictionary.

        Returns:
            dict: a Python dictionary representing the message
        """
        out = {}
        if self.__field_bitmap0 & 1 == 1:
            out["user_id"] = self.user_id
        if self.__field_bitmap0 & 2 == 2:
            out["project_id"] = self.project_id
        if self.__field_bitmap0 & 4 == 4:
            out["methods"] = self.methods
        if self.__field_bitmap0 & 8 == 8:
            out["exp"] = self.exp

        return out

    def SerializePartialToDict(self):
        """
        Translate the message into a Python dictionary.

        Returns:
            dict: a Python dictionary representing the message
        """
        out = {}
        if self.__field_bitmap0 & 1 == 1:
            out["user_id"] = self.user_id
        if self.__field_bitmap0 & 2 == 2:
            out["project_id"] = self.project_id
        if self.__field_bitmap0 & 4 == 4:
            out["methods"] = self.methods
        if self.__field_bitmap0 & 8 == 8:
            out["exp"] = self.exp

        return out

    def Items(self):
        """
        Iterator over the field names and values of the message.

        Returns:
            iterator
        """
        yield 'user_id', self.user_id
        yield 'project_id', self.project_id
        yield 'methods', self.methods
        yield 'exp', self.exp

    def Fields(self):
        """
        Iterator over the field names of the message.

        Returns:
            iterator
        """
        yield 'user_id'
        yield 'project_id'
        yield 'methods'
        yield 'exp'

    def Values(self):
        """
        Iterator over the values of the message.

        Returns:
            iterator
        """
        yield self.user_id
        yield self.project_id
        yield self.methods
        yield self.exp

    

    def Setters(self):
        """
        Iterator over functions to set the fields in a message.

        Returns:
            iterator
        """
        def setter(value):
            self.user_id = value
        yield setter
        def setter(value):
            self.project_id = value
        yield setter
        def setter(value):
            self.methods = value
        yield setter
        def setter(value):
            self.exp = value
        yield setter

    
