#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from layers import *
from fast_layers import *


conv_backward = conv_backward_fast
conv_forward = conv_forward_fast

avg_pool_forward = avg_pool_forward_fast
avg_pool_backward = avg_pool_backward_fast
max_pool_forward = avg_pool_forward_fast
max_pool_backward = avg_pool_backward_fast


def skip_forward(x, n_out_channels):
    N, n_in_channels, H, W = x.shape
    skip = np.array(x, copy=True)
    pool_cache, downsampled, skip_p = None, False, 0

    if n_out_channels > n_in_channels:
        # downsampling
        pool_param = {'pool_width': 2, 'pool_height': 2, 'stride': 2}
        skip, pool_cache = avg_pool_forward(skip, pool_param)
        # padding
        p = skip_p = (n_out_channels - n_in_channels)/2
        skip = np.pad(skip, ((0, 0), (p, p), (0, 0), (0, 0)),
                      mode='constant')

        downsampled = True

    return skip, (pool_cache, downsampled, skip_p)


def skip_backward(dout, cache):
    pool_cache, downsampled, skip_p = cache
    dskip = np.array(dout, copy=True)
    if downsampled:
        # back pad
        dskip = dskip[:, skip_p:-skip_p, :, :]
        # back downsampling
        dskip = avg_pool_backward(dskip, pool_cache)
    return dskip


def affine_relu_forward(x, w, b):
    '''
    Convenience layer that perorms an affine transform followed by a ReLU

    Inputs:
    - x: Input to the affine layer
    - w, b: Weights for the affine layer

    Returns a tuple of:
    - out: Output from the ReLU
    - cache: Object to give to the backward pass
    '''
    a, fc_cache = affine_forward(x, w, b)
    out, relu_cache = relu_forward(a)
    cache = (fc_cache, relu_cache)
    return out, cache


def affine_relu_backward(dout, cache):
    '''
    Backward pass for the affine-relu convenience layer
    '''
    fc_cache, relu_cache = cache
    da = relu_backward(dout, relu_cache)
    dx, dw, db = affine_backward(da, fc_cache)
    return dx, dw, db


def affine_batchnorm_relu_forward(x, w, b, gamma, beta, bn_param):
    '''
    Convenience layer that perorms an affine transform followed by a ReLU

    Inputs:
    - x: Input to the affine layer
    - w, b: Weights for the affine layer
    - gamma, beta : Weight for the batch norm regularization
    - bn_params : Contain variable use to batch norml, running_mean and var

    Returns a tuple of:
    - out: Output from the ReLU
    - cache: Object to give to the backward pass
    '''

    h, h_cache = affine_forward(x, w, b)
    hnorm, hnorm_cache = batchnorm_forward(h, gamma, beta, bn_param)
    hnormrelu, relu_cache = relu_forward(hnorm)
    cache = (h_cache, hnorm_cache, relu_cache)

    return hnormrelu, cache


def affine_batchnorm_relu_backward(dout, cache):
    '''
    Backward pass for the affine-relu convenience layer
    '''
    h_cache, hnorm_cache, relu_cache = cache

    dhnormrelu = relu_backward(dout, relu_cache)
    dhnorm, dgamma, dbeta = batchnorm_backward(dhnormrelu, hnorm_cache)
    dx, dw, db = affine_backward(dhnorm, h_cache)

    return dx, dw, db, dgamma, dbeta


def conv_batchnorm_relu_pool_forward(x, w, b, conv_param, gamma, beta, bn_param, pool_param):

    out, conv_cache = conv_forward_fast(x, w, b, conv_param)
    out, batchnorm_cache = spatial_batchnorm_forward(
        out, gamma, beta, bn_param)
    out, relu_cache = relu_forward(out)
    out, maxpool_cache = max_pool_forward(out, pool_param)

    cache = (conv_cache, batchnorm_cache, relu_cache, maxpool_cache)
    return out, cache


def conv_batchnorm_relu_pool_backward(dout, cache):

    conv_cache, batchnorm_cache, relu_cache, maxpool_cache = cache
    dout = max_pool_backward(dout, maxpool_cache)

    dout = relu_backward(dout, relu_cache)
    dout, dgamma, dbeta = spatial_batchnorm_backward(dout, batchnorm_cache)
    dx, dw, db = conv_backward_fast(dout, conv_cache)

    return dx, dw, db, dgamma, dbeta


def conv_batchnorm_relu_forward(x, w, b, conv_param, gamma, beta, bn_param):

    out, conv_cache = conv_forward_fast(x, w, b, conv_param)
    out, batchnorm_cache = spatial_batchnorm_forward(
        out, gamma, beta, bn_param)
    out, relu_cache = relu_forward(out)

    cache = (conv_cache, batchnorm_cache, relu_cache)
    return out, cache


def conv_batchnorm_relu_backward(dout, cache):

    conv_cache, batchnorm_cache, relu_cache = cache
    dout = relu_backward(dout, relu_cache)
    dout, dgamma, dbeta = spatial_batchnorm_backward(dout, batchnorm_cache)
    dx, dw, db = conv_backward_fast(dout, conv_cache)

    return dx, dw, db, dgamma, dbeta


def conv_relu_forward(x, w, b, conv_param):
    '''
    A convenience layer that performs a convolution followed by a ReLU.

    Inputs:
    - x: Input to the convolutional layer
    - w, b, conv_param: Weights and parameters for the convolutional layer

    Returns a tuple of:
    - out: Output from the ReLU
    - cache: Object to give to the backward pass
    '''
    a, conv_cache = conv_forward_fast(x, w, b, conv_param)
    out, relu_cache = relu_forward(a)
    cache = (conv_cache, relu_cache)
    return out, cache


def conv_relu_backward(dout, cache):
    '''
    Backward pass for the conv-relu convenience layer.
    '''
    conv_cache, relu_cache = cache
    da = relu_backward(dout, relu_cache)
    dx, dw, db = conv_backward_fast(da, conv_cache)
    return dx, dw, db


def conv_relu_pool_forward(x, w, b, conv_param, pool_param):
    '''
    Convenience layer that performs a convolution, a ReLU, and a pool.

    Inputs:
    - x: Input to the convolutional layer
    - w, b, conv_param: Weights and parameters for the convolutional layer
    - pool_param: Parameters for the pooling layer

    Returns a tuple of:
    - out: Output from the pooling layer
    - cache: Object to give to the backward pass
    '''
    a, conv_cache = conv_forward_fast(x, w, b, conv_param)
    s, relu_cache = relu_forward(a)
    out, pool_cache = max_pool_forward(s, pool_param)
    cache = (conv_cache, relu_cache, pool_cache)
    return out, cache


def conv_relu_pool_backward(dout, cache):
    '''
    Backward pass for the conv-relu-pool convenience layer
    '''
    conv_cache, relu_cache, pool_cache = cache
    ds = max_pool_backward(dout, pool_cache)
    da = relu_backward(ds, relu_cache)
    dx, dw, db = conv_backward_fast(da, conv_cache)
    return dx, dw, db
