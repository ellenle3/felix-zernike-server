# IRTF-ZernikeServer

Client will send two sets of five points, as:

    x1,y1,x2,y2,...,x5,y5,...,x10,y10

    x1,y1 is the centerpoint of the calibration data, x2,y2 - x5,y5 are the points for the calibration data.
    x5,y5 is the centerpoint of the calibration data, x6,y6 - x10,y10 are the points for the input data.



There are two "start_server_*" commands, one for TCP one for UDP.

On linux you can send tcp sample data via:

    echo "points [2024-01-01 12:34:56] [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,17.0,18.0,19.0,20.0]" | nc localhost 8000

On linux you can send udp sample data via:

    echo "points [2024-01-01 12:34:56] [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,17.0,18.0,19.0,20.0]" | nc -u localhost 8000


# FELIX spot positions to Zernikes

Setup:

    ssh -R 10488:localhost:10488 felix@felix-spare

Run the script:

    python felix_zernikes.py

You can configure the number of Zernike modes and slope sampling points in config.py.
Slopes are measured with respect to calibration spots.

FELIX data server and client written by Charles Lockhart. Conversion of FELIX spot
positions to Zernike coefficients written by Ellen Lee.