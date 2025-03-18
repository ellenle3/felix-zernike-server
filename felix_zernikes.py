import argparse
from reconstruction import ZernikeReconstructor
from server import start_server_tcp, start_server_udp
from config import *

def print_color(s: str, c: str) -> None:
    """Prints a colored string.

    Parameters
    ----------
    s: str
        String to print.
    c: str 
        Color of the string. Options: 'red', 'green', 'yellow', 'blue',
        'magenta', 'cyan', 'black', 'white', 'bold', 'underline'

    Returns
    -------
    None
    """
    color_dict = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'black': '\033[30m',
        'white': '\033[37m',
        'bold':'\033[1m',
        'underline': '\033[4m'
    }
    assert c in color_dict, "The ANSI escape sequence for c must be defined print_color"

    color_code = color_dict[c]
    end_code = '\033[0m'
    print(f'{color_code}' + s + f'{end_code}')

def main(protocol, port):

    zernike_names = ["Tip", "Tilt", "Focus", "Astig1", "Astig2", "Coma1", "Coma2",
                      "Trefoil1", "Trefoil2", "Spherical"]

    # Initalize the wavefront reconstructor
    recon = ZernikeReconstructor()

    while True:

        # Start the server to listen for FELIX data
        if protocol == 'tcp':
            timestamp, X_values, Y_values = start_server_tcp(port)
        elif protocol == 'udp':
            timestamp, X_values, Y_values = start_server_udp(port)
        else:
            raise ValueError(f"Invalid protocol: {protocol}")

        recon.update_slopes(timestamp, X_values, Y_values)
        a_z = recon.slopes_to_zernikes()
        
        print(f"Zernikes at {recon.recent_timestamp}:")
        for i, coeff in enumerate(a_z):
            prefix = f"  J = {i + 2}: "
            if coeff >= 0:
                prefix += ' '
            if i < 10:
                name = f" ({zernike_names[i]})"
            else:
                name = ''
            print_color(prefix + '{:.4f}'.format(coeff) + name, "cyan")
        
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FELIX slopes to Zernikes server")
    parser.add_argument('--protocol', type=str, default='tcp', choices=['tcp', 'udp'], help="Protocol to use (tcp or udp)")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help="Port number to listen on")
    
    args = parser.parse_args()
    main(args.protocol, args.port)