import argparse
import numpy as np
from reconstruction import ZernikeReconstructor
from config import *

import matplotlib.pyplot as plt

# x1 x2 ... y1 y2 ...
cal_x = np.array([130.73, 138.72, 126.03, 132.68])
cal_y = np.array([135.50, 129.99, 127.62, 121.91])
cal_x -= cal_x.mean()
cal_y -= cal_y.mean()

CAL_SLOPES = np.array( cal_x.tolist() + cal_y.tolist() )


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
    print(f"RC {n}")
    messages = {
        0: "MSG success",
        1: "MSG no input provided",
        2: "MSG input does not contain 8 elements",
        3: "MSG input points do not match N_SPOTS",
        4: "MSG computed zernikes are NaN",
    }
    if n in messages:
        print(messages[n])
    else:
        print("MSG unknown error")

def main(coords):

    recon = ZernikeReconstructor()
    a_z = np.zeros(N_MODES)

    # Subtract off the mean
    xmean = np.mean(coords[::2])
    ymean = np.mean(coords[1::2])
    pointsx = np.array(coords[::2]) - xmean
    pointsy = np.array(coords[1::2]) - ymean

    # Reformat from [x1, y1, ... xn, yn] to [x1, ..., xn, y1, ..., yn]
    slopes = np.array( pointsx.tolist() + pointsy.tolist() ) - CAL_SLOPES
    
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
        exit()
    
    # Print Zernike coefficients
    print_return_code(0)
    print_coeffs(a_z)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FELIX slopes to Zernikes server")
    parser.add_argument("coords", type=float, nargs=8, help="Spot positions: x1, y1, x2, y2, x3, y3, x4, y4")
    args = parser.parse_args()

    if args.coords is None:
        print_return_code(1)  # no input
        print_coeffs(np.zeros(N_MODES))
        exit()

    if len(args.coords) != 8:
        print_return_code(2)  # input does not contain 8 elements
        print_coeffs(np.zeros(N_MODES))
        exit()

    main(args.coords)