import sys
import urllib
import asyncio
import importlib
import uuid
from datetime import datetime, timedelta
from itertools import islice

import dateparser
import pytz


def add_sys_path(path):
    if not path in sys.path:
        sys.path.insert(0, path)


def get_class_from_classpath(class_path):
    str_mod, str_klass = ".".join(class_path.split(".")[:-1]), class_path.split(".")[-1]
    mod = importlib.import_module(str_mod)

    return getattr(mod, str_klass)


def get_class_from_classpath_for_obj(obj):
    """
    This is version of get_class_from_classpath() function working for string, dictionary or another object.
    If the `obj` param is a string with correct path to python class or object it returns value of get_class_from_classpath().
    If the 'obj' is dictionary the function returns copy of object with python paths replaced with corresponding objects.
    Otherwise the function returns unchanged parameter.
    """
    if isinstance(obj,str):
        try:
            chg_obj = get_class_from_classpath(obj)
        except ValueError:
            chg_obj = obj
        except ModuleNotFoundError:
            chg_obj = obj
    elif isinstance(obj,dict):
        chg_obj = {}
        for key in obj:
            if isinstance(obj[key],(dict, str)):
                chg_obj[key] = get_class_from_classpath_for_obj(obj[key])
            else:
                chg_obj[key] = obj[key]

    return chg_obj


def get_callable_from_path(path, dir_prefix = ""):
    str_mod, str_callable = path.split("::")
    str_mod = dir_prefix + str_mod

    mod = importlib.import_module(str_mod)
    return getattr(mod, str_callable)


def get_root_url(request):
    """
    Extract protocol and host from request to build URLs
    pointing to self (the API).
    """
    # try to build the root URL from x-forwared-for header (from Traefik) to provide links ready-to-click
    # note: we might serve incorrect proto, if https, traefik only reports http because https only happend at AWS ELB level
    proto = request.headers.get("x-forwarded-proto")
    host = request.headers.get("x-forwarded-host")
    if proto and host:
        root_url = urllib.parse.urlunparse((proto,host,'',None,None,None))
    else:
        root_url = ""  # give up :(
    root_url = root_url.rstrip("/")
    return root_url


def process_coroutine(coro):
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(coro)
    return res


def dateparse(date_or_ttl):
    try:
        return datetime.now(tz=pytz.UTC) + timedelta(seconds=int(date_or_ttl))
    except ValueError:
        return dateparser.parse(date_or_ttl,settings={"RETURN_AS_TIMEZONE_AWARE": True})


def random_id(obj):
    """Generate random ID for a given object, different accross time"""
    # uuid1 is interesting because timestamp is involved
    # but the node parameter is supposed to be the hardware address (48 bits), and
    # this will not change a lot as it's running on server side
    # we can use id() builtin function, but we need to make sure it's not longer than 48 bits)
    mask = 2**48 - 1
    node = id(obj) & mask
    aid = uuid.uuid1(node=node)
    # add random ID for fun
    rid = uuid.uuid4()
    return aid.hex + rid.hex


def iter_batch(iterable, batch_size):
    itr = iter(iterable)
    while True:
        chunk = tuple(islice(itr, batch_size))
        if not chunk:
            return
        yield chunk


def merge_struct(ver1, ver2, aslistofdict=None):
    """
    Merge python structure ver1 into ver2. It's doing what
    you think it should do.
    A warning though: ver1 will be modified while merged into ver2.
    """
    if isinstance(ver1, list):
        if isinstance(ver2, list):
            ver1 = ver1 + [x for x in ver2 if x not in ver1]
        else:
            if ver2 not in ver1:
                ver1.append(ver2)
    elif isinstance(ver2, list) and isinstance(ver1, dict):
        if ver1 not in ver2:
            ver2.append(ver1)
    elif isinstance(ver1, dict):
        assert isinstance(ver2, dict), "ver2 %s not a dict (ver1: %s)" % (ver2, ver1)
        for k in list(ver1.keys()):
            if k in ver2:
                if aslistofdict == k:
                    v1elem = ver1[k]
                    v2elem = ver2[k]
                    if not isinstance(v1elem, list):
                        v1elem = [v1elem]
                    if not isinstance(v2elem, list):
                        v2elem = [v2elem]
                    # v1elem and v2elem may be the same, in this case as a result
                    # we may have transformed it in a list (no merge, but just type change).
                    # if so, back to scalar
                    if v1elem != v2elem:
                        ver1[k] = merge_struct(v1elem, v2elem)
                else:
                    ver1[k] = merge_struct(ver1[k], ver2[k])
            else:
                ver2[k] = ver1[k]
        for k in ver2:
            if k in ver1:
                pass  # already done
            else:
                ver1[k] = ver2[k]
    elif isinstance(ver1, (float, int, str)):
        if isinstance(ver2, (float, int, str)):
            if ver1 != ver2:
                ver1 = [ver1, ver2]
            else:
                pass
        else:
            return merge_struct(ver2, ver1)
    elif ver1 is None:
        pass
    else:
        raise TypeError("Don't know how to merge type %s" % type(ver1))


def flatten_dict(dictionary:dict, sep:str="."):
    """converts dictionary into 1 level dictionary {key:val}
    where key is path to field from original dictionary and val is field value,
    key will be path with sep value being a separator
    """
    ret = {}
    for key, val in dictionary.items():
        if isinstance(val,dict):
            ret.update({key + sep + str(newkey): newval for newkey, newval in flatten_dict(val, sep).items()})
        else:
            ret.update({key:val})
    return ret


def compile_python_file(py_path):
    """Compiles python file. Returns dict with ready-to-use functionality."""
    ns = {}
    with open(py_path) as f:
        code = compile(f.read(), py_path, 'exec')
        exec(code, ns, ns)

    return ns


def get_callable_info(callable_obj, keep_self=False):
    """Function returns information about parameters and docs."""
    args_spec = inspect.getfullargspec(callable_obj)

    named_params = {}
    for par in args_spec.args:
        if par == "self" and not keep_self:
            continue
        named_params[par] = {}

    if args_spec.kwonlydefaults:
        for par in args_spec.kwonlydefaults:
            if par == "self" and not keep_self:
                continue
            named_params[par] = {}
            named_params[par]['default'] = args_spec.kwonlydefaults[par]

    for par in args_spec.annotations:
        if par in named_params:
            par_type = args_spec.annotations[par]
            if hasattr(par_type, "__name__"):
                par_type = par_type.__name__
            else:
                par_type = repr(par_type)
            named_params[par]['type'] = par_type

    for par in args_spec.kwonlyargs:
        named_params[par]['kwargs_only'] = True

    callable_info = {
        "named_params": named_params
    }

    if args_spec.varargs:
        args_name = args_spec.varargs
        args = {
            "name": args_name
        }
        if args_name in args_spec.annotations:
            args["type"] = args_spec.annotations[args_name].__name__
        callable_info["args"] = args
    else:
        callable_info["args"] = None

    if args_spec.varkw:
        kwargs_name = args_spec.varkw
        kwargs = {
            "name": kwargs_name
        }
        if kwargs_name in args_spec.annotations:
            kwargs["type"] = args_spec.annotations[kwargs_name].__name__
        callable_info["kwargs"] = kwargs
    else:
        callable_info["kwargs"] = None

    callable_info["docs"] = callable_obj.__doc__
    return callable_info
