'''
runMothLearnerOnReducedMnist

Main script to train a moth brain model on a crude (downsampled) MNIST set.
The moth can be generated from template or loaded complete from file.

Modifying parameters:
	1. Modify 'specifyModelParamsMnist_fn' with the desired parameters for
		generating a moth (ie neural network), or specify a pre-existing 'modelParams' file to load.
	2. Edit USER ENTRIES

The dataset:
	Because the moth brain architecture, as evolved, only handles ~60 features, we need to
create a new, MNIST-like task but with many fewer than 28x 28 pixels-as-features.
We do this by cropping and downsampling the mnist thumbnails, then selecting a subset of the
remaining pixels.
	This results in a cruder dataset (set various view flags to see thumbnails).
However, it is sufficient for testing the moth brain's learning ability. Other ML methods need
to be tested on this same cruder dataset to make useful comparisons.

Define train and control pools for the experiment, and determine the receptive field.
This is done first because the receptive field determines the number of AL units, which
     must be updated in modelParams before 'initializeMatrixParams_fn' runs.
This dataset will be used for each simulation in numRuns. Each
     simulation draws a new set of samples from this set.

Order of events:
	1. Load and pre-process dataset
	Within the loop over number of simulations:
	2. Select a subset of the dataset for this simulation (only a few samples are used).
	3. Create a moth (neural net). Either select an existing moth file, or generate a new moth in 2 steps:
		a) run 'specifyModelParamsMnist' and
		   incorporate user entry edits such as 'goal'.
		b) create connection matrices via 'init_connection_matrix'
	4. Load the experiment parameters.
	5. Run the simulation with 'sde_wrap'
	6. Plot results, print results to console

Copyright (c) 2019 Adam P. Jones (ajones173@gmail.com) and Charles B. Delahunt (delahunt@uw.edu)
MIT License
'''

# import packages
import time
runStart = time.time() # time execution duration
import numpy as np
import os
import dill # for pickling module object (optional)
import copy # for deep copy of nested lists

# Experiment details
from support_functions.generate import generate_ds_MNIST
from support_functions.show_figs import show_FA_thumbs, view_EN_resp
from support_functions.params import init_connection_matrix, ExpParams
from support_functions.sde import sde_wrap
from support_functions.classify import classify_digits_log_likelihood, classify_digits_thresholding

# DEV NOTE: Add test for Python vers == 3

## USER ENTRIES (Edit parameters below):
#-------------------------------------------------------------------------------
screen_size = (1920, 1080) # screen size (width, height)

use_existing_conn_matrices = False
# if True, load 'matrixParamsFilename', which includes filled-in connection matrices
# if False, generate new moth from template in params.py

matrix_params_filename = 'sampleMothModelParams'
# dict with all info, including connection matrices, of a particular moth

num_runs = 1 # how many runs you wish to do with this moth or moth template,
# each run using random draws from the mnist set

goal  = 15
# defines the moth's learning rates, in terms of how many training samples per
# class give max accuracy. So "goal = 1" gives a very fast learner.
# if goal == 0, the rate parameters defined the template will be used as-is
# if goal > 1, the rate parameters will be updated, even in a pre-set moth

tr_per_class =  3 # the number of training samples per class
num_sniffs = 2 # number of exposures each training sample

# nearest neighbors
runNearestNeighbors = True
numNeighbors = 1 # optimization param for nearest neighbors
# Suggested values: trPerClass ->
#	numNeighbors:  1,3,5 -> 1;  (10, 20, 50) -> 1 or 3;  100 -> 3; 500 + -> 5

# SVM
runSVM = True
boxConstraint = 1e1 # optimization parameter for svm
# Suggested values: trPerClass ->
#	boxConstraint:  1 -> NA; 3 -> 1e4; 5 -> 1e0 or 1e1; 10 -> 1e-1,
#					20 -> 1e-4 or 1e-5, 50 -> 1e-5 ; 100+ -> 1e-7

## Flags to show various images:
show_thumbnails = 0 # N means show N experiment inputs from each class
	# 0 means don't show any
show_EN_plots = [1, 1] # 1 to plot, 0 to ignore
# arg1 refers to statistical plots of EN response changes: One image (with 8 subplots) per EN
# arg2 refers to EN timecourses: Three scaled ENs timecourses on each of 4 images (only one EN on the 4th image)

# To save results if wished:
save_all_neural_timecourses = False # 0 -> save only EN (ie readout) timecourses
# Caution: 1 -> very high memory demands, hinders longer runs
results_filename = 'results' # will get the run number appended to it
save_results_data_folder = 'results/data' # String
# If non-empty, 'results_filename' will be saved here
save_results_image_folder = 'results' # String
# If non-empty, results will be saved here (if show_EN_plots also non-zero)
save_params_folder = 'params' # String
# If non-empty, params will be saved here (if show_EN_plots also non-zero)

#-------------------------------------------------------------------------------

## Misc book-keeping
class_labels = np.array(range(10))  # For MNIST. '0' is labeled as 10
val_per_class = 15  # number of digits used in validation sets and in baseline sets

# make a vector of the classes of the training samples, randomly mixed:
tr_classes = np.repeat( class_labels, tr_per_class )
tr_classes = np.random.permutation( tr_classes )
# repeat these inputs if taking multiple sniffs of each training sample:
tr_classes = np.tile( tr_classes, [1, num_sniffs] )[0]

#-------------------------------------------------------------------------------

## Load and preprocess the dataset.

# The dataset:
# Because the moth brain architecture, as evolved, only handles ~60 features, we need to
# create a new, MNIST-like task but with many fewer than 28x28 pixels-as-features.
# We do this by cropping and downsampling the MNIST thumbnails, then selecting
# a subset of the remaining pixels.
# This results in a cruder dataset (set various view flags to see thumbnails).
# However, it is sufficient for testing the moth brain's learning ability. Other
# ML methods need to be tested on this same cruder dataset to make useful comparisons.

# Define train and control pools for the experiment, and determine the receptive field.
# This is done first because the receptive field determines the number of AL units, which
#      must be updated in modelParams before 'initializeMatrixParams_fn' runs.
# This dataset will be used for each simulation in num_runs. Each
#      simulation draws a new set of samples from this set.

# Parameters:
# Parameters required for the dataset generation function are attached to a dictionary: 'preP'.
# 1. The images used. This includes pools for mean-subtraction, baseline, train, and val.
#   This is NOT the number of training samples per class.
# 	That is tr_per_class, defined above.

# Specify pools of indices from which to draw baseline, train, val sets.
indPoolForBaseline = list(range(100)) # 1:100
indPoolForTrain = list(range(100,300)) # 101:300
indPoolForPostTrain = list(range(300,400)) # 301:400

# Population preprocessing pools of indices:
preP = dict()
preP['indsToAverageGeneral'] = list(range(550,1000)) # 551:1000
preP['indsToCalculateReceptiveField'] = list(range(550,1000)) # 551:1000
preP['maxInd'] = max( [ preP['indsToCalculateReceptiveField'] + \
	indPoolForTrain ][0] ) # we'll throw out unused samples

## 2. Pre-processing parameters for the thumbnails:
preP['screen_size'] = screen_size
preP['downsampleRate'] = 2
preP['crop'] = 2
preP['numFeatures'] =  85  # number of pixels in the receptive field
preP['pixelSum'] = 6
preP['showThumbnails'] = show_thumbnails # boolean
preP['downsampleMethod'] = 1 # 0 means sum square patches of pixels
							 # 1 means use bicubic interpolation

preP['classLabels'] = class_labels # append
preP['useExistingConnectionMatrices'] = use_existing_conn_matrices # boolean
preP['matrixParamsFilename'] = matrix_params_filename

# generate the data array:
fA, activePixelInds, lengthOfSide = generate_ds_MNIST(preP, save_results_image_folder)
# argin = preprocessingParams

pixNum, numPerClass, classNum = fA.shape
# The dataset fA is a feature array ready for running experiments.
# Each experiment uses a random draw from this dataset.
# fA = n x m x 10 array where n = #active pixels, m = #digits from each class
# that will be used. The 3rd dimension gives the class, 1:10 where 10 = '0'.

#-------------------------------------------------------------------------------

# Loop through the number of simulations specified:
print(f'starting sim(s) for goal = {goal}, tr_per_class = {tr_per_class}, numSniffsPerSample = {num_sniffs}')

for run in range(num_runs):

	## Subsample the dataset for this simulation
	# Line up the images for the experiment (in 10 parallel queues)
	digitQueues = np.zeros(fA.shape)

	for i in class_labels:

		## 1. Baseline (pre-train) images
		# choose some images from the baselineIndPool
		rangeTopEnd = max(indPoolForBaseline) - min(indPoolForBaseline) + 1
		r_sample = np.random.choice(rangeTopEnd, val_per_class) # select random digits
		theseInds = min(indPoolForBaseline) + r_sample
		digitQueues[:,:val_per_class,i] = fA[:,theseInds,i]

		## 2. Training images
		# choose some images from the trainingIndPool
		rangeTopEnd = max(indPoolForTrain) - min(indPoolForTrain) + 1
		r_sample = np.random.choice(rangeTopEnd, tr_per_class) # select random digits
		theseInds = min(indPoolForTrain) + r_sample
		# repeat these inputs if taking multiple sniffs of each training sample
		theseInds = np.tile(theseInds, num_sniffs)
		digitQueues[:, val_per_class:(val_per_class+tr_per_class*num_sniffs), i] = fA[:, theseInds, i]

		## 3. Post-training (val) images
		# choose some images from the postTrainIndPool
		rangeTopEnd = max(indPoolForPostTrain) - min(indPoolForPostTrain) + 1
		r_sample = np.random.choice(rangeTopEnd, val_per_class) # select random digits
		theseInds = min(indPoolForPostTrain) + r_sample
		digitQueues[:,(val_per_class+tr_per_class*num_sniffs):(val_per_class+tr_per_class*num_sniffs+val_per_class),
			i] = fA[:, theseInds, i]

	# show the final versions of thumbnails to be used, if wished
	if show_thumbnails:
		tempArray = np.zeros((lengthOfSide, numPerClass, classNum))
		tempArray[activePixelInds,:,:] = digitQueues
		normalize = 1
		titleStr = 'Input thumbnails'
		show_FA_thumbs(tempArray, show_thumbnails, normalize,
									titleStr, screen_size, save_results_image_folder)

#-------------------------------------------------------------------------------
	# Re-organize train and val sets for classifiers:

	# Build train and val feature matrices and class label vectors.
	# X = n x numberPixels;  Y = n x 1, where n = 10*tr_per_class.
	trainX = np.zeros((10*tr_per_class, fA.shape[0]))
	valX = np.zeros((10*val_per_class, fA.shape[0]))
	trainY = np.zeros((10*tr_per_class, 1))
	valY = np.zeros((10*val_per_class, 1))

	# populate the labels one class at a time
	for i in class_labels:
		# skip the first 'val_per_class' digits,
		# as these are used as baseline digits in the moth (formality)
		temp = digitQueues[:,val_per_class:val_per_class+tr_per_class,i]
		trainX[i*tr_per_class:(i+1)*tr_per_class,:] = temp.T
		temp = digitQueues[:,val_per_class+tr_per_class:2*val_per_class+tr_per_class,i]
		valX[i*val_per_class:(i+1)*val_per_class,:] = temp.T
		trainY[i*tr_per_class:(i+1)*tr_per_class] = i
		valY[i*val_per_class:(i+1)*val_per_class,:] = i

	# nearest neighbors
	if runNearestNeighbors:

		pass
		# import pdb; pdb.set_trace()

		# from sklearn.neighbors import KNeighborsClassifier
		# neigh = KNeighborsClassifier(n_neighbors=numNeighbors)
		# neigh.fit(trainX, trainY)
		# y_hat = neigh.predict(valX)
		# nn_acc = neigh.score(valX, valY)

		# # Accuracy:
        # overallAcc = round(100* sum(yHat == valY) / len(valY) )
        # for i = classLabels
        #     inds = find(valY == classLabels(i))
        #     classAcc(i) = round(100*sum( yHat(inds) == valY(inds) ) / length(valY(inds) ) )
        #
        # disp( [ type,  ': ', num2str(trPerClass), ' training samples per class. ',...
        #     ' Accuracy = ', num2str(overallAcc), '%. numNeigh = ', num2str(numNeighbors), ...
        #     '. Class accs (%): ', num2str(classAcc) ] )

	# load an existing moth, or create a new moth
	if use_existing_conn_matrices:
		params_fname = os.path.join(save_params_folder, 'modelParams.pkl')
		# load modelParams
		with open(params_fname,'rb') as f:
			modelParams = dill.load(f)
	else:
		# Load template params
		from support_functions.params import ModelParams
		modelParams = ModelParams(nF=len(activePixelInds), goal=goal)

		# Now populate the moth's connection matrices using the modelParams
		modelParams = init_connection_matrix(modelParams)

		# save params to file (if save_params_folder not empty)
		if save_params_folder:
			if not os.path.isdir(save_params_folder):
				os.mkdir(save_params_folder)
				# pickle parameters for other branch of if construct
				params_fname = os.path.join(save_params_folder, 'modelParams.pkl')
				dill.dump(modelParams, open(params_fname, 'wb'))

	modelParams.trueClassLabels = class_labels # misc parameter tagging along
	modelParams.saveAllNeuralTimecourses = save_all_neural_timecourses

	# # Define the experiment parameters, including book-keeping for time-stepped
	# # 	evolutions, eg when octopamine occurs, time regions to poll for digit
	# # 	responses, windowing of firing rates, etc
	# experimentParams = experimentFn( tr_classes, class_labels, val_per_class )

	# Load experiment params, including book-keeping for time-stepped
	# 	evolutions, eg when octopamine occurs, time regions to poll for digit
	# 	responses, windowing of Firing rates, etc
	experimentParams = ExpParams(tr_classes, class_labels, val_per_class)

#-------------------------------------------------------------------------------

	# 3. run this experiment as sde time-step evolution:
	simResults = sde_wrap( modelParams, experimentParams, digitQueues )

#-------------------------------------------------------------------------------

	# Experiment Results: EN behavior, classifier calculations:
	if save_results_image_folder:
		if not os.path.isdir(save_results_image_folder):
			os.mkdir(save_results_image_folder)

	# Process the sim results to group EN responses by class and time:
	respOrig = view_EN_resp(simResults, modelParams, experimentParams,
		show_EN_plots, class_labels, screen_size, results_filename, save_results_image_folder)

	# Calculate the classification accuracy:
	# for baseline accuracy function argin, substitute pre- for post-values in respOrig:
	respNaive = copy.deepcopy(respOrig)
	for i, resp in enumerate(respOrig):
		respNaive[i]['postMeanResp'] = resp['preMeanResp'].copy()
		respNaive[i]['postStdResp'] = resp['preStdResp'].copy()
		respNaive[i]['postTrainOdorResp'] = resp['preTrainOdorResp'].copy()

	# 1. Using Log-likelihoods over all ENs:
	# Baseline accuracy:
	outputNaiveLogL = classify_digits_log_likelihood( respNaive )
	print( 'LogLikelihood:' )
	print( f"Naive Accuracy: {round(outputNaiveLogL['total_acc'])}" + \
		f"#, by class: {np.round(outputNaiveLogL['acc_perc'])} #.   ")

	# Post-training accuracy using log-likelihood over all ENs:
	outputTrainedLogL = classify_digits_log_likelihood( respOrig )
	print( f"Trained Accuracy: {round(outputTrainedLogL['total_acc'])}" + \
		f"#, by class: {np.round(outputTrainedLogL['acc_perc'])} #.   ")

	# 2. Using single EN thresholding:
	outputNaiveThresholding = classify_digits_thresholding( respNaive, 1e9, -1, 10 )
	outputTrainedThresholding = classify_digits_thresholding( respOrig, 1e9, -1, 10 )

	# append the accuracy results, and other run data, to the first entry of respOrig:
	respOrig[0]['modelParams'] = modelParams  # will include all connection weights of this moth
	respOrig[0]['outputNaiveLogL'] = outputNaiveLogL
	respOrig[0]['outputTrainedLogL'] = outputTrainedLogL
	respOrig[0]['outputNaiveThresholding'] = outputNaiveThresholding
	respOrig[0]['outputTrainedThresholding'] = outputTrainedThresholding
	respOrig[0]['matrixParamsFilename'] = matrix_params_filename
	respOrig[0]['K2Efinal'] = simResults['K2Efinal']

	if save_results_data_folder:
		if not os.path.isdir(save_results_data_folder):
			os.mkdir(save_results_data_folder)

		# save results data
		results_fname = os.path.join(save_results_data_folder, f'{results_filename}_{run}.pkl')
		dill.dump(respOrig, open(results_fname, 'wb'))
		# open via:
		# >>> with open(results_fname,'rb') as f:
    	# >>> 	B = dill.load(f)

		print(f'Results saved to: {results_fname}')

print('         -------------All done-------------         ')

runDuration = time.time() - runStart
print(f'{__file__} executed in {runDuration/60:.3f} minutes')

# MIT license:
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# import pdb; pdb.set_trace()
