# Server setup
HOST = '0.0.0.0'     # Listen on all available interfaces
DEFAULT_PORT = 8000  # Port number

# Wavefront reconstruction parameters
N_SPOTS = 4         # Number of spots not including the center spot
N_MODES = 5         # Number of Zernike polynomials not including piston
ROTATION_ANGLE = 0  # Rotation angle in degrees
SCALE = 1           # Scale factor
FLIP = 1            # Set to -1 to flip sign of Zernike

# (x, y) coordinates of spot positions mapped on the pupil (slope sampling points).
# Radius of pupil is 1.
SPOT_POSITIONS = [
    [0.5, 0.5],
    [0.5, -0.5],
    [-0.5, 0.5],
    [-0.5, -0.5]
    ]