import typing

import inspect

forbidden_keys = set([
    'parent_file_name',
    'typed_dict_proxy_name',
])

import collections


class TypedDictProxy(dict):

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, TypedDictProxy):
            return False
        return self.dict == other.dict

    def __init__(self, typed_dict_proxy_name: str, **kwargs: typing.Any) -> None:
        self.dict = {}
        current_frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(current_frame, 2)
        parent_frame = outer_frames[1]
        print(parent_frame)
        self.parent_file_name = parent_frame.filename
        self.typed_dict_proxy_name = typed_dict_proxy_name
        self.dict.pop('parent_file_name', None)
        for (key, value) in kwargs.items():
            self.dict[key] = value

    def __setitem__(self, key: typing.Any, item: typing.Any) -> None:
        import pdb;pdb.set_trace()
        if key in forbidden_keys:
            return
        self.dict[key] = item

    def __getitem__(self, key: typing.Any) -> typing.Any:
        if key == 'parent_file_name':
            print("!!")
        return self.dict[key]

    def __repr__(self) -> str:
        return repr(self.dict)

    def __len__(self) -> int:
        return len(self.dict)

    def __delitem__(self, key: typing.Any) -> None:
        del self.dict[key]

    def clear(self) -> None:
        return self.dict.clear()

    def copy(self) -> typing.Any:
        return self.dict.copy()

    def has_key(self, key: typing.Any) -> bool:
        import pdb;pdb.set_trace()
        return key in self.dict

    def update(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        import pdb;pdb.set_trace()
        return self.dict.update(*args, **kwargs)

    def keys(self) -> typing.Any:
        return self.dict.keys()

    def values(self) -> typing.Any:
        return self.dict.values()

    def items(self) -> typing.Any:
        return self.dict.items()

    def pop(self, *args):
        return self.dict.pop(*args)

    def __cmp__(self, dict_: typing.Any):
        return self.__cmp__(self.dict, dict_)

    def __contains__(self, item: typing.Any):
        return item in self.dict

    def __iter__(self):
        return iter(self.dict)


typed_dict_proxy_key = 'typed_dict_proxy'
typed_dict_proxy_attrs_key = 'typed_dict_proxy_attrs'
typed_dict_proxy_name_key = 'typed_dict_proxy_name'

#
# test_dict = TypedDictProxy(
#     'test',
#     a=123,
# )
#
# import pdb;pdb.set_trace()
# print(test_dict)
# import json
# json.dumps(test_dict)