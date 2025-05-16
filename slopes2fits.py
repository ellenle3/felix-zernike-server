import numpy as np
import argparse
from astropy.io import fits
from datetime import datetime, timezone


def main(fn_in, fn_out):
    
    data = np.genfromtxt(fn_in).T
    timestamps = data[1]
    slopes = data[2:].T

    timestamps = timestamps.astype(np.float64)
    slopes = slopes.astype(np.float64)

    # Create UTC timestamps of starting and ending times YYYYMMDDTHH:MM:SS+00:00
    t_start = timestamps[0]
    t_end = timestamps[-1]

    utc_time = datetime.now(timezone.utc)
    stamp_start = utc_time.fromtimestamp(t_start).strftime("%Y%m%dT%H:%M:%S+00:00")
    stamp_end = utc_time.fromtimestamp(t_end).strftime("%Y%m%dT%H:%M:%S+00:00")

    # Create a new FITS file
    hdu1 = fits.PrimaryHDU(slopes)
    hdu2 = fits.ImageHDU(timestamps)
    hdu_list = fits.HDUList([hdu1, hdu2])

    # Set the header information
    hdu1.header['TSTART'] = (stamp_start, 'Start time of the data')
    hdu1.header['TSTOP'] = (stamp_end, 'End time of the data')

    hdu_list.writeto(fn_out, overwrite=True)
    print(f"Created FITS file {fn_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert slopes to FITS file.")
    parser.add_argument("fn_in", type=str, help="Input file name")
    parser.add_argument("fn_out", type=str, help="Output file name")
    args = parser.parse_args()

    main(args.fn_in, args.fn_out)