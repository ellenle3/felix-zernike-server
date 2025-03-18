import argparse
import warnings
import numpy as np
from astropy.io import fits
from zernike import zernike_derv, make_gamma_matrices
from config import *

class ZernikeReconstructor:
    """Modal wavefront reconstruction for a Shack-Hartmann wavefront sensor with
    a Zernike basis. The solution is based on Southwell (1980) with the geometry
    in Fig. 1C (can also be used for Fig. 1A).
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
        """Creates normalization coefficients for Noll Zernike polynomials.
        """
        norm = np.ones(cls.n_modes + 1)
        norm *= cls.scale
        # flip and rotation not implemented yet...
        return norm

    @classmethod
    def make_imat(cls, norm):
        """Creates Zernike to slopes matrix without piston.

        Parameters
        ----------

        """
        A = np.zeros((2*cls.n_spots, cls.n_modes))
        # Apply rotation by rotating the spot positions
        rot_matrix = np.array([ [np.cos(cls.rot), -np.sin(cls.rot)],
                                [np.sin(cls.rot),  np.cos(cls.rot)] ])
        points = np.dot(rot_matrix, cls.spot_positions.T).T

        for k in range(cls.n_modes):
            # Noll index would usually be k + 1... Skip piston, so k + 2.
            dervx, dervy = zernike_derv(k+2, cls.gammax, cls.gammay, points)
            for i in range(cls.n_spots):
                A[i,k] = norm[k] * dervx[i]
                A[i+cls.n_spots,k] = norm[k] * dervy[i]
        return A
    
    @classmethod
    def invert_imat(cls, A):
        """Creates slopes to Zernike matrix from imat.
        """
        A_inv = np.linalg.pinv(A)
        return A_inv

    @classmethod
    def estimate_wavefront(cls, slopes):
        """Reconstructs the wavefront from the slope measurements.

        References: Southwell (1980) and Herrmann (1979)

        Parameters
        ----------
        slopes: nd_array of size 2*n_spots
            The slope measurements in the x and y directions. x values first,
            then y values.

        Returns
        ------
        a_z: nd_array of size n_zernike
            Zernike coefficients.
        """
        a_z = np.zeros(cls.n_modes)

        pass

    def __init__(self):
        """Initializes the Slopes class.

        Parameters
        ----------
        n_zernike : int, optional
            Number of Noll Zernike polynomials excluding piston. E.g., n_zernike = 5
            yields tip, tilt, focus, astig1, astig2.
        rot: float, optional
            Rotation angle in degrees. Default is 0.
        scale: float, optional
            Scale factor. Default is 1.
        flip: int, optional
            If 1, no flip. If -1, flips the Zernike coefficients. Default is 1.

        Returns
        -------
        None
        """
        self.recent_timestamp = None
        self.slopes = None

        # Initialize zernike to slopes matrix
        self.norm = self.make_norm_coeffs()
        self.A = self.make_imat(self.norm)
        self.z2s = self.invert_imat(self.A)

    def points_to_slopes(self, points):
        """Converts x, y points to slopes.

        Parameters
        ----------
        points: nd_array of shape (2, n_spots + 1)
            The x, y coordinates of the spots. The first element should be the
            coordinates of the center point.
        
        Returns
        -------
        out: nd_array of shape (2, n_spots)
        """
        pass


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
    
def main(Npts, Nmodes):
    """Saves a FITS file with the x and y slopes for each Zernike mode.
    """
    gammax, gammay = make_gamma_matrices(Nmodes)

    # Points to sample    
    subap_size = 2 / Npts
    xpts = np.arange(-1 + subap_size/2, 1, subap_size)
    ypts = np.arange(-1 + subap_size/2, 1, subap_size)
    X, Y = np.meshgrid(xpts, ypts, indexing="ij")
    points = np.column_stack([X.ravel(), Y.ravel()])

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