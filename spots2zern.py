import argparse
import numpy as np
from reconstruction import ZernikeReconstructor
from config import *


def print_coeffs(a_z):
    """Prints Zernike coefficients.

    Since we do not calculate piston, the index is printed starting from 2.
    """
    coeff_names = ["ZTIP", "ZTILT", "ZFOCUS", "ZASTIG1", "ZASTIG2", "ZCOMA1", "ZCOMA2",
                   "ZTREFOIL1", "ZTREFOIL2", "ZSPHERICAL"]
    for i,coeff in enumerate(a_z):
        if i >= len(coeff_names):
            name = f"J={i+2}".zfill(2)
        else:
            name = coeff_names[i]
        print(name + ' ' + '{:.6f}'.format(coeff))

def print_return_code(n):
    """Prints return code with an error message if it is not 0.
    """
    msg = f"CODE {n}: "
    match n:
        case 0:
            print(msg + "success")
        case 1:
            print(msg + "no input provided")
        case 2:
            print(msg + "input does not contain 8 elements")
        case 3:
            print(msg + "input points do not match N_SPOTS")
        case 4:
            print(msg + "computed zernikes are NaN")
        case _:
            print(msg + "undefined error")

def main(coords):

    recon = ZernikeReconstructor()
    a_z = np.zeros(N_MODES)

    # Reformat from [x1, y1, ... xn, yn] to [x1, ..., xn, y1, ..., yn]
    slopes = np.array([coords[::2], coords[1::2]]).flatten()

    if len(slopes) != N_SPOTS * 2:
        print_return_code(3)  # N_SPOTS doesn't match number of poitns
        print_coeffs(a_z)
        exit()
    
    # Convert points to Zernike coefficients
    recon.update_slopes(slopes)
    a_z = recon.slopes_to_zernikes()

    if np.isnan(a_z.sum()):
        print_return_code(4)  # one of the coeffs is nan
        print_coeffs(a_z)
        return
    
    # Print Zernike coefficients
    print_return_code(0)
    print_coeffs(a_z)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FELIX slopes to Zernikes server")
    parser.add_argument("coords", type=float, nargs=8, help="Spot positions: x1, y1, x2, y2, x3, y3, x4, y4")
    args = parser.parse_args()

    if args.coords is None:
        print_return_code(1)  # no input
        exit()

    coords = np.array(args.coords)
    if len(coords) != 8:
        print_return_code(2)  # input does not contain 8 elements
        exit()

    main(coords)