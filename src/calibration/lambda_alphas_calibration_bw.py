import numpy as np
from sklearn.neighbors import KernelDensity
from scipy.stats import binom
import matplotlib.pyplot as plt

from .lambda_alphas_access import save_lambda
from ..bandwidth_test import is_unimodal_kde, critical_bandwidth
from ..util.bootstrap_MPI import expected_value_above


class XSampleBW(object):

    def __init__(self, N):
        self.N = N
        data = np.random.randn(N)
        data = data[np.abs(data) < 1.5]  # avoiding spurious bumps in the tails
        self.h_crit = critical_bandwidth(data)
        self.kde_h_crit = KernelDensity(kernel='gaussian', bandwidth=self.h_crit).fit(data.reshape(-1, 1))

    def is_unimodal_resample(self, lambda_val):
        data = self.kde_h_crit.sample(self.N).reshape(-1)
        data = data[np.abs(data) < 1.5]  # avoiding spurious bumps in the tails
        return is_unimodal_kde(self.h_crit*lambda_val, data)

    def probability_of_unimodal_above(self, lambda_val, gamma):
        '''
            G_n(\lambda) = P(\hat h_{crit}^*/\hat h_{crit} <= \lambda)
                         = P(\hat h_{crit}^* <= \lambda*\hat h_{crit})
                         = P(KDE(X^*, \lambda*\hat h_{crit}) is unimodal)
        '''
        return expected_value_above(lambda: self.is_unimodal_resample(lambda_val), gamma, max_samp=5000, mpi=True)


class XSampleShoulderBW(XSampleBW):

    def __init__(self, N):
        self.N = N
        N1 = binom.rvs(N, 1.0/17)
        print "N1 = {}".format(N1)
        N2 = N - N1
        m1 = -1.25
        s1 = 0.25
        data = np.hstack([s1*np.random.randn(N1)+m1, np.random.randn(N2)])
        data = data[np.abs(data) < 1.5]
        self.h_crit = critical_bandwidth(data)
        self.kde_h_crit = KernelDensity(kernel='gaussian', bandwidth=self.h_crit).fit(data.reshape(-1, 1))

sampling_dict = {'normal': XSampleBW, 'shoulder': XSampleShoulderBW}


def print_bound_search(fun):

    def printfun(lambda_val):
        print "Testing if {} is upper bound for lambda_alpha".format(lambda_val)
        res = fun(lambda_val)
        print "{} is".format(lambda_val)+" not"*(not res)+" upper bound for lambda_alpha."
        return res

    return printfun


def h_crit_scale_factor(alpha, null='normal', lower_lambda=0, upper_lambda=2.0):

    sampling_class = sampling_dict[null]

    @print_bound_search
    def is_upper_bound_on_lambda(lambda_val):
        '''
            P(P(G_n(lambda)) > 1 - alpha) > alpha
                => lambda is upper bound on lambda_alpha
        '''
        return expected_value_above(lambda: sampling_class(N).probability_of_unimodal_above(lambda_val, 1-alpha), alpha)

    def save_upper(lambda_bound):
        save_lambda(lambda_bound, 'bw', null, alpha, upper=True)

    def save_lower(lambda_bound):
        save_lambda(lambda_bound, 'bw', null, alpha, upper=False)

    lambda_tol = 1e-4

    N = 10000
    #seed = np.random.randint(1000)
    seed = 846
    print "seed = {}".format(seed)
    np.random.seed(seed)

    if lower_lambda == 0:
        new_lambda = upper_lambda/2
        while is_upper_bound_on_lambda(new_lambda):
            upper_lambda = new_lambda
            save_upper(upper_lambda)
            new_lambda = (upper_lambda+lower_lambda)/2
        lower_lambda = new_lambda
        save_lower(lower_lambda)

    while upper_lambda-lower_lambda > lambda_tol:
        new_lambda = (upper_lambda+lower_lambda)/2
        if is_upper_bound_on_lambda(new_lambda):
            upper_lambda = new_lambda
            save_upper(upper_lambda)
        else:
            lower_lambda = new_lambda
            save_lower(lower_lambda)

    return (upper_lambda+lower_lambda)/2


if __name__ == '__main__':
    if 0:
        print "h_crit_scale_factor(0.30, 0, 2.0) = {}".format(h_crit_scale_factor(0.30, 0, 2.0))  # alpha=0.05 => lambda_alpha=1.12734985352

    if 0:
        xsamp = XSampleShoulderBW(100000)
        x = np.linspace(-2, 2)
        plt.plot(x, np.exp(xsamp.kde_h_crit.score_samples(x.reshape(-1, 1))))
        plt.show()
