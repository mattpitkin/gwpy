# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""Unit test for timeseries module
"""

import tempfile

import pytest

import numpy

from matplotlib import rc_context

from astropy import units

from ...detector import Channel
from ...time import Time
from ...tests import utils
from ...types import Array2D
from .. import (StateVector, StateVectorDict, StateVectorList,
                StateTimeSeries, StateTimeSeriesDict, Bits)
from .test_core import (TestTimeSeriesBase as _TestTimeSeriesBase,
                        TestTimeSeriesBaseDict as _TestTimeSeriesBaseDict,
                        TestTimeSeriesBaseList as _TestTimeSeriesBaseList)
from .test_timeseries import (LOSC_IFO, LOSC_GW150914_SEGMENT,
                              LOSC_FETCH_ERROR)

LOSC_GW150914_DQ_NAME = {
    'hdf5': 'Data quality',
    'gwf': 'L1:LOSC-DQMASK',
}
LOSC_GW150914_DQ_BITS = {
    'hdf5': [
        'data present',
        'passes cbc CAT1 test',
        'passes cbc CAT2 test',
        'passes cbc CAT3 test',
        'passes burst CAT1 test',
        'passes burst CAT2 test',
        'passes burst CAT3 test',
    ],
    'gwf': [
        'DATA',
        'CBC_CAT1',
        'CBC_CAT2',
        'CBC_CAT3',
        'BURST_CAT1',
        'BURST_CAT2',
        'BURST_CAT3',
    ],
}

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# -- StateTimeSeries ----------------------------------------------------------

class TestStateTimeSeries(_TestTimeSeriesBase):
    TEST_CLASS = StateTimeSeries

    @classmethod
    def setup_class(cls):
        cls.data = numpy.asarray([0, 1, 1, 1, 0, 0, 0, 1, 0, 0,
                                  1, 1, 1, 0, 1, 0, 1, 1, 1, 1],
                                 dtype=bool)

    def test_new(self):
        sts = self.create()
        assert isinstance(sts, self.TEST_CLASS)
        assert sts.dtype is numpy.dtype('bool')

    def test_getitem(self, array):
        assert isinstance(array[0], numpy.bool_)

    def test_unit(self, array):
        assert array.unit is units.dimensionless_unscaled

        # check that we can't delete the unit
        with pytest.raises(AttributeError):
            del array.unit

        # check that we can't set the unit
        with pytest.raises(TypeError):
            self.create(unit='test')

    def test_math(self, array):
        # test that math operations give back booleans
        a2 = array ** 2
        assert a2.dtype is numpy.dtype(bool)
        utils.assert_array_equal(array.value, a2.value)

    def test_override_unit(self):
        return NotImplemented

    def test_is_compatible(self):
        return NotImplemented

    def test_to_from_pycbc(self):
        return NotImplemented

    def test_to_from_lal(self):
        return NotImplemented

    def test_from_nds2_buffer(self):
        return NotImplemented


# -- StateTimeSeriesDict ------------------------------------------------------

class TestStateTimeSeriesDict(_TestTimeSeriesBaseDict):
    TEST_CLASS = StateTimeSeriesDict
    ENTRY_CLASS = StateTimeSeries
    DTYPE = 'bool'

    def test_resample(self):
        return NotImplemented


# -- Bits ---------------------------------------------------------------------

class TestBits(object):
    TEST_CLASS = Bits

    @pytest.mark.parametrize('in_, out', [
        # list
        (['bit 0', 'bit 1', 'bit 2', None, 'bit 3', ''],
         ['bit 0', 'bit 1', 'bit 2', None, 'bit 3', None]),
        # dict
        ({1: 'bit 1', 4: 'bit 4', '6': 'bit 6'},
         [None, 'bit 1', None, None, 'bit 4', None, 'bit 6']),
    ])
    def test_init(self, in_, out):
        bits = self.TEST_CLASS(in_)
        assert bits == out
        assert bits.channel is None
        assert bits.epoch is None
        assert bits.description == {bit: None for bit in bits if
                                    bit is not None}

        bits = self.TEST_CLASS(in_, channel='L1:Test', epoch=0)
        assert bits.epoch == Time(0, format='gps')
        assert bits.channel == Channel('L1:Test')

    def test_str(self):
        bits = self.TEST_CLASS(['a', 'b', None, 'c'])
        assert str(bits) == (
            "Bits(0: a\n"
            "     1: b\n"
            "     3: c,\n"
            "     channel=None,\n"
            "     epoch=None)")

    def test_repr(self):
        bits = self.TEST_CLASS(['a', 'b', None, 'c'])
        assert repr(bits) == (
            "<Bits(0: 'a'\n"
            "      1: 'b'\n"
            "      3: 'c',\n"
            "      channel=None,\n"
            "      epoch=None)>")

    def test_array(self):
        bits = self.TEST_CLASS(['a', 'b', None, 'c'])
        utils.assert_array_equal(
            numpy.asarray(bits),
            ['a', 'b', '', 'c'],
        )


# -- StateVector---------------------------------------------------------------

class TestStateVector(_TestTimeSeriesBase):
    TEST_CLASS = StateVector
    DTYPE = 'uint32'

    @classmethod
    def setup_class(cls):
        numpy.random.seed(0)
        cls.data = numpy.random.randint(
            2**4+1, size=100).astype(cls.DTYPE, copy=False)

    def test_bits(self, array):
        assert isinstance(array.bits, Bits)
        assert array.bits == ['Bit %d' % i for i in range(32)]

        bits = ['Bit %d' % i for i in range(4)]

        sv = self.create(bits=bits)
        assert isinstance(sv.bits, Bits)
        assert sv.bits.channel is sv.channel
        assert sv.bits.epoch == sv.epoch
        assert sv.bits == bits

        del sv.bits
        del sv.bits
        assert isinstance(sv.bits, Bits)
        assert sv.bits == ['Bit %d' % i for i in range(32)]

        sv = self.create(dtype='uint16')
        assert sv.bits == ['Bit %d' % i for i in range(16)]

    def test_boolean(self, array):
        b = array.boolean
        assert isinstance(b, Array2D)
        assert b.shape == (array.size, len(array.bits))
        # array[0] == 12, check boolean equivalent
        utils.assert_array_equal(b[0], [int(12) >> j & 1 for j in range(32)])

    def test_get_bit_series(self, array):
        # test default
        bs = array.get_bit_series()
        assert isinstance(bs, StateTimeSeriesDict)
        assert list(bs.keys()) == array.bits
        # check that correct number of samples match (simple test)
        assert bs['Bit 2'].sum() == 43

        # check that bits in gives bits out
        bs = array.get_bit_series(['Bit 0', 'Bit 3'])
        assert list(bs.keys()) == ['Bit 0', 'Bit 3']
        assert [v.sum() for v in bs.values()] == [50, 41]

        # check that invalid bits throws exception
        with pytest.raises(ValueError) as exc:
            array.get_bit_series(['blah'])
        assert str(exc.value) == "Bit 'blah' not found in StateVector"

    @utils.skip_missing_dependency('lal')
    def test_plot(self, array):
        with rc_context(rc={'text.usetex': False}):
            plot = array.plot()
            # make sure there were no lines drawn
            assert plot.gca().lines == []
            # assert one collection for each of known and active segmentlists
            assert len(plot.gca().collections) == len(array.bits) * 2
            with tempfile.NamedTemporaryFile(suffix='.png') as f:
                plot.save(f.name)
            plot.close()

            # test timeseries plotting as normal
            plot = array.plot(format='timeseries')
            line = plot.gca().lines[0]
            utils.assert_array_equal(line.get_xdata(), array.xindex)
            utils.assert_quantity_sub_equal(line.get_ydata(), array)
            plot.close()

    def test_resample(self, array):
        # check downsampling by factor of 2
        a2 = array.resample(array.sample_rate / 2.)
        assert a2.sample_rate == array.sample_rate / 2.
        assert a2.bits is array.bits
        utils.assert_array_equal(a2.value[:10],
                                 [12, 0, 3, 0, 4, 0, 6, 5, 8, 0])

        # check upsampling raises NotImplementedError
        with pytest.raises(NotImplementedError):
            array.resample(array.sample_rate * 2.)

        # check resampling by non-integer factor raises error
        with pytest.raises(ValueError):
            array.resample(array.sample_rate * .75)
        with pytest.raises(ValueError):
            array.resample(array.sample_rate * 1.5)

    # -- data access ----------------------------

    @pytest.mark.parametrize('format', [
        'hdf5',
        pytest.param(  # only frameCPP actually reads units properly
            'gwf', marks=utils.skip_missing_dependency('LDAStools.frameCPP')),
    ])
    def test_fetch_open_data(self, format):
        try:
            sv = self.TEST_CLASS.fetch_open_data(
                LOSC_IFO, *LOSC_GW150914_SEGMENT, format=format, version=1)
        except LOSC_FETCH_ERROR as e:
            pytest.skip(str(e))
        utils.assert_quantity_sub_equal(
            sv,
            StateVector([127, 127, 127, 127], unit='',
                        t0=LOSC_GW150914_SEGMENT[0], dt=1,
                        name=LOSC_GW150914_DQ_NAME[format],
                        bits=LOSC_GW150914_DQ_BITS[format]),
            exclude=['channel'])


# -- StateVectorDict ----------------------------------------------------------

class TestStateVectorDict(_TestTimeSeriesBaseDict):
    TEST_CLASS = StateVectorDict
    ENTRY_CLASS = StateVector
    DTYPE = 'uint32'


# -- StateVectorList ----------------------------------------------------------

class TestStateVectorList(_TestTimeSeriesBaseList):
    TEST_CLASS = StateVectorList
    ENTRY_CLASS = StateVector
    DTYPE = 'uint32'