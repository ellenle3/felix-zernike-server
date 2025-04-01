"""Saves theoretical imat and cmat for FELIX as FITS files. Spot locations and
number of modes are defined in config.py.
"""
from astropy.io import fits
from reconstruction import ZernikeReconstructor

def main():
    recon = ZernikeReconstructor()

    hdu = fits.PrimaryHDU(recon.A)
    hdu.writeto("data/FELIXimattheor.fits", overwrite=True)

    hdu = fits.PrimaryHDU(recon.s2z)
    hdu.writeto("data/FELIXcmattheor.fits", overwrite=True)


if __name__=='__main__':
    main()