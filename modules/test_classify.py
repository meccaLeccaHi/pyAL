#!/usr/bin/env python3

import numpy as np
from classify import roc_multi, classify_digits_log_likelihood, classify_digits_thresholding

# create dummy data
dummy_results = []
for i in range(10):
    dummy_results.append(
                {
                'odor_class':np.array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 2., 2., 2., 2.,
       2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 3., 3., 3., 3., 3., 3.,
       3., 3., 3., 3., 3., 3., 3., 3., 3., 4., 4., 4., 4., 4., 4., 4., 4.,
       4., 4., 4., 4., 4., 4., 4., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5.,
       5., 5., 5., 5., 5., 6., 6., 6., 6., 6., 6., 6., 6., 6., 6., 6., 6.,
       6., 6., 6., 7., 7., 7., 7., 7., 7., 7., 7., 7., 7., 7., 7., 7., 7.,
       7., 8., 8., 8., 8., 8., 8., 8., 8., 8., 8., 8., 8., 8., 8., 8., 9.,
       9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 3., 8., 2.,
       4., 1., 5., 9., 6., 7., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2.,
       2., 3., 3., 3., 3., 3., 3., 3., 3., 3., 3., 3., 3., 3., 3., 3., 4.,
       4., 4., 4., 4., 4., 4., 4., 4., 4., 4., 4., 4., 4., 4., 5., 5., 5.,
       5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 5., 6., 6., 6., 6., 6.,
       6., 6., 6., 6., 6., 6., 6., 6., 6., 6., 7., 7., 7., 7., 7., 7., 7.,
       7., 7., 7., 7., 7., 7., 7., 7., 8., 8., 8., 8., 8., 8., 8., 8., 8.,
       8., 8., 8., 8., 8., 8., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9.,
       9., 9., 9., 9.]),
                'post_train_resp':np.array([ 9.48384067, 10.68866832,  8.61315601,  9.78861181,  9.36538948,
        9.97120359,  9.8180303 ,  8.68916622,  8.17165416,  9.47223755,
       10.06562553,  9.58421544,  9.86210921,  9.43386927,  9.96060974,
       10.44993793, 11.1597287 ,  9.45032211, 10.18070598, 10.08316007,
       11.10589462, 10.22176177, 10.56820901, 10.21847453, 10.43651534,
        9.7268444 ,  9.99912675, 11.08001985, 11.13085488, 10.41877182,
       10.03596904, 10.1067563 , 10.03734258,  9.72760949,  9.60068383,
        9.48393241, 10.63034793,  9.5555856 , 10.38646351,  9.0676789 ,
        9.0735811 , 10.12178345, 10.34732525,  9.98266513,  8.51391452,
       10.68632267,  9.39878764, 10.63951412, 10.0628892 ,  9.34161389,
        9.81581547,  9.59418301, 10.07314521, 10.20149125, 10.10774161,
       11.20706814, 10.70153894,  9.90720154, 10.54694166, 11.4942632 ,
       10.8236142 ,  9.60362554,  9.92836285, 10.5716775 , 10.0727818 ,
        8.94387223, 10.05202681,  9.4858353 , 10.73053657,  9.59630771,
        9.8643672 ,  9.21064414, 10.96866583, 10.6859072 ,  9.69536935,
       10.42369271,  9.82827659, 10.94997211,  9.01029281, 10.94531398,
        9.98851904,  9.8342566 ,  9.74981327, 10.61454787, 10.94478584,
        9.57862373, 10.04554563, 10.23503781,  9.55995108, 10.24289087,
       10.66832242,  9.98169683, 10.05754399,  9.69287837, 10.44896854,
        9.0597882 ,  9.57623158, 10.38546711,  9.87467487,  9.56148151,
        9.86518701, 10.69430657,  9.42058539,  9.96471265,  9.92863533,
       10.08211477, 11.21026123,  9.54269602, 11.05648219, 10.0081959 ,
       10.03171193, 10.03034831, 10.17789707,  9.74169071,  9.69339046,
        9.8514267 ,  8.89457879, 10.04420706, 11.2541476 , 10.48232644,
       11.45689659, 10.0077468 , 10.01346059, 10.30408407,  9.50348039,
       10.62485302,  9.81999296,  9.87736898,  9.75747098,  9.97397621,
       11.43114612, 10.09295882, 11.05047163, 10.66615616, 11.16781688,
        9.74166164, 10.34560732, 10.15957223,  9.54053642, 10.54230655,
        9.73431235,  9.90986506,  9.97075339,  8.69099529, 10.63409141,
        9.5652583 ,  9.6481689 , 10.1073358 ,  9.5715103 , 10.16026575]),
                'post_mean_resp':np.array([ 9.53122582, 10.41535518,  9.77810927, 10.25190117, 10.01557295,
       10.13010133,  9.94536536, 10.14009835, 10.38319201,  9.88814938]),
                'post_std_resp':np.array([0.61682304, 0.50529935, 0.55325801, 0.60404227, 0.59951367,
       0.552491  , 0.44451372, 0.61904373, 0.61776464, 0.46604156]),
                }
                )

# test roc_multi
roc_multi(np.array([0,1,2]),np.array([[0,1,2],[0,1,2],[0,1,2]]))
print('roc_multi function test passed')

# test classify_digits_log_likelihood
classify_digits_log_likelihood( dummy_results )
print('classify_digits_log_likelihood function test passed')

# test classify_digits_thresholding
classify_digits_thresholding( dummy_results, 1e9, -1, 10 )
print('classify_digits_thresholding function test passed')

print('classify module tests passed')
