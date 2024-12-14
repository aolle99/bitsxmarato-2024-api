from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt

import pykrige.kriging_tools as kt
from pykrige.uk import UniversalKriging
from sklearn.neighbors import BallTree

from ftplib import FTP
import os


def get_no2(dia, mes, hora, center_coordinate_lat, center_coordinate_lon):
    host = 'es-ftp.bsc.es'
    port = 8021
    usr = 'AQS_database'
    pwd = 'yFXh+Rx3lggTsmNJ'

    ftp = FTP()
    ftp.connect(host, port)
    ftp.login(usr, pwd)

    ftp.cwd('DADES_CALIOPE_buenos/NO2')

    filename = f"sconcno2_2023{mes}{dia}00.nc"
    with open(filename, 'wb') as fp:
        ftp.retrbinary(f"RETR {filename}", fp.write)

    fp.close()

    nc_file = Dataset(filename, 'r')

    # Access a specific variable, e.g., 'sconcno2'
    data = nc_file.variables['sconcno2'][:]  # Replace 'sconcno2' with your desired variable

    dict_keys = ['time', 'lat', 'lon', 'x', 'y', 'lev', 'sconcno2', 'Lambert_conformal']
    time = nc_file.variables['time'][:]
    lat = nc_file.variables['lat'][:]
    lon = nc_file.variables['lon'][:]
    sconcno2 = nc_file.variables['sconcno2'][:]
    lev = nc_file.variables['lev'][:]

    nc_file.close()
    os.remove(filename)

    lat_coords = [np.deg2rad(x) for xs in lat for x in xs]
    lon_coords = [np.deg2rad(x) for xs in lon for x in xs]
    coordinates = [[lat_coords[i], lon_coords[i]] for i in range(len(lat_coords))]
    bt = BallTree(coordinates, leaf_size=2, metric="haversine")
    # primer mirem si esta dins la matriu sino no seguim

    if (center_coordinate_lat < lat[0, 0] or center_coordinate_lat > lat[-1, -1] or center_coordinate_lon < lon[
        0, 0] or center_coordinate_lon > lon[-1, -1]):
        print("The center coordinate is not within the matrix")
        exit()

    # Find closest point to center
    _, idx = bt.query([[np.deg2rad(center_coordinate_lat), np.deg2rad(center_coordinate_lon)]], k=1)
    idx = idx[0][0]

    # Compute row and col indexes of matrix
    row_index = idx // len(lat[0])
    col_index = idx % len(lat[0])

    # (298, 278)
    num_points = 6
    newlat = np.zeros((num_points, num_points))
    newlon = np.zeros((num_points, num_points))
    no2_values = np.zeros((num_points, num_points))

    if (row_index < 3 or row_index > lat.shape[0] - 3 or col_index < 3 or col_index > lon.shape[1] - 3):
        print("The center coordinate is too close to the edge of the matrix")
        exit()

    lat_start = row_index - 3
    lon_start = col_index - 3

    print(lat[lat_start, lon_start])
    print(lon[lat_start, lon_start])

    x = 0
    for i in range(lat_start, lat_start + num_points):
        y = 0
        for j in range(lon_start, lon_start + num_points):
            newlat[x, y] = lat[i, j]
            newlon[x, y] = lon[i, j]
            no2_values[x, y] = sconcno2[hora, 0, i, j]
            y += 1
        x += 1

    # Parameters
    size = 256

    def assign_values_to_map(size, num_points, values):

        # Initialize the map with zeros
        map_array = np.zeros((size, size))

        # Calculate equally spaced coordinates
        coords = np.linspace(0, size - 1, int(num_points)).astype(int)

        # Assign values from the 14x14 matrix to the corresponding points in the map
        for i, x in enumerate(coords):
            for j, y in enumerate(coords):
                map_array[x, y] = values[i, j]

        return map_array

    starting_map = assign_values_to_map(size, num_points, no2_values)

    # Visualize the matrix
    # plt.figure(figsize=(8, 6))
    # plt.imshow(starting_map, cmap='viridis', interpolation='nearest')
    # plt.colorbar(label='Values')  # Add a colorbar
    # plt.title("Matrix Visualization")
    # plt.xlabel("X-axis")
    # plt.ylabel("Y-axis")
    # plt.show()

    flat_no2 = [x for xs in no2_values for x in xs]
    coords = np.linspace(0, size - 1, int(num_points)).astype(int)

    x_coords = []
    y_coords = []
    for x in coords:
        for y in coords:
            x_coords.append(x)
            y_coords.append(y)

    # cax = plt.scatter(x_coords, y_coords, c=flat_no2)
    # cbar = plt.colorbar(cax, fraction=0.03)
    # plt.title('Measured Porosity')
    # plt.show()

    UK = UniversalKriging(
        x_coords,
        y_coords,
        flat_no2,
        variogram_model='gaussian',
        verbose=True,
        enable_plotting=False,
        nlags=len(flat_no2),
    )

    gridx = np.arange(0, size, 1, dtype='float64')
    gridy = np.arange(0, size, 1, dtype='float64')
    zstar, ss = UK.execute("grid", gridx, gridy)

    # cax = plt.imshow(zstar, extent=(0, size-1, 0, size-1), origin='lower')
    # cbar=plt.colorbar(cax)
    # plt.title('Porosity estimate')
    # plt.show()

    x_coords = np.linspace(newlat[0, 0], newlat[-1, -1], size)
    y_coords = np.linspace(newlon[0, 0], newlon[-1, -1], size)

    llista = []

    for i, x in enumerate(x_coords):
        for j, y in enumerate(y_coords):
            llista.append([x, y, zstar[i, j] * 100])

    return llista