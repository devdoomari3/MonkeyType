import typing

import inspect

forbidden_keys = set([
    'parent_file_name',
    'typed_dict_proxy_name',
])

class TypedDictProxy(dict):

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, TypedDictProxy):
            return False
        return self.__dict__ == other.__dict__

    def __init__(self, typed_dict_proxy_name: str, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)
        current_frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(current_frame, 2)
        parent_frame = outer_frames[1]
        print(parent_frame)
        self.parent_file_name = parent_frame.filename
        self.typed_dict_proxy_name = typed_dict_proxy_name
        for (key, value) in kwargs.items():
            self.__dict__[key] = value

    def __setitem__(self, key: typing.Any, item: typing.Any) -> None:
        import pdb;pdb.set_trace()
        if key in forbidden_keys:
            return
        self.__dict__[key] = item

    def __getitem__(self, key: typing.Any) -> typing.Any:
        if key == 'parent_file_name':
            print("!!")
        return self.__dict__[key]

    def __repr__(self) -> str:
        return repr(self.__dict__)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __delitem__(self, key: typing.Any) -> None:
        del self.__dict__[key]

    def clear(self) -> None:
        return self.__dict__.clear()

    def copy(self) -> typing.Any:
        return self.__dict__.copy()

    def has_key(self, key: typing.Any) -> bool:
        return key in self.__dict__

    def update(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        return self.__dict__.update(*args, **kwargs)

    def keys(self) -> typing.Any:
        return self.__dict__.keys()

    def values(self) -> typing.Any:
        return self.__dict__.values()

    def items(self) -> typing.Any:
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, dict_: typing.Any):
        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item: typing.Any):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)


typed_dict_proxy_key = 'typed_dict_proxy'
typed_dict_proxy_attrs_key = 'typed_dict_proxy_attrs'
typed_dict_proxy_name_key = 'typed_dict_proxy_name'

TypedDictProxy(
    'test',
    a=123,
)
