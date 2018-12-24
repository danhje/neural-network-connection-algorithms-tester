'''
@author: Daniel Hjertholm

Tests for spatially structured networks generated by NEST. 
'''

import numpy as np
import numpy.random as rnd
import nest
import nest.topology as topo

from testsuite.spatial_test import SpatialTester


class NEST_SpatialTester(SpatialTester):
    '''Tests for spatially structured networks generated by NEST.'''

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

        nest.set_verbosity('M_FATAL')

        SpatialTester.__init__(self, L=L, N=N)

        self._constant = lambda D: self._params
        self._linear = lambda D: self._params['c'] + self._params['a'] * D
        self._exponential = lambda D: (self._params['c'] + self._params['a'] *
                                       np.e ** (-D / self._params['tau']))
        self._gauss = lambda D: (self._params['c'] + self._params['p_center'] *
                                 np.e ** -((D - self._params['mean']) ** 2 /
                                           (2. * self._params['sigma'] ** 2)))
        kernels = {
            'constant': self._constant,
            'linear': self._linear,
            'exponential': self._exponential,
            'gaussian': self._gauss}
        self._kernel = kernels[kernel_name]

        default_params = {
            'constant': 1.0,
            'linear': {'a':-np.sqrt(2) / self._L, 'c': 1.0},
            'exponential': {'a':1.0, 'c': 0.0, 'tau':-self._L /
                            (np.sqrt(2) * np.log((.1 - 0) / 1))},
            'gaussian': {'p_center': 1., 'sigma': self._L / 4.,
                         'mean': 0., 'c': 0.}}
        self._params = default_params[kernel_name]
        if kernel_params is not None:
            if kernel_name == 'constant':
                self._params = kernel_params
            else:
                self._params.update(kernel_params)

        if self._dimensions == 3:
            maskdict = {'box': {'lower_left': [-self._L / 2.] * 3,
                                'upper_right': [self._L / 2.] * 3}}
        else:
            maskdict = {'rectangular': {'lower_left': [-self._L / 2.] * 2,
                                        'upper_right': [self._L / 2.] * 2}}
        if kernel_name == 'constant':
            kerneldict = self._params
        else:
            kerneldict = {kernel_name: self._params}
        self._conndict = {'connection_type': 'divergent',
                          'mask': maskdict, 'kernel': kerneldict}

    def _reset(self, seed):
        '''
        Reset NEST and seed PRNGs.
        
        Parameters
        ----------
            seed: PRNG seed value.
        '''

        nest.ResetKernel()

        if seed is None:
            seed = rnd.randint(10 ** 10)
        seed = 3 * seed # Reduces probability of overlapping seed values.
        rnd.seed(seed)
        nest.SetKernelStatus({'rng_seeds': [seed + 1],
                              'grng_seed': seed + 2})

    def _build(self):
        '''Create populations.'''

        ldict_s = {'elements': 'iaf_neuron',
                   'positions': [[0.] * self._dimensions],
                   'extent': [self._L] * self._dimensions, 'edge_wrap': True}
        x = rnd.uniform(-self._L / 2., self._L / 2., self._N)
        y = rnd.uniform(-self._L / 2., self._L / 2., self._N)
        if self._dimensions == 3:
            z = rnd.uniform(-self._L / 2., self._L / 2., self._N)
            pos = zip(x, y, z)
        else:
            pos = zip(x, y)
        ldict_t = {'elements': 'iaf_neuron', 'positions': pos,
                   'extent': [self._L] * self._dimensions, 'edge_wrap': True}
        self._ls = topo.CreateLayer(ldict_s)
        self._lt = topo.CreateLayer(ldict_t)
        self._driver = topo.FindCenterElement(self._ls)

    def _connect(self):
        '''Connect populations.'''

        topo.ConnectLayers(self._ls, self._lt, self._conndict)

    def _distances(self):
        '''Return distances to all nodes in target population.'''

        return topo.Distance(self._driver, nest.GetLeaves(self._lt)[0])

    def _target_distances(self):
        '''Return distances from source node to connected nodes.'''

        connections = nest.GetConnections(source=self._driver)
        target_nodes = [conn[1] for conn in connections]
        return topo.Distance(self._driver, target_nodes)

    def _positions(self):
        '''Return positions of all nodes.'''

        return [tuple(pos) for pos in
                topo.GetPosition(nest.GetLeaves(self._lt)[0])]

    def _target_positions(self):
        '''Return positions of all connected target nodes.'''

        return [tuple(pos) for pos in
                topo.GetTargetPositions(self._driver, self._lt)[0]]


class Spatial2DTester(NEST_SpatialTester):
    '''Tests for 2D spatially structured networks generated by NEST.'''

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
        NEST_SpatialTester.__init__(self, L=L, N=N, kernel_name=kernel_name,
                                    kernel_params=kernel_params)


class Spatial3DTester(NEST_SpatialTester):
    '''Tests for 3D spatially structured networks generated by NEST.'''

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

        self._dimensions = 3
        NEST_SpatialTester.__init__(self, L=L, N=N, kernel_name=kernel_name,
                                    kernel_params=kernel_params)


if __name__ == '__main__':
    test = Spatial2DTester(L=1.0, N=10000, kernel_name='gaussian')
    ks, p = test.ks_test(control=False, seed=0)
    print 'p-value of KS-test:', p
    z, p = test.z_test(control=False, seed=0)
    print 'p-value of Z-test:', p
    test.show_network()
    test.show_PDF()
    test.show_CDF()
