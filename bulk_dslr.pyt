#author: Dio Dinta Dafrista (WFP Indonesia)

import time
import arcpy
import os
import datetime
from arcpy.sa import *
from datetime import date
from arcpy import env
from arcpy.sa import *


def createRaster(folder, netcdffile, tiffolder):
	arcpy.env.workspace = tiffolder
	filename = os.path.join(folder, netcdffile)
	newfilename = netcdffile+".tif"
	tiffile = os.path.join(tiffolder, newfilename)
	if not os.path.exists(os.path.join(tiffolder, newfilename)):
		arcpy.MakeNetCDFRasterLayer_md(in_netCDF_file=filename,variable="precipitationCal",x_dimension="lon",y_dimension="lat",out_raster_layer=newfilename,band_dimension="",dimension_values="",value_selection_method="BY_VALUE")
		arcpy.CopyRaster_management(newfilename, tiffile, "", "", "", "NONE", "NONE", "")
		if not os.path.exists(tiffile):
			print("Failed to create " + newfilename)
		if os.path.exists(tiffile):
			print(newfilename + " is successfully created")
		arcpy.Delete_management(newfilename)
	else:
		print(newfilename + " already exists")

def rainydays(tiffolder, threshold, rainydayFolder):
	print("start processing rainy data........ ")
	sr = arcpy.SpatialReference(4326)
	tifdata = []
	rainydata = []
	for tdata in os.listdir(tiffolder):
		if tdata.endswith(".tif") or tdata.endswith(".tiff"):
			parseString = tdata.split('.')
			parse = parseString[4]
			tifdate = parse[0:8]
			tifdata.append(tifdate)
	for rdata in os.listdir(rainydayFolder):
		if rdata.endswith(".tif") or rdata.endswith(".tiff"):
			parseStringtdata = rdata.split('.')
			rainydate = parseStringtdata[1]
			rainydata.append(rainydate)
	for i in tifdata:
		print("checking rainday data for date " +i)
		if i not in rainydata:
			print("rainday data for date " +i+ " has not been calculated")
			print("calculating rainday for date " +i)
			tifname = 'masked_day-L.MS.MRG.3IMERG.{0}-S000000-E235959.tif'.format(i)
			rainyfilename = 'raindays.{0}.threshold_{1}mm.tif'.format(i,threshold)
			tiffile = os.path.join(tiffolder, tifname)
			arcpy.CheckOutExtension("spatial")
			outCon = Con(Raster(tiffile) > int(threshold),1,0)
			outCon.save(os.path.join(rainydayFolder, rainyfilename))
			arcpy.DefineProjection_management(os.path.join(rainydayFolder, rainyfilename),sr)
			print("file "+rainyfilename+" is created")
			arcpy.CheckInExtension("spatial")
	print("processing rainy days for threshold "+str(threshold)+" is  completed--------")

def calculatedslr(dslrdate, threshold, num_of_days, raindayfolder, dslrfolder):
	dslrfilename = 'dslr_{0}mm_threshold_{1}.tif'.format(threshold.zfill(2), dslrdate)
	#print("start processing DSLR--------------- ")
	if not os.path.exists(os.path.join(dslrfolder,dslrfilename)):
		arcpy.CheckOutExtension("spatial")
		#messages.addmessage("DSLR file for date " +dslrdate+ " has not been calculated")
		#messages.addmessage("calculating DSLR file for date "+dslrdate)
		dslrdateformatted = date(int(dslrdate[0:4]), int(dslrdate[4:6]), int(dslrdate[6:8]))
		NumDaysRain = int(num_of_days)+1
		index = []
		for rainyfilename in os.listdir(raindayfolder):
			if rainyfilename.endswith(".tif") or rainyfilename.endswith(".tiff"):
				arcpy.CalculateStatistics_management(os.path.join(raindayfolder,rainyfilename))
				get_min_value = arcpy.GetRasterProperties_management(os.path.join(raindayfolder,rainyfilename), "MINIMUM")
				get_max_value = arcpy.GetRasterProperties_management(os.path.join(raindayfolder,rainyfilename), "MAXIMUM")
				max_value = int(get_max_value.getOutput(0))
				min_value = int(get_min_value.getOutput(0))
				if min_value == 0 and max_value == 1:
					parseStringRain = rainyfilename.split('.')
					parseRain = parseStringRain[1]
					yearRain = int(parseRain[0:4])
					monthRain = int(parseRain[4:6])
					dayRain = int(parseRain[6:8])
					filedateRain = date(yearRain, monthRain, dayRain)
					if filedateRain < dslrdateformatted:
						if filedateRain > dslrdateformatted - datetime.timedelta(days=int(num_of_days)+1): 
							index.append(os.path.join(raindayfolder, rainyfilename))
				else:
					print(rainyfilename + " is not a proper rainyday data. max value must be 1 and min value must be 0.")

		if len(index)>=num_of_days:
			#messages.addmessage("rainday data "+str(len(index))+" before DSLR date are complete. calculating DSLR....")
			indexReverse = sorted(index, reverse=True)
			#print(indexReverse)
			outHighestPosition = HighestPosition(indexReverse)
			#outHighestPosition.save(os.path.join(dslrfolder, 'temp.tif'))
			minusOne = outHighestPosition - 1
			minusOne.save(os.path.join(dslrfolder, dslrfilename))
			print("file "+dslrfilename+" is created. Process completed")
		else:
			print("the sum of the data " +str(len(index))+ " is less than the num of days = "+str(num_of_days))
		arcpy.CheckInExtension("spatial")
	else:
		print("DSLR file for date " +dslrdate+ " exists")


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Calculate days since last rain"
        self.alias = "Calculate days since last rain based on daily rainfall data"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "DSLR Tool 0.1 - WFP Indonesia"
        self.description = "Calculate days since last rain based on daily rainfall data"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(displayName="Input Folder",name="in_folder",datatype="DEFolder",parameterType="Required",direction="Input")
        param4 = arcpy.Parameter(displayName="Boundary",name="boundary",datatype="DEFeatureClass",parameterType="Required",direction="Input")
        param1 = arcpy.Parameter(displayName="Threshold",name="Threshold",datatype="Field",parameterType="Required",direction="Input")
        param1.value = 1
        param5 = arcpy.Parameter(displayName="Number of Days",name="number_of_days",datatype="Field",parameterType="Required",direction="Input")
        param5.value = 90
        param2 = arcpy.Parameter(displayName="Output Folder",name="out_features",datatype="DEFolder",parameterType="Required",direction="Output")
        #param3 = arcpy.Parameter(displayName="Date",name="Date",datatype="GPDate",parameterType="Required",direction="Input")
        params = [param0, param1, param5, param4, param2]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        nc4_folder = parameters[0].valueAsText
        threshold = parameters[1].valueAsText
        messages.addmessage("threshold is " +threshold)
        result_folder = parameters[4].valueAsText
        subset_file = parameters[3].valueAsText
        num_of_days = parameters[2].valueAsText
        messages.addmessage("We are counting for " +num_of_days+ " days")
        IndexData = []
        IndexDate = []
        for nc4_file in os.listdir(nc4_folder):
            if nc4_file.endswith(".nc4"):
                parseStringRain = nc4_file.split('.')
                parseRain = parseStringRain[4]
                yearRain = int(parseRain[0:4])
                monthRain = int(parseRain[4:6])
                dayRain = int(parseRain[6:8])
                filedateRain = date(yearRain, monthRain, dayRain)
                IndexDate.append(filedateRain)
                IndexData.append(nc4_file)
        indexDateSorted = sorted(IndexDate, reverse=True)
        indexDataSorted = sorted(IndexData, reverse=True)
        data_numdays = indexDateSorted[0] - indexDateSorted[len(indexDateSorted)-1]
        date_numdays = len(indexDateSorted)
        if data_numdays.days+1 == date_numdays and date_numdays > 90:
            messages.addmessage("data is in order from " +str(indexDateSorted[0])+ " to "+ str(indexDateSorted[len(indexDateSorted)-1]))
            messages.addmessage("start processing...........................")
            messages.addmessage("creating folder to store raster precipitation data...")
            if not os.path.exists(result_folder):
                os.mkdir(result_folder)
            tiffolder = result_folder+ "\\imerg_precipitation"
            if not os.path.exists(tiffolder):
                os.mkdir(tiffolder)
            for i in indexDataSorted:
                createRaster(nc4_folder, i, tiffolder)
            messages.addmessage("creating raster precipitation data are done")
            print("creating folder to store indonesia precipitation data...")
            idn_precipitation = result_folder + "\\masked_precipitation"
            if not os.path.exists(idn_precipitation):
                os.mkdir(idn_precipitation)
            messages.addmessage("start processing the subset data")
            for tif_file in os.listdir(tiffolder):
                if tif_file.endswith(".tif"):
                    dateparse = tif_file.split('.')
                    datefile = dateparse[4]
                    new_name = 'masked_day-L.MS.MRG.3IMERG.{0}.tif'.format(datefile)
                    arcpy.CheckOutExtension("spatial")
                    if not os.path.exists(os.path.join(idn_precipitation, new_name)):
                        extractbymask = ExtractByMask(os.path.join(tiffolder, tif_file), subset_file)
                        extractbymask.save(os.path.join(idn_precipitation, new_name))
                        #messages.addmessage(new_name+ " is successfully created")
                    else:
                        messages.addmessage(new_name + " exists")
            idn_rainyday = result_folder + "\\masked_rainyday"
            if not os.path.exists(idn_rainyday):
                os.mkdir(idn_rainyday)
            rainydays(idn_precipitation, threshold, idn_rainyday)
            messages.addmessage("----------start calculating DSLR from rainy data----------------")
            start_checking_array = sorted(indexDateSorted, reverse=True)
            start_checking = start_checking_array[int(num_of_days)]
            date_end = start_checking_array[-1]
            idn_dslr = result_folder + "\\masked_dslr"
            if not os.path.exists(idn_dslr):
                os.mkdir(idn_dslr)
            dslrfilename = 'dslr_{0}mm_threshold_{1}.tif'.format(threshold.zfill(2), start_checking.strftime('%Y%m%d'))
            messages.addmessage("start processing DSLR--------------- ")
            if not os.path.exists(os.path.join(idn_dslr, dslrfilename)):
                messages.addmessage("processing " + str(start_checking))
                dslrdate = start_checking.strftime('%Y%m%d')
                if not os.path.exists(os.path.join(idn_dslr,dslrfilename)):
                    arcpy.CheckOutExtension("spatial")
                    messages.addmessage("DSLR file for date " +dslrdate+ " has not been calculated")
                    messages.addmessage("calculating DSLR file for date "+dslrdate)
                    dslrdateformatted = date(int(dslrdate[0:4]), int(dslrdate[4:6]), int(dslrdate[6:8]))
                    NumDaysRain = int(num_of_days)+1
                    index = []
                    for rainyfilename in os.listdir(idn_rainyday):
                        if rainyfilename.endswith(".tif") or rainyfilename.endswith(".tiff"):
                            arcpy.CalculateStatistics_management(os.path.join(idn_rainyday,rainyfilename))
                            get_min_value = arcpy.GetRasterProperties_management(os.path.join(idn_rainyday,rainyfilename), "MINIMUM")
                            get_max_value = arcpy.GetRasterProperties_management(os.path.join(idn_rainyday,rainyfilename), "MAXIMUM")
                            max_value = int(get_max_value.getOutput(0))
                            min_value = int(get_min_value.getOutput(0))
                            if min_value == 0 and max_value == 1:
                                parseStringRain = rainyfilename.split('.')
                                parseRain = parseStringRain[1]
                                yearRain = int(parseRain[0:4])
                                monthRain = int(parseRain[4:6])
                                dayRain = int(parseRain[6:8])
                                filedateRain = date(yearRain, monthRain, dayRain)
                                if filedateRain < dslrdateformatted:
                                    if filedateRain > dslrdateformatted - datetime.timedelta(days=int(num_of_days)+1):
                                        index.append(os.path.join(idn_rainyday, rainyfilename))
                            else:
                                messages.addmessage(rainyfilename + " is not a proper rainyday data. max value must be 1 and min value must be 0.")

                    if len(index)>=num_of_days:
                        messages.addmessage("rainday data "+str(len(index))+" before DSLR date are complete. calculating DSLR....")
                        indexReverse = sorted(index, reverse=True)
                        outHighestPosition = HighestPosition(indexReverse)
                        minusOne = outHighestPosition - 1
                        minusOne.save(os.path.join(idn_dslr, dslrfilename))
                        messages.addmessage("file "+dslrfilename+" is created. Process completed")
                    else:
                        messages.addmessage("the sum of the data " +str(len(index))+ " is less than the num of days = "+str(num_of_days))
                    arcpy.CheckInExtension("spatial")
                else:
                    messages.addmessage("DSLR file for date " +dslrdate+ " exists")
            else:
                messages.addmessage(str(start_checking) + " is available")
            start_checking = start_checking + datetime.timedelta(days=1)
            while date_end >= start_checking:
                messages.addmessage("processing " + str(start_checking))
                date_before_dslr = start_checking - datetime.timedelta(days=1)
                dslrdate_beforedslr = date_before_dslr.strftime('%Y%m%d')
                idn_data = 'idn_day-L.MS.MRG.3IMERG.{0}-S000000-E235959.tif'.format(dslrdate_beforedslr)
                dslr_prev_day = 'dslr_01mm_threshold_20170503'.format(dslrdate_beforedslr)
                raster_idn_data = Raster(os.path.join(idn_precipitation, idn_data))
                raster_dslr_prev_day = Raster(os.path.join(idn_dslr, dslr_prev_day))
                new_dslr = Con( raster_idn_data < 1 , raster_dslr_prev_day + 1, raster_dslr_prev_day)
                new_dslr.save(os.path.join(idn_dslr, dslrfilename))
                start_checking = start_checking + datetime.timedelta(days=1)
            arcpy.CheckOutExtension("spatial")
        return
