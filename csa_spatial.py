'''
@author: Daniel Hjertholm

Tests for spatially structured networks generated by CSA. 
'''

import numpy as np
import numpy.random as rnd
import random
import csa

from testsuite.spatial_test import SpatialTester


class CSA_SpatialTester(SpatialTester):
    '''Tests for spatially structured networks generated by CSA.'''

    def __init__(self, L, N, kernel_name, kernel_params=None):
        '''
        Construct a test object.

        Parameters
        ----------
            L            : Side length of area / volume.
            N            : Number of nodes.
            kernel_name  : Name of kernel to use.
            kernel_params: Dict with params to update.
        '''

        SpatialTester.__init__(self, L=L, N=N)

        assert kernel_name == 'gaussian', 'Currently, only a Gaussian kernel' \
                              'is supported by this implementation of the CSA.'
        default_params = {'p_center': 1., 'sigma': self._L / 4.,
                          'mean': 0., 'c': 0.}
        self._params = default_params
        if kernel_params is not None:
            assert kernel_params.keys() == ['sigma'], \
                'Only valid kernel parameter is "sigma".'
            self._params.update(kernel_params)

        self._kernel = lambda D: (self._params['c'] + self._params['p_center'] *
                                  np.e ** -((D - self._params['mean']) ** 2 /
                                            (2. * self._params['sigma'] ** 2)))

    def _reset(self, seed):
        '''
        Seed the PRNG.
        
        Parameters
        ----------
            seed: PRNG seed value. 
        '''

        if seed is None:
            seed = random.randint(0, 10 ** 10)
        seed = 2 * seed # Reduces probability of overlapping seed values.
        random.seed(seed) # CSA uses random.
        rnd.seed(seed + 1) # _get_expected_distribution uses numpy.random.

    def _build(self):
        '''Create populations.'''

        def pos(idx):
            assert idx == 0, 'This population has only one node.'
            return (0.5, 0.5)
            # Source node is located at (0.5, 0.5) because csa.random2d() can
            # only scatter nodes on the unit square.
        self._g1 = pos
        self._g2 = csa.random2d(self._N)
        self._d = csa.euclidMetric2d(self._g1, self._g2)

    def _connect(self):
        '''Connect populations.'''

        sigma = self._params['sigma']
        cutoff = self._max_dist
        self._cs = csa.cset(csa.cross([0], xrange(self._N - 1)) *
            (csa.random * (csa.gaussian(sigma, cutoff) * self._d)), 1.0, 1.0)

    def _distances(self):
        '''Return distances to all nodes in target population.'''

        return [self._d(0, i) for i in xrange(0, self._N)]

    def _target_distances(self):
        '''Return distances from source node to connected nodes.'''

        target_nodes = [c[1] for c in self._cs]
        return [self._d(0, t) for t in target_nodes]

    def _positions(self):
        '''Return positions of all nodes.'''

        return [self._g2(i) for i in xrange(0, self._N)]

    def _target_positions(self):
        '''Return positions of all connected target nodes.'''

        return [self._g2(c[1]) for c in self._cs]


class Spatial2DTester(CSA_SpatialTester):
    '''Tests for 2D spatially structured networks generated by CSA.'''

    def __init__(self, L, N, kernel_name, kernel_params=None):
        '''
        Construct a test object.

        Parameters
        ----------
            L            : Side length of area / volume.
            N            : Number of nodes.
            kernel_name  : Name of kernel to use.
            kernel_params: Dict with params to update.
            '''

        self._dimensions = 2
        CSA_SpatialTester.__init__(self, L=L, N=N, kernel_name=kernel_name,
                                    kernel_params=kernel_params)


class Spatial3DTester(CSA_SpatialTester):
    '''Tests for 3D spatially structured networks generated by CSA.'''

    def __init__(self, *args, **kwargs):
        raise NotImplementedError('CSA does currently not support ' \
                                  'construction of 3D spatial networks.')


if __name__ == '__main__':
    test = Spatial2DTester(L=1.0, N=10000, kernel_name='gaussian')
    ks, p = test.ks_test(control=False, seed=0)
    print 'p-value of KS-test:', p
    z, p = test.z_test(control=False, seed=0)
    print 'p-value of Z-test:', p
    test.show_network()
    test.show_PDF()
    test.show_CDF()
