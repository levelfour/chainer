import warnings

import numpy
import six

import chainer
from chainer import backend
from chainer.backends import cuda
import chainerx


def as_vec(x):
    warnings.warn(
        'chainer.utils.array.as_vec is deprecated. Please refer to '
        'numpy.ravel or other array backend functions to flatten ndarrays.',
        DeprecationWarning)
    if x.ndim == 1:
        return x
    return x.ravel()


def as_mat(x):
    warnings.warn(
        'chainer.utils.array.as_mat is deprecated. Please refer to '
        'numpy.reshape or other array backend functions to reshape ndarrays.',
        DeprecationWarning)
    if x.ndim == 2:
        return x
    return x.reshape(len(x), -1)


def empty_like(x):
    warnings.warn(
        'chainer.utils.array.empty_like is deprecated. Please refer to '
        'numpy.empty_like or other array backend functions to initialize '
        'empty arrays.',
        DeprecationWarning)
    if cuda.available and isinstance(x, cuda.ndarray):
        return cuda.cupy.empty_like(x)
    else:
        return numpy.empty_like(x)


def size_of_shape(shape):
    size = 1
    for i in shape:
        size *= i

    # should not return long in Python 2
    return int(size)


def sum_to(x, shape):
    if x.shape == shape:
        return x
    if isinstance(x, chainer.Variable):
        raise TypeError(
            'chainer.utils.sum_to does not support Variable input. '
            'Use chainer.functions.sum_to instead.')
    ndim = len(shape)
    lead = x.ndim - ndim
    lead_axis = tuple(six.moves.range(lead))
    axis = tuple([i + lead for i, sx in enumerate(shape) if sx == 1])
    y = x.sum(lead_axis + axis, keepdims=True)
    if lead > 0:
        y = y.squeeze(lead_axis)
    return y


# Workaround for chainerx.ndarray advanced indexing.
# This function is not differentiable.
# TODO(hvy): Remove this function when chainerx.ndarray.__getitem__ supports
# advanced indexing.
def _getitem(arr, key):
    try:
        return arr[key]
    except (IndexError, chainerx.DimensionError):
        pass

    if isinstance(arr, chainerx.ndarray):
        arr = backend.from_chainerx(arr)
        is_arr_chainerx = True
    else:
        is_arr_chainerx = False
    if isinstance(key, chainerx.ndarray):
        key = backend.from_chainerx(key)
    if isinstance(arr, cuda.ndarray):
        with arr.device:
            ret = arr[key]
    else:
        ret = arr[key]
    if is_arr_chainerx:
        ret = backend.to_chainerx(ret)
    return ret


# Workaround for chainerx.ndarray advanced indexing.
# This function is not differentiable.
# TODO(hvy): Remove this function when chainer.ndarray.__setitem__ supports
# advanced indexing.
def _setitem(arr, key, value):
    """Sets arr[key] to value by falling back to a non-ChainerX arrays.

    Supports both basic and advanced indexing.

    Note:

        With the ``cuda`` backend, the behavior differs from NumPy when
        integer arrays in ``slices`` reference the same location
        multiple times. In that case, the value that is actually stored
        is undefined.

        >>> import chainerx
        >>> chainerx.set_default_device('cuda:0')
        >>> a = chainerx.zeros((2,), dtype=chainerx.float)
        >>> i = chainerx.array([0, 1, 0, 1, 0, 1])
        >>> v = chainerx.arange(6).astype(chainerx.float)
        >>> a[i] = v
        >>> a  # doctest: +SKIP
        array([2., 3.], shape=(2,), dtype=float64, device='cuda:0')

        On the other hand, NumPy and ``native`` backend store the value
        corresponding to the last index among the indices referencing
        duplicate locations.

        >>> import numpy
        >>> a_cpu = numpy.zeros((2,), dtype=numpy.float)
        >>> i_cpu = numpy.array([0, 1, 0, 1, 0, 1])
        >>> v_cpu = numpy.arange(6).astype(numpy.float)
        >>> a_cpu[i_cpu] = v_cpu
        >>> a_cpu
        array([4., 5.])

    """
    if isinstance(arr, chainerx.ndarray):
        arr = backend.from_chainerx(arr)
    if isinstance(key, chainerx.ndarray):
        key = backend.from_chainerx(key)
    if isinstance(value, chainerx.ndarray):
        value = backend.from_chainerx(value)
    if isinstance(arr, cuda.ndarray):
        with arr.device:
            arr[key] = value
    else:
        arr[key] = value
