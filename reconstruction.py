import argparse
import warnings
import numpy as np
from astropy.io import fits
from zernike import zernike_derv, make_gamma_matrices, noll_zernike_index
from config import *

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
        # Apply rotation by rotating the spot positions - I think this is wrong...
        #rot_matrix = np.array([ [np.cos(cls.rot), -np.sin(cls.rot)],
        #                        [np.sin(cls.rot),  np.cos(cls.rot)] ])
        #points = np.dot(rot_matrix, cls.spot_positions.T).T
        points = cls.spot_positions

        for k in range(cls.n_modes):
            # Noll index would usually be k + 1... Skip piston, so k + 2.
            dervx, dervy = zernike_derv(k+2, cls.gammax, cls.gammay, points)
            for i in range(cls.n_spots):
                A[i,k] = norm[k] * dervx[i]
                A[i+cls.n_spots,k] = norm[k] * dervy[i]
        return A
    
    @staticmethod
    def invert_imat( A):
        """Creates slopes to Zernike matrix from imat.
        """
        A_inv = np.linalg.pinv(A)
        return A_inv

    def __init__(self):
        """Initializes the ZernikeReconstructor object. Define FELIX parameters
        in config.py.
        """
        self.recent_timestamp = None
        self.slopes = None

        # Initialize zernike to slopes matrix
        self.norm = self.make_norm_coeffs()
        self.A = self.make_imat(self.norm)
        self.z2s = self.invert_imat(self.A)

    def update_slopes(self, timestamp, X_values, Y_values):
        """Updates slope data.
        """
        # Expecting n_spots for the slopes + 1 for the coordinates of the central
        # spot. Mutliply by 2 for the cal data and input data.
        assert len(X_values) == 2 * (self.n_spots + 1), f"X_values do not match n_spots={self.n_spots}: {X_values}"
        assert len(Y_values) == 2 * (self.n_spots + 1), f"Y_values do not match n_spots={self.n_spots}: {Y_values}"

        self.recent_timestamp = timestamp

        # Index of X and Y values for input data
        idx_in = self.n_spots + 1

        cal_points = np.array([X_values[:idx_in], Y_values[:idx_in]]).T
        input_points = np.array([X_values[idx_in:], Y_values[idx_in:]]).T

        # Get center points for subapertures using calibration data
        subap_centers = cal_points[1:] - cal_points[0]

        # If you don't want tip/tilt to be measured, replace cal_points[0] with
        # input_points[0] in the line below.
        input_slopes = input_points[1:] - cal_points[0] - subap_centers

        # Reformat to 1D array of x slopes then y slopes
        self.slopes =  np.array([input_slopes.T[0], input_slopes.T[1]]).flatten()

    def slopes_to_zernikes(self):
        """Converts current slope data to Zernike coefficients.
        """
        if self.slopes is None:
            warnings.warn("No slope data. Returning zeros.")
            return np.zeros(self.n_modes)
        
        return np.dot(self.z2s, self.slopes)
    
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
    hdu.writeto("slopesXandY.fits", overwrite=True)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Zernike slope offset generation")
    parser.add_argument('--Npts', type=int, default=12, help="Number of points to sample along one direction")
    parser.add_argument('--Nmodes', type=int, default=36, help="Number of Zernike modes")

    args = parser.parse_args()
    main(args.Npts, args.Nmodes)