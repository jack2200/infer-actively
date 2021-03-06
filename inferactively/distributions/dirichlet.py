#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Dirichlet

__author__: Conor Heins, Alexander Tschantz, Brennan Klein

"""

import numpy as np
import warnings


class Dirichlet(object):
    def __init__(self, dims=None, values=None):
        """Initialize a Dirichlet distribution

        `IS_AOA` refers to whether this class uses the `array-of-array` formulation

        Parameters
        ----------
        dims: list of int _or_ list of list (where each list is a list of int)
            Specify the number and size of dimensions
            This will initialize the parameters with zero values
        values: np.ndarray
            The parameters of the distribution
        """

        self.IS_AOA = False

        if values is not None and dims is not None:
            raise ValueError("please provide _either_ :dims: or :values:, not both")

        if values is None and dims is None:
            self.values = np.zeros([1, 1])

        if values is not None:
            self.construct_values(values)

        if dims is not None:
            self.construct_dims(dims)

    def construct_values(self, values):
        """Initialize a Dirichlet distribution with `values` argument

        Parameters
        ----------
        values: np.ndarray
            The parameters of the distribution

        """
        if not isinstance(values, np.ndarray):
            raise ValueError(":values: must be a :numpy.ndarray:")

        if values.dtype == "object":
            self.IS_AOA = True

        if self.IS_AOA:
            self.values = np.empty(len(values), dtype="object")
            for i, array in enumerate(values):
                if array.ndim == 1:
                    values[i] = np.expand_dims(values[i], axis=1)
                self.values[i] = values[i].astype("float64")
        else:
            if values.ndim == 1:
                values = np.expand_dims(values, axis=1)
            self.values = values.astype("float64")

    def construct_dims(self, dims):
        """Initialize a Dirichlet distribution with `values` argument

        TODO: allow other iterables (such as tuple)

        Parameters
        ----------
        dims: list of int
            Specify the number and size of dimensions
            This will initialize the parameters with zero values
        """

        if isinstance(dims, list):
            if any(isinstance(el, list) for el in dims):
                if not all(isinstance(el, list) for el in dims):
                    raise ValueError(":list: of :dims: must only contains :lists:")
                self.IS_AOA = True

            if self.IS_AOA:
                self.values = np.empty(len(dims), dtype="object")
                for i in range(len(dims)):
                    if len(dims[i]) == 1:
                        self.values[i] = np.zeros([dims[i][0], 1])
                    else:
                        self.values[i] = np.zeros(dims[i])
            else:
                if len(dims) == 1:
                    self.values = np.zeros([dims[0], 1])
                else:
                    self.values = np.zeros(dims)
        elif isinstance(dims, int):
            self.values = np.zeros([dims, 1])
        else:
            raise ValueError(":dims: must be either :list: or :int:")

    def normalize(self):
        """ Normalize distribution

        This function will ensure the distribution(s) integrate to 1.0
        In the case `ndims` >= 2, normalization is performed along the columns of the arrays

        """
        if self.IS_AOA:
            normed = np.empty(len(self.values), dtype=object)
            for i in range(len(self.values)):
                array_i = self.values[i]
                column_sums = np.sum(array_i, axis=0)
                array_i = np.divide(array_i, column_sums)
                array_i[np.isnan(array_i)] = np.divide(1.0, array_i.shape[0])
                normed[i] = array_i
        else:
            normed = np.zeros(self.values.shape)
            column_sums = np.sum(self.values, axis=0)
            normed = np.divide(self.values, column_sums)
            normed[np.isnan(normed)] = np.divide(1.0, normed.shape[0])
        return normed

    def remove_zeros(self):
        """ Remove zeros by adding a small number

        This function avoids division by zero
        exp(-16) is used as the minimum value

        """
        self.values += np.exp(-16)

    def wnorm(self, return_numpy=True):
        """ Expectation of a (log) Categorical distribution parameterized
        with a Dirichlet prior over its parameters (or a set of such Categorical distributions,
        e.g. a multi-dimensional likelihood)
        """

        if self.IS_AOA:
            wA = np.empty(len(self.values), dtype=object)
            for i in range(len(self.values)):
                A = Dirichlet(values=self[i].values)
                A.remove_zeros()
                A = A.values
                norm = np.divide(1.0, np.sum(A, axis=0))
                avg = np.divide(1.0, A)
                wA[i] = norm - avg
            if return_numpy:
                return wA
            else:
                return Dirichlet(values=wA)
        else:
            A = Dirichlet(values=self.values)
            A.remove_zeros()
            A = A.values
            norm = np.divide(1.0, np.sum(A, axis=0))
            avg = np.divide(1.0, A)
            wA = norm - avg
            if return_numpy:
                return wA
            else:
                return Dirichlet(values=wA)

    def contains_zeros(self):
        """ Checks if any values are zero

        Returns
        ----------
        bool
            Whether there are any zeros

        """
        if not self.IS_AOA:
            return (self.values == 0.0).any()
        else:
            for i in range(len(self.values)):
                if (self.values[i] == 0.0).any():
                    return True
            return False

    def entropy(self, return_numpy=False):
        pass

    def log(self, return_numpy=False):
        """ Return the log of the parameters

        Parameters
        ----------
        return_numpy: bool
            Whether to return a :np.ndarray: or :Dirichlet: object

        Returns
        ----------
        np.ndarray or Dirichlet
            The log of the parameters
        """

        if self.contains_zeros():
            self.remove_zeros()
            warnings.warn(
                "You have called :log: on a Dirichlet that contains zeros. \
                     We have removed zeros."
            )

        if not self.IS_AOA:
            values = np.copy(self.values)
            log_values = np.log(values)
        else:
            log_values = np.empty(len(self.values), dtype="object")
            for i in range(len(self.values)):
                values = np.copy(self.values[i])
                log_values[i] = np.log(values)

        if return_numpy:
            return log_values
        else:
            return Dirichlet(values=log_values)

    def copy(self):
        """Returns a copy of this object

        Returns
        ----------
        Dirichlet
            Returns a copy of this object
        """
        values = np.copy(self.values)
        return Dirichlet(values=values)

    def print_shape(self):
        if not self.IS_AOA:
            print("Shape: {}".format(self.values.shape))
        else:
            string = [str(el.shape) for el in self.values]
            print("Shape: {} {}".format(self.values.shape, string))

    @property
    def ndim(self):
        return self.values.ndim

    @property
    def shape(self):
        return self.values.shape

    def __add__(self, other):
        if isinstance(other, Dirichlet):
            values = self.values + other.values
            return Dirichlet(values=values)
        else:
            values = self.values + other
            return Dirichlet(values=values)

    def __radd__(self, other):
        if isinstance(other, Dirichlet):
            values = self.values + other.values
            return Dirichlet(values=values)
        else:
            values = self.values + other
            return Dirichlet(values=values)

    def __sub__(self, other):
        if isinstance(other, Dirichlet):
            values = self.values - other.values
            return Dirichlet(values=values)
        else:
            values = self.values - other
            return Dirichlet(values=values)

    def __rsub__(self, other):
        if isinstance(other, Dirichlet):
            values = self.values - other.values
            return Dirichlet(values=values)
        else:
            values = self.values - other
            return Dirichlet(values=values)

    def __mul__(self, other):
        if isinstance(other, Dirichlet):
            values = self.values * other.values
            return Dirichlet(values=values)
        else:
            values = self.values * other
            return Dirichlet(values=values)

    def __rmul__(self, other):
        if isinstance(other, Dirichlet):
            values = self.values * other.values
            return Dirichlet(values=values)
        else:
            values = self.values * other
            return Dirichlet(values=values)

    def __contains__(self, value):
        pass

    def __getitem__(self, key):
        values = self.values[key]
        if isinstance(values, np.ndarray):
            if values.ndim == 1:
                values = values[:, np.newaxis]
            return Dirichlet(values=values)
        else:
            return values

    def __setitem__(self, idx, value):
        if isinstance(value, Dirichlet):
            value = value.values
        self.values[idx] = value

    def __repr__(self):
        if not self.IS_AOA:
            return "<Dirichlet Distribution> \n {}".format(np.round(self.values, 3))
        else:
            string = [np.round(el, 3) for el in self.values]
            return "<Dirichlet Distribution> \n {}".format(string)
