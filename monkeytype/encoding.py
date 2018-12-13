# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import json
import logging

from typing import (
    Any,
    Callable,
    Dict,
    Union,
    Iterable,
    Optional,
    Type,
    TypeVar,
    Tuple, NewType)

from monkeytype.compat import is_any, is_union, is_generic, qualname_of_generic
from monkeytype.db.base import CallTraceThunk
from monkeytype.exceptions import InvalidTypeError
from monkeytype.tracing import CallTrace, TypeDetails
from monkeytype.typing import NoneType
from monkeytype.util import (
    get_func_in_module,
    get_name_in_module,
)

logger = logging.getLogger(__name__)

# Types are converted to dictionaries of the following form before
# being JSON encoded and sent to storage:
#
#     {
#         'module': '<module>',
#         'qualname': '<qualname>',
#         'elem_types': [type_dict],
#     }
#
# The corresponding type alias should actually be
#
#     TypeDict = Dict[str, Union[str, TypeDict]]
#
# (or better, a TypedDict) but mypy does not support recursive type aliases:
#  https://github.com/python/mypy/issues/731
TypeDict = Dict[str, Any]


def type_to_dict(typ: type, typ_detail: Optional[TypeDetails] = None) -> TypeDict:
    """Convert a type into a dictionary representation that we can store.

    The dictionary must:
        1. Be encodable as JSON
        2. Contain enough information to let us reify the type
    """
    # Union and Any are special cases that aren't actually types.
    if is_union(typ):
        qualname = 'Union'
    elif is_any(typ):
        qualname = 'Any'
    elif is_generic(typ):
        qualname = qualname_of_generic(typ)
    else:
        qualname = typ.__qualname__
    d: TypeDict = {
        'module': typ.__module__,
        'qualname': qualname,
    }
    elem_types = getattr(typ, '__args__', None)
    if elem_types and is_generic(typ):
        d['elem_types'] = [type_to_dict(t) for t in elem_types]
    return d


_HIDDEN_BUILTIN_TYPES: Dict[str, type] = {
    # NoneType is only accessible via type(None)
    'NoneType': NoneType,
}


def type_from_dict(d: TypeDict) -> Tuple[type, Optional[TypeDetails]]:
    """Given a dictionary produced by type_to_dict, return the equivalent type.

    Raises:
        NameLookupError if we can't reify the specified type
        InvalidTypeError if the named type isn't actually a type
    """
    module, qualname = d['module'], d['qualname']
    if module == 'builtins' and qualname in _HIDDEN_BUILTIN_TYPES:
        typ = _HIDDEN_BUILTIN_TYPES[qualname]
    else:
        typ = get_name_in_module(module, qualname)
    if not (
            isinstance(typ, type) or
            is_any(typ) or
            is_generic(typ)
    ):
        raise InvalidTypeError(
            f"Attribute specified by '{qualname}' in module '{module}' "
            f"is of type {type(typ)}, not type."
        )
    elem_type_dicts = d.get('elem_types')
    if elem_type_dicts and is_generic(typ):
        elem_types = tuple(type_from_dict(e) for e in elem_type_dicts)
        # mypy complains that a value of type `type` isn't indexable. That's
        # true, but we know typ is a subtype that is indexable. Even checking
        # with hasattr(typ, '__getitem__') doesn't help
        typ = typ[elem_types]  # type: ignore
    return typ, d.get('type_detailss')


def type_to_json(typ: type, type_details: Optional[TypeDetails]) -> str:
    """Encode the supplied type as json using type_to_dict."""
    type_dict = type_to_dict(typ, type_details)
    return json.dumps(type_dict, sort_keys=True)
    # return type_dict


def type_from_json(typ_json: str) -> Tuple[type, Optional[TypeDetails]]:
    """Reify a type from the format produced by type_to_json."""
    type_dict = json.loads(typ_json)
    return type_from_dict(type_dict)


def arg_types_to_json(arg_types: Dict[str, type]) -> str:
    """Encode the supplied argument types as json"""
    type_dict = {name: type_to_dict(typ) for name, typ in arg_types.items()}
    return json.dumps(type_dict, sort_keys=True)


def arg_types_and_details_from_json(arg_types_json: str) -> Dict[str, Tuple[type, Optional[TypeDetails]]]:
    """Reify the encoded argument types from the format produced by arg_types_to_json."""
    arg_types = json.loads(arg_types_json)
    return {name: type_from_dict(type_dict) for name, type_dict in arg_types.items()}


TypeEncoder = Callable[[type, Optional[TypeDetails]], str]


def maybe_encode_type(encode: TypeEncoder, typ: Optional[type],
                      typ_details: Optional[TypeDetails]) -> Optional[str]:
    if typ is None:
        return None

    return encode(typ, typ_details)


TypeDecoder = Callable[[str], Optional[Tuple[type, Optional[TypeDetails]]]]


def maybe_decode_type(decode: TypeDecoder, encoded: Optional[str]) -> Optional[
    Tuple[type, Optional[TypeDetails]]]:
    if (encoded is None) or (encoded == 'null'):
        return None
    return decode(encoded)


def infer_data_types(var_traces: Dict[str, Any]) -> Union[Dict[Any, Any], type]:
    if isinstance(var_traces, dict):
        return {k: infer_data_types(v) if isinstance(v, dict) else type(v) for k, v in
                var_traces.items()}
    return type(var_traces)


CallTraceRowT = TypeVar('CallTraceRowT', bound='CallTraceRow')


class CallTraceRow(CallTraceThunk):
    """A semi-structured call trace where each field has been json encoded."""

    def __init__(
            self,
            module: str,
            qualname: str,
            arg_types: str,
            return_type: Optional[str],
            yield_type: Optional[str],
            return_type_detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.module = module
        self.qualname = qualname
        self.arg_types = arg_types
        self.return_type = return_type
        self.yield_type = yield_type
        self.return_type_detail = return_type_detail

    @classmethod
    def from_trace(cls: Type[CallTraceRowT], trace: CallTrace) -> CallTraceRowT:
        return cls(
            module=trace.func.__module__,
            qualname=trace.func.__qualname__,
            arg_types=arg_types_to_json(trace.arg_types),
            return_type=maybe_encode_type(
                type_to_json,
                trace.return_type,
                trace.return_type_detail,
            ),
            yield_type=maybe_encode_type(
                type_to_json,
                trace.yield_type,
                trace.yield_type_detail,
            ),
        )

    def to_trace(self) -> CallTrace:
        function = get_func_in_module(self.module, self.qualname)
        (arg_types, arg_type_detail) = arg_types_and_details_from_json(self.arg_types)
        (return_type, return_type_detail) = maybe_decode_type(type_from_json, self.return_type) \
            or (None, None)

        (yield_type, yield_type_detail) = maybe_decode_type(type_from_json, self.yield_type) \
            or (None, None)

        return CallTrace(
            func=function,
            arg_types=arg_types,
            return_type=return_type,
            return_type_detail=return_type_detail,
            yield_type=yield_type,
            yield_type_detail=yield_type_detail,
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CallTraceRow):
            return (
                       self.module,
                       self.qualname,
                       self.arg_types,
                       self.return_type,
                       self.yield_type,
                   ) == (
                       other.module,
                       other.qualname,
                       other.arg_types,
                       other.return_type,
                       other.yield_type,
                   )
        return NotImplemented


def serialize_traces(traces: Iterable[CallTrace]) -> Iterable[CallTraceRow]:
    """Serialize an iterable of CallTraces to an iterable of CallTraceRow.

    Catches and logs exceptions, so a failure to serialize one CallTrace doesn't
    lose all traces.

    """
    for trace in traces:
        try:
            yield CallTraceRow.from_trace(trace)
        except Exception:
            logger.exception("Failed to serialize trace")
