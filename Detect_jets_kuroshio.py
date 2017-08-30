import numpy as np
from matplotlib import pyplot as plt
from netCDF4 import Dataset
import Wavelet_Jet_Detection

#=========================#
# WAVELET PARAMETERS
#=========================#
N_DECOMP_LEVELS = 4
confidence_param = 0.9

#============================#
#Set the gradient threshold
grad_thres = 0.0025
#============================#

#Start year and end year 
START_YEAR = 2010
END_YEAR   = 2011


#==================================================#
#Input and output paths of the files
base_sla_path = '/home/cchlod/AVISO/AVISO_Gridded_2/'
base_output_path = base_sla_path

adt_file_stem = 'adt_Kuroshio_'
output_file_stem = 'jet_detection_Kuroshio_'
#==================================================#


#==========================#
#Here we instantiate the
#wavelet jet detection class
#==========================#
wavelet_jet_detector = Wavelet_Jet_Detection.Jet_Detector(N_DECOMP_LEVELS,confidence_param,wavelet_basis='haar',
                       grad_thresh=grad_thres)



#some counters
time_counter = 0
start_lon = 0

for i_year in range(START_YEAR,END_YEAR):
    print 'writting file to: ', base_output_path+output_file_stem + str(i_year)+'.nc'
    dataset_out        = Dataset(base_output_path+output_file_stem + str(i_year)+'.nc',
                                'w',clobber=True, format='NETCDF4')
                                
                                
    dataset_out.createDimension('time', None)
    var_time = dataset_out.createVariable('time', 'f8', ['time'])

    #Load input data
    dataset_adt = Dataset(base_sla_path+adt_file_stem + str(i_year) + '.nc','r')
    adt         = dataset_adt.variables['adt'][:,:,:]
    time        = dataset_adt.variables['time'][:]
    lat_adt     = dataset_adt.variables['latitude'][:]
    lon_adt     = dataset_adt.variables['longitude'][:]
    
    
    nT    = time.size   
    n_lon = lon_adt.size
    n_lat = lat_adt.size
    jet_histogram = np.zeros([n_lat,n_lon],dtype='u4')
    jet_locations = np.zeros([nT,n_lat,n_lon],dtype='u4')

    #============================#
    #Set up the output file
    #============================#
    dataset_out.createDimension('lat', n_lat)
    dataset_out.createDimension('lon', n_lon)
    var_lat = dataset_out.createVariable('lat', 'f8', ['lat'])
    var_lon = dataset_out.createVariable('lon', 'f8', ['lon'])
    var_time[:] = time

    var_lat[:] = lat_adt
    var_lon[:] = lon_adt
    var_hist      = dataset_out.createVariable('jet_loc_hist', 'f8', ['lat','lon'])
    var_locations = dataset_out.createVariable('jet_locations', 'f8', ['time','lat','lon'])
    #============================#
    
    for iT in range(0,nT):
        print "time step: ", iT, " of ", nT
        for i_lon in range(start_lon,n_lon):
            adt_slice = adt[iT,:,i_lon]
            adt_slice[adt_slice.mask] = np.nan
            lat_slice = lat_adt.copy()
            
            #==================================#
            #Here's where the magic happens
            #For each meridional transect, and at each 
            lon_positions, lat_positions = wavelet_jet_detector.detect_jets(lon_adt[i_lon]*np.ones(n_lat), lat_adt,adt_slice,only_eastward=True)
            
            
            for i_jet in range(0,len(lat_positions)):
                index_y = np.nonzero(lat_adt>=lat_positions[i_jet])[0][0]     
                jet_histogram[index_y,i_lon] = jet_histogram[index_y,i_lon]+1
                jet_locations[iT,index_y,i_lon] = 1
    var_locations[0:nT,:,:] =  jet_locations 
    time_counter = time_counter+nT    
    
        
    dataset_adt.close()
var_hist[:,:] = jet_histogram/float(time_counter)
dataset_out.close()  
    
