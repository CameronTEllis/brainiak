#  Copyright 2016 Intel Corporation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""fmrisim real-time generator test script

 Authors: Cameron Ellis (Princeton) 2020
"""
import numpy as np
import math
from brainiak.utils import fmrisim_real_time_generator as gen
import pytest
from itertools import product
import os
import nibabel as nib
import time
import glob
import copy

# Test that it crashes without inputs
with pytest.raises(TypeError):
    gen.generate_data()

# Set up the default values
outputDir = tmp_path

data_dict = {}
data_dict['ROI_A_file'] = resource_stream(__name__, "ROI_A.nii.gz")
data_dict['ROI_B_file'] = resource_stream(__name__, "ROI_B.nii.gz")
data_dict['template_path'] = resource_stream(__name__, "sub_template.nii.gz")
data_dict['noise_dict_file'] = resource_stream(__name__, "sub_noise_dict.txt")
data_dict['numTRs'] = 30
data_dict['event_duration'] = 2
data_dict['scale_percentage'] = 1
data_dict['different_ROIs'] = True
data_dict['multivariate_pattern'] = False
data_dict['save_dicom'] = False
data_dict['save_realtime'] = False
data_dict['trDuration'] = 2
data_dict['isi'] = 4
data_dict['burn_in'] = 6

# Run default test
def test_default(outputDir=outputDir, dd=data_dict):

    # Make sure you don't edit the data dict
    dd = copy.deepcopy(dd)

    # Clean directory
    os.system('rm -rf %s' % outputDir)

    # Run the simulation
    gen.generate_data(outputDir,
                      dd)

    # Check that there are 32 files where there should be (30 plus label and
    # mask)
    assert len(os.listdir(outputDir)) == 32, "Incorrect file number"

    # Check that the data is the right shape
    input_template = nib.load(dd['template_path'])
    input_shape = input_template.shape
    output_vol = np.load(outputDir + 'rt_000.npy')
    output_shape = output_vol.shape
    assert input_shape == output_shape, 'Output shape is incorrect'

    # Check the labels have the correct count
    labels = np.load(outputDir + 'labels.npy')

    assert np.sum(labels > 0) == 9, 'Incorrect number of events'


def test_signal_size(outputDir=outputDir, dd=data_dict):

    # Make sure you don't edit the data dict
    dd = copy.deepcopy(dd)

    # Change it to only use ROI A
    dd['different_ROIs'] = False

    # Make the signal large
    dd['scale_percentage'] = 100

    # Clean directory
    os.system('rm -rf %s' % outputDir)

    # Run the simulation
    gen.generate_data(outputDir,
                      dd)

    # Load in the ROI masks
    ROI_A = nib.load(dd['ROI_A_file']).get_data()
    ROI_B = nib.load(dd['ROI_B_file']).get_data()

    # Load in the data just simulated
    ROI_A_mean = []
    ROI_B_mean = []
    for TR_counter in range(dd['numTRs']):

        # Load the data
        vol = np.load(outputDir + 'rt_%03d.npy' % TR_counter)

        # Mask the data
        ROI_A_mean += [np.mean(vol[ROI_A == 1])]
        ROI_B_mean += [np.mean(vol[ROI_B == 1])]

    assert np.std(ROI_A_mean) > np.std(ROI_B_mean), 'Signal not scaling'


# Run default test
def test_save_dicoms_realtime(outputDir=outputDir, dd=data_dict):

    # Make sure you don't edit the data dict
    dd = copy.deepcopy(dd)

    # Clean directory
    os.system('rm -rf %s' % outputDir)

    dd['save_dicom'] = True
    dd['save_realtime'] = True

    start_time = time.time()

    # Run the simulation
    gen.generate_data(outputDir,
                      dd)

    end_time = time.time()

    # Check it took 2s per TR
    assert (end_time - start_time) > 60, 'Realtime ran fast'

    # Check correct file number
    assert len(glob.glob(outputDir + '*.dcm')) == 30, "Incorrect dicom file num"


def test_multivariate(outputDir=outputDir, dd=data_dict):

    # Make sure you don't edit the data dict
    dd = copy.deepcopy(dd)

    dd['multivariate_pattern'] = True
    dd['different_ROIs'] = False

    # Make the signal large
    dd['scale_percentage'] = 100

    # Clean directory
    os.system('rm -rf %s' % outputDir)

    # Run the simulation
    gen.generate_data(outputDir,
                      dd)

    # Load in the ROI masks
    ROI_A = nib.load(dd['ROI_A_file']).get_data()
    ROI_B = nib.load(dd['ROI_B_file']).get_data()

    # Test this volume
    vol = np.load(outputDir + 'rt_007.npy')

    ROI_A_std = np.std(vol[ROI_A == 1])
    ROI_B_std = np.std(vol[ROI_B == 1])

    assert ROI_A_std > ROI_B_std, 'Multivariate test not making variable signal'

