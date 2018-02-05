import arcpy
import os
import gzip
from arcpy.sa import *


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Bulk Standard Precipitation Index"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(displayName="Input Folder",name="in_folder",datatype="DEFolder",parameterType="Required",direction="Input")
        param1 = arcpy.Parameter(displayName="Output Folder",name="out_features",datatype="DEFolder",parameterType="Required",direction="Output")
        param2 = arcpy.Parameter(displayName="Subset Shapefile",name="boundary",datatype="DEFeatureClass",parameterType="Required",direction="Input")
        param3 = arcpy.Parameter(displayName="Long Term Average Calculated",name="LTSYear",datatype="Field",parameterType="Required",direction="Input")
        param3.value = 2015
        params = [param0, param1, param2, param3]
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
        """The source code of the tool."""
        lst_year = parameters[3].valueAsText
        messages.addmessage("Long term average is calculated until " +lst_year)
        data_folder = parameters[0].valueAsText
        output_folder = parameters[1].valueAsText
        shapefile = parameters[2].valueAsText
        messages.addmessage("data folder is in " +data_folder)
        messages.addmessage("checking input data...")
        messages.addmessage("checking data naming format...")
        data_array_lst = []
        data_array = []
        month_year_lst = []
        month_year = []
        month_list = ['01','02','03','04', '05', '06', '07', '08', '09', '10', '11', '12']
        for filename in os.listdir(data_folder):
            if filename.endswith(".gz"):
                data_array.append(filename)
                parseString = filename.split('.')
                filename_my = parseString[2]+parseString[3]
                month_year.append(filename_my)
                messages.addmessage(int(parseString[2]), int(lst_year))
                if int(parseString[2]) <= int(lst_year):
                    month_year_lst.append(filename_my)
                    data_array_lst.append(filename)
        num_of_years_lst = (int(lst_year)-1980)*12
        messages.addmessage("data needed to calculate long term average until "+lst_year+" is "+str(num_of_years_lst))
        messages.addmessage("data available is "+str(len(data_array_lst)))
        if num_of_years_lst == len(data_array_lst):
            messages.addmessage("data for calculating long term average is complete......")
            messages.addmessage("Creating output folder......")
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            tif_folder = output_folder+ "\\tif_data"
            if not os.path.exists(tif_folder):
                messages.addmessage("Creating output folder for tif data......")
                os.mkdir(tif_folder)

            #============================== extracting gzip data ================================#

            messages.addmessage("Extracting gzip data into tif........")
            for file_monthly in data_array_lst:
                local_f = os.path.join(data_folder, os.path.basename(file_monthly))
                tifdata = os.path.join(tif_folder, os.path.basename(file_monthly))
                with gzip.open(local_f, 'rb') as _in_file:
                    s = _in_file.read()
                    _path_to_store = os.path.splitext(tifdata)[0] #f[:-3]
                    print(_path_to_store)
                    if not os.path.isfile(_path_to_store) or overwrite:
                        with open(_path_to_store, 'wb') as _out_file:
                            _out_file.write(s)

            #======================= mask into shapefile ==============================#

            messages.addmessage("Start masking global data........")
            masking_folder = output_folder+ "\\mask_folder"
            arcpy.CheckOutExtension("spatial")
            if not os.path.exists(masking_folder):
                messages.addmessage("Creating output folder for masking data......")
                os.mkdir(masking_folder)
            for file_global in os.listdir(tif_folder):
                masking_filename = 'mask_{0}'.format(file_global)
                if file_global.endswith(".tif"):
                    extractbymask = ExtractByMask(os.path.join(tif_folder, file_global) , shapefile)
                    extractbymask.save(os.path.join(masking_folder, masking_filename))



            # =========================Create LTA file=================================#
            messages.addmessage("Start calculating long term average........")
            dictionary = {}
            for i in month_list:
                content = []
                for file_monthly in os.listdir(tif_folder):
                    #messages.addmessage("Data: "+file_monthly)
                    if file_monthly.endswith(".tif"):
                        parseString1 = file_monthly.split('.')
                        Dmonth = parseString1[3]
                        #messages.addmessage("check file with "+Dmonth)
                        #messages.addmessage("check "+i)
                        if Dmonth == i and int(parseString1[2]) <= int(lst_year):
                            #messages.addmessage("check"+Dmonth+" and"+i)
                            content.append(os.path.join(tif_folder, file_monthly))
                dictionary[i] = content
            #messages.addmessage(dictionary)

            lta_folder = output_folder+ "\\lta_data"
            if not os.path.exists(lta_folder):
                os.mkdir(lta_folder)
            for k in month_list:
                index = k
                listoffile = dictionary[index]
                ext = ".tif"
                years_num = int(lst_year)-1980
                newfilename_monthly_std = 'chirps-v2.0.1981-{0}.{1}.monthly.{2}yrs.std{3}'.format(lst_year, k, years_num, ext)
                newfilename_monthly_avg = 'chirps-v2.0.1981-{0}.{1}.monthly.{2}yrs.avg{3}'.format(lst_year, k, years_num, ext)
                messages.addmessage("creating " +newfilename_monthly_avg + " and "+newfilename_monthly_std)
                if arcpy.Exists(os.path.join(lta_folder, newfilename_monthly_avg)):
                    messages.addmessage(newfilename_monthly_avg + " exists")
                else:

                    outCellStatistics_avg = CellStatistics(listoffile, "MEAN", "DATA")
                    outCellStatistics_avg.save(os.path.join(lta_folder, newfilename_monthly_avg))
                    messages.addmessage("file " + newfilename_monthly_avg + " is created")

                if arcpy.Exists(os.path.join(lta_folder, newfilename_monthly_std)):
                    print(newfilename_monthly_std + " exists")
                else:

                    outCellStatistics_avg = CellStatistics(listoffile, "STD", "DATA")
                    outCellStatistics_avg.save(os.path.join(lta_folder, newfilename_monthly_std))
                    messages.addmessage("file " + newfilename_monthly_std + " is created")


            messages.addmessage("Finish Creating Long Term Average Data........")
            messages.addmessage("Start Calculating Standard Precipitation Index........")
            messages.addmessage("Creating folder to save Standard Precipitation Index data........")
            spi_folder = output_folder+ "\\spi_data"
            if not os.path.exists(spi_folder):
                os.mkdir(spi_folder)

            #----------------------Calculating Rainfall Anomaly-----------------------#

            for each_mask_file in os.listdir(masking_folder):
                if each_mask_file.endswith(".tif"):
                    parse_string_mask = each_mask_file.split('.')
                    month_mask = parse_string_mask[3]
                    year_mask = parse_string_mask[2]
                    for each_lta_file in os.listdir(lta_folder):
                        if each_lta_file.endswith(".tif"):
                            parse_string_lta = each_lta_file.split('.')
                            if parse_string_lta[3] == month_mask and parse_string_lta[6] == 'avg':
                                avg_lta_used = os.path.join(lta_folder, each_lta_file)
                            if parse_string_lta[3] == month_mask and parse_string_lta[6] == 'std':
                                std_lta_used = os.path.join(lta_folder, each_lta_file)
                    ext = ".tif"
                    spi_filename = 'mask_cli_chirps-v2.0.{0}.{1}.spi{2}'.format(year_mask, month_mask, ext)

                    if arcpy.Exists(os.path.join(spi_folder, spi_filename)):
                        messages.addmessage("file " + spi_folder + " is already exist")
                    else:
                        SPIRaster = (Raster(os.path.join(masking_folder, each_mask_file)) - Raster(avg_lta_used)) / Raster(std_lta_used)
                        SPIRaster.save(os.path.join(spi_folder, spi_filename))
                        messages.addmessage("file " + spi_filename + " is created")
            arcpy.CheckInExtension("spatial")

        else:
            messages.addmessage("data for calculating long term average is not complete. Please check your data")
        return
