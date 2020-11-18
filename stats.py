from scipy.stats import beta

def beta(alpha, beta, x):
    beta.cdf(x, alpha, beta)
