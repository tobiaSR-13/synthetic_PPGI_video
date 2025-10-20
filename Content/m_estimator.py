import numpy as np

def huber_m_estimator(data, k=1.345, tol=1e-5, max_iter=1000):
    """
    robust mean estimator for distribution with big outliers and/or corrupting distributions
    (based on Muma's robustsp package which hadn't worked in my Blender environment)
    :param data: data where mean should be estimated
    :param k: tuning constant
    :param tol: convergence tolerance
    :param max_iter: maximum iterations
    :return: estimated mean value
    """
    data = np.asarray(data)
    mu = np.median(data)  # robust initial estimate
    sigma = np.median(np.abs(data - mu)) * 1.4815  # robust scale estimate

    for _ in range(max_iter):
        residuals = (data - mu) / sigma
        weights = np.where(np.abs(residuals) <= k, 1, k / np.abs(residuals))
        mu_new = np.sum(weights * data) / np.sum(weights)

        if np.abs(mu_new - mu)/sigma < tol:
            break
        mu = mu_new

    return mu