import argparse
import warnings
import numpy as np
from scipy.special import factorial
from astropy.io import fits
from config import *

def poly_radial(m, n, rho):
    """Returns the radial part of the Zernike polynomial.
    
    Reference: Noll (1976).
    
    Parameters
    ----------
    m: int
        The azimuthal frequency as defined by Noll. Requires m <= n and n - abs(m) is even.
    n: int
        The radial degree as defined by Noll. Requires m <= n and n - abs(m) is even.
    rho: nd_array
        A 1D or 2D array of normalized radius rho in polar coordinates.
        
    Returns
    -------
    out: nd_array of shape rho.shape
        The polynomial evaluated for each value of rho. 
    """
    m = np.abs(m)
    s = np.arange(0, (n-m)/2 + 1, 1)
    # Argument of the sum for one value of s and rho
    arg = lambda s1, rho1: (-1)**s1 * factorial(n-s1) * rho1**(n-2*s1) \
                        / ( factorial(s1) * factorial((n+m)/2-s1)      \
                           * factorial((n-m)/2-s1) )
    # Compute the argument over every s and rho first, then collapse along the appropriate
    # dimension to get the sum. This is significantly faster than iterating over the array and
    # computing the sum for each value of rho.
    if len(rho.shape)==1:
        # 1D array of rho
        res = arg(s[None, :], rho[:, None])
        return np.sum(res, axis=1)
    else:
        # 2D array of rho
        sarr = np.ones(rho.shape + (len(s),))
        sarr[:,:] = s
        # force sarr and rho to have the same shape
        res = arg(sarr, rho[:,:,None])
        return np.sum(res, axis=-1)

def poly_angular(m, n, theta):
    """Returns the angular part of the Zernike polynomial. If m = 0, this function returns an
    array of constants.
    
    Reference: Noll (1976).
    
    Parameters
    ----------
    m: int
        The azimuthal frequency as defined by Noll. Requires m <= n and n - abs(m) is even.
    n: int
        The radial degree as defined by Noll. Requires m <= n and n - abs(m) is even.
    theta: nd_array
        A 1D or 2D array of angle theta in polar coordinates, in radians.
    
    Returns
    -------
    out: nd_array of shape theta.shape
        The polynomial evaluated for each value of theta. 
    """
    if m != 0:
        if m > 0:
            return np.sqrt(n + 1) * np.sqrt(2) * np.cos(m*theta)
        else:
            m = np.abs(m)
            return np.sqrt(n + 1) * np.sqrt(2) * np.sin(m*theta)
    # Make an array of constants for m = 0
    return np.ones_like(theta) * np.sqrt(n + 1)

def noll_zernike_index(j):
    """Returns m and n from the Noll index j.
    
    Reference: Townson et al. (2019)
               AOtools v1.0.1
               https://github.com/AOtools/aotools
               
    Parameters
    ----------
    j: int
        The mode ordering number as defined by Noll.
    
    Returns
    -------
    m: int
        The azimuthal degree.
    n: int
        The radial degree.
    """
    # This is copied almost verbatim from AOtools's source code, specifically the zernIndex
    # function. See reference for more info.
    assert j > 0, "j must be greater than or equal to 1"
    assert int(j)==j, "j must be an integer"
    
    n = int((-1.+np.sqrt(8*(j-1)+1))/2.)
    p = (j-(n*(n+1))/2.)
    k = n%2
    m = int((p+k)/2.)*2 - k

    if m!=0:
        if j%2==0:
            s=1
        else:
            s=-1
        m *= s

    return [m, n]

def zernike_mn(m, n, rho, theta):
    """Returns a Zernike polynomial defined by m and n. The behavior of this function
    is slightly different than in zernike_generator.ipynb.
    
    Reference: Noll (1976).
    
    Parameters
    ----------
    m: int
        The azimuthal degree. m > 0 means that the polynomial is even, m < 0 for odd.
        Requires m <= n and n - abs(m) is even.
    n: int
        The radial degree. Requires m <= n and n - abs(m) is even.
    rho: nd_array
        A 1D normalized radius rho in polar coordinates
    theta: nd_array of shape rho.shape
        A 1D array of angle theta in polar coordinates, in radians.
        
    Returns
    -------
    out: nd_array of size (rho.size)
        The Zernike polynomial defined by m and n evaluated over the given values of rho
        and theta.
    """
    assert m==int(m), "m must be an integer"
    assert n==int(n), "n must be an integer"
    assert m <= n, "m must be less than or equal to n"
    assert (n - np.abs(m)) % 2 == 0, "n - abs(m) must be even"
    assert rho.shape == theta.shape, "rho and theta must have the same shape"

    return poly_radial(m, n, rho) * poly_angular(m, n, theta)

def noll_zernike_j(j, rho, theta):
    """Returns a Zernike polynomial defined by the Noll index j.
    
    Parameters
    ----------
    j: int
        The mode ordering number as defined by Noll.
    rho: nd_array
        A 1D array of normalized radius rho in polar coordinates.
    theta: nd_array
        A 1D array of angle theta in polar coordinates, in radians.
        
    Returns
    -------
    out: nd_array
        The Zernike polynomial defined by j evaluated over the given values of rho and theta.
    """
    m, n = noll_zernike_index(j)
    return zernike_mn(m, n, rho, theta)

def generate_zernike_wavefront(a_j, points):
    """Returns a wavefront composed of Zernike polynomials. The coefficients a_j define the
    shape of the wavefront.
    
    Parameters
    ----------
    a_j: nd_array
        An array containing the coefficients [a_1, a_2, ..., a_j] of the Zernike modes.
    points: nd_array of shape (2, n_pts)
        [rho, theta] coordinates to evaluate.

    Returns
    -------
    out: nd_array of size (rho.size, theta.size)
        The wavefront error evaluated over the given values of rho and theta.
    """
    wfe = np.zeros(points.shape[0])
    rho, theta = points.T
    for j in range(1, len(a_j)+1):
        # Noll index j starts at 1 but array indexing in Python starts at 0...
        wfe += a_j[j-1] * noll_zernike_j(j, rho, theta)
    return wfe

def generate_zernike_wavefront_cartesian(a_j, pts):
    """Returns the wavefront error over the pupil. Pupil radius is set to 1.

    Parameters
    ----------
    a_j: nd_array
        An array containing the coefficients [a_1, a_2, ..., a_j] of the Zernike modes.
    points: nd_array of shape (2, n_pts)
        [x, y] coordinates to evaluate.
    
    Returns
    -------
    out: nd_array of size (x.size, y.size)
        The wavefront error in units of a_j.
    """
    # generate a grid of rho and theta from given x and y
    xx = pts.T[0]
    yy = pts.T[1]

    rho = np.sqrt(xx**2 + yy**2)
    # arctan2 instead of arctan to convert the angle depending on the quadrant
    theta = np.arctan2(yy, xx)

    points_polar = np.column_stack([rho, theta])
    wfe = generate_zernike_wavefront(a_j, points_polar)

    # mask out everything outside of the aperture
    wfe = np.where(xx**2 + yy**2 > 1, 0, wfe)
    return wfe

def make_gamma_matrices(n_modes):
    """
    The derivative of a Zernike polynomial can be expressed as a linear combination
    of Zernikes. Use the matrices gammax and gammay to store the coefficients
    of the linear combination.

    References: Noll (1975)
    """
    gammax = np.zeros((n_modes, n_modes))
    gammay = np.zeros((n_modes, n_modes))

    for j in range(1, n_modes+1):
        for j1 in range(1, j+1):
            m, n = noll_zernike_index(j)
            m1, n1 = noll_zernike_index(j1)

            # Noll remaps the indices so m is always positive
            m = abs(m)
            m1 = abs(m1)

            # magnitudes - same for x and y
            mag = 0
            if (m==0 or m1==0):
                mag = np.sqrt(2*(n+1)*(n1+1))
            elif (m!=0 and m1!=0):
                mag = np.sqrt((n+1)*(n1+1))

            # For a particular m, only m' = m +/- 1 gives non-zero elements.
            if (abs(m1-m) == 1):
                # x conditions - non-zero elements are for j and j' either both even
                # or both odd. Except for m or m' == 0, in which case only even j or
                # j' give a non-zero result. All elements are positive.
                if (j%2 == j1%2) and (m!=0 and m1!=0):
                    gammax[j-1, j1-1] = mag

                # This is supposed to be the second half of rule b in Noll's paper,
                # but there is either an error in the paper or it is worded very
                # poorly. Modified conditions here to match Tables II and III.
                elif (m==0 and j1%2==0):
                    gammax[j-1, j1-1] = mag
                elif (m1==0 and j%2==0):
                    gammax[j-1, j1-1] = mag

                # y conditions - non-zero elemetns are for j and j' either even/odd
                # or odd/even. Except for m or m' == 0, in which case only odd j or
                # j' give a non-zero result.
                if (j%2 != j1%2) and (m!=0 and m1!=0):
                    gammay[j-1, j1-1] = mag

                elif (m==0 and j1%2==1):
                    gammay[j-1, j1-1] = mag
                elif (m1==0 and j%2==1):
                    gammay[j-1, j1-1] = mag

                # Negative sign for m' = m + 1 and odd j, or m' = m - 1 and even j.
                if ((m1 == m+1) and (j%2==1)) or ((m1 == m-1) and (j%2==0)):
                    gammay[j-1, j1-1] *= -1
                
    return gammax, gammay
            
def zernike_derv(j, gammax, gammay, points):
    """Computes the derivative of the kth order Zernike polynomial as a linear
    combination of Zernikes up to the nth order.

    Parameters
    ----------
    j: int
        The Noll Zernike index of the mode to differentiate.
    gammax: nd_array
        Gamma matrix for x as defined by Noll (1975).
    gammay: nd_array
        Gamma matrix for y as defined by Noll (1975).
    points: nd_array of shape (2, n_spots)
        Points to evaluate.

    Returns
    -------
    dervx: nd_array of shape (n_spots)
        Derivative of the Zernike polynomial along x.
    dervy: nd_array of shape (n_spots)
        Derivative of the Zernike polynomial along y.
    """
    # A row of gammax essentially serves as Zernike coefficients
    xcoeffs = gammax[j-1]
    dervx = generate_zernike_wavefront_cartesian(xcoeffs, points)

    # Repeat for gammay
    ycoeffs = gammay[j-1]
    dervy = generate_zernike_wavefront_cartesian(ycoeffs, points)
    return dervx, dervy

def make_southwell_points(Npts):
    """Creates an array of points that sample the pupil evenly according to the
    sampling geometry shown in Southwell (1980) Fig 1A. Radius of pupil is 1.

    Parameters
    ----------
    Npts: int
        Number of points to sample along one direction.
    
    Returns
    -------
    out: np.ndarray
        Array of points in the Southwell geometry for a SHWFS.
    """
    subap_size = 2 / Npts
    xpts = np.arange(-1 + subap_size/2, 1, subap_size)
    ypts = np.arange(-1 + subap_size/2, 1, subap_size)
    x, y = np.meshgrid(xpts, ypts, indexing="ij")
    return np.column_stack([x.ravel(), y.ravel()])

class ZernikeReconstructor:
    """Modal wavefront reconstruction for a Shack-Hartmann wavefront sensor with
    a Zernike basis. The solution is based on Southwell (1980) with the geometry
    in Fig. 1A.
    """
    n_spots = N_SPOTS     # Number of spots not including the center spot
    n_modes = N_MODES     # Number of Zernike polynomials not including piston
    rot = np.radians(ROTATION_ANGLE)
    scale = SCALE         # Scale factor
    flip = FLIP           # Set to -1 to flip sign of Zernike

    # Derivative matrices, plus 1 to skip piston
    gammax, gammay = make_gamma_matrices(n_modes + 1)

    # Spot positions on the pupil
    spot_positions = np.array(SPOT_POSITIONS)

    @classmethod
    def make_norm_coeffs(cls):
        """Creates normalization coefficients for Noll Zernike polynomials without
        piston.
        """
        norm = np.ones(cls.n_modes)
        norm *= cls.scale

        # Flip sign of all indices with negative azimuthal frequency
        for k in range(N_MODES):
            m, n = noll_zernike_index(k + 2)
            if m < 0:
                norm[k] *= cls.flip

        return norm

    @classmethod
    def make_imat(cls, norm):
        """Creates Zernike to slopes matrix without piston.
        """
        A = np.zeros((2*cls.n_spots, cls.n_modes))
        points = cls.spot_positions

        for k in range(cls.n_modes):
            # Noll index would usually be k + 1... Skip piston, so k + 2.
            dervx, dervy = zernike_derv(k+2, cls.gammax, cls.gammay, points)
            for i in range(cls.n_spots):
                A[i,k] = norm[k] * dervx[i]
                A[i+cls.n_spots,k] = norm[k] * dervy[i]
        return A
    
    @staticmethod
    def invert_imat(A):
        """Creates slopes to Zernike matrix from imat.
        """
        A_inv = np.linalg.pinv(A)
        return A_inv

    def __init__(self):
        """Initializes the ZernikeReconstructor object. Define FELIX parameters
        in config.py.
        """
        self.slopes = None

        # Initialize zernike to slopes matrix
        self.norm = self.make_norm_coeffs()
        self.A = self.make_imat(self.norm)
        self.s2z = self.invert_imat(self.A)

    def update_slopes(self, slopes):
        """Updates slope data.
        """
        self.slopes = slopes

    def slopes_to_zernikes(self):
        """Converts current slope data to Zernike coefficients.
        """
        if self.slopes is None:
            warnings.warn("No slope data. Returning zeros.")
            return np.zeros(self.n_modes)
        
        return np.dot(self.s2z, self.slopes)

def main(Npts, Nmodes):
    """Saves a FITS file with the x and y slopes for each Zernike mode.
    """
    gammax, gammay = make_gamma_matrices(Nmodes)
    points = make_southwell_points(Npts)

    # Compute derivatives for each subaperture
    slopesx = np.zeros((Nmodes, Npts, Npts))
    slopesy = np.zeros((Nmodes, Npts, Npts))
    for i in range(Nmodes):
        dervx, dervy = zernike_derv(i+1, gammax, gammay, points)
        slopesx[i] = np.reshape(dervx, (Npts, Npts))
        slopesy[i] = np.reshape(dervy, (Npts, Npts))
    
    hdu = fits.PrimaryHDU(np.concatenate((slopesx, slopesy), axis=2))
    hdu.writeto("data/slopesXandY.fits", overwrite=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Zernike slope offset generation")
    parser.add_argument('--Npts', type=int, default=12, help="Number of points to sample along one direction")
    parser.add_argument('--Nmodes', type=int, default=36, help="Number of Zernike modes")

    args = parser.parse_args()
    main(args.Npts, args.Nmodes)