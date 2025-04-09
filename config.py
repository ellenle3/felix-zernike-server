# Wavefront reconstruction parameters
N_SPOTS = 4         # Number of spots not including the center spot
N_MODES = 7         # Number of Zernike polynomials not including piston
ROTATION_ANGLE = 45  # Rotation angle in degrees
SCALE = 1           # Scale factor
FLIP = 1            # Set to -1 to flip sign of Zernike

# (x, y) coordinates of spot positions mapped on the pupil (slope sampling points).
# Radius of pupil is 1.
# Note: There is a function in reconstruction.py called make_southwell_points()
# that might be helpful if an even grid of spots is used. However, for FELIX if
# the number of pyramid facets are increased it may not follow Southwell's geometry.
import numpy as np

def _make_spot_positions(rot):
    """Makes spot positions for the given rotation angle.

    Parameters
    ----------
    rot : float
        Rotation angle in degrees.
    """
    default_spots = np.array([
        [0.5, 0.5],
        [0.5, -0.5],
        [-0.5, 0.5],
        [-0.5, -0.5]
        ])

    rot *= np.pi / 180
    rot_matrix = np.array([ [np.cos(rot), -np.sin(rot)],
                        [np.sin(rot),  np.cos(rot)] ])

    new_pos = []
    for spot in default_spots:
        new_pos.append(np.dot(rot_matrix, spot))
    return new_pos
SPOT_POSITIONS = _make_spot_positions(ROTATION_ANGLE)

# Server setup
HOST = '0.0.0.0'      # Listen on all available interfaces
DEFAULT_PORT = 10488  # Port number
