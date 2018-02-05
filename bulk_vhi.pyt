#author: Dio Dinta Dafrista (WFP Indonesia)

import arcpy
import os
import calendar
from arcpy.sa import *

def JulianDate_to_MMDDYYY(y,jd):
    month = 1
    day = 0
    while jd - calendar.monthrange(y,month)[1] > 0 and month <= 12:
        jd = jd - calendar.monthrange(y,month)[1]
        month = month + 1
    return month,jd,y

def mod13a3Process(folder, index, outputFolder, product):
    for filename in os.listdir(folder):
        if filename.endswith(".hdf"):
            print("processing "+filename)
            arcpy.env.workspace = outputFolder
            arcpy.CheckOutExtension("spatial")
            inputRaster = os.path.join(folder,filename)
            outputEVI = '{0}.{1}.tif'.format(filename, product)
            if arcpy.Exists(os.path.join(outputFolder, outputEVI)):
                print(outputEVI + " exists")
            else:
                EVIfile = arcpy.ExtractSubDataset_management(inputRaster,outputEVI,index)
            arcpy.CheckInExtension("spatial")
        else:
            continue

def LSTAverage(day,night,result):
    for filename in os.listdir(day):
        if filename.endswith(".tif") or filename.endswith(".tiff"):
            split = filename.split('.')
            daydate = split[1]
            print(daydate)
            for Nfilename in os.listdir(night):
                if Nfilename.endswith(".tif") or Nfilename.endswith(".tiff"):
                    Nsplit = Nfilename.split('.')
                    year = int(Nsplit[1][1:5])
                    date = int(Nsplit[1][5:8])
                    print(year, day)
                    month, jd, y = JulianDate_to_MMDDYYY(year, date)
                    twodigitmonth = str(month).zfill(2)
                    twodigitday = str(jd).zfill(2)
                    print(twodigitmonth,twodigitday)
                    nightdate = Nsplit[1]
                    if daydate == nightdate:
                        print("day file  "+filename+" match with "+Nfilename)
                        arcpy.CheckOutExtension("spatial")
                        ext = ".tif"
                        newfilename = 'idn_cli_MOD11C3.{0}.{1}.{2}.avg{3}'.format(y, twodigitmonth, twodigitday, ext)
                        print(newfilename)
                        Calculation =  CellStatistics([Raster(os.path.join(day,filename)),Raster(os.path.join(night,Nfilename))], "MEAN", "DATA")
                        Calculation.save(os.path.join(result, newfilename))
                        print("Average file "+newfilename+" created")
                        arcpy.CheckInExtension("spatial")
                    continue
                else:
                    continue
        else:
            continue

def kelvintocelcius(folder, outputfolder):
    for filename in os.listdir(folder):
        if filename.endswith(".tif") or filename.endswith(".tiff"):
            fileKelvin = os.path.join(folder,filename)
            celciusfile = (Raster(fileKelvin)*0.02) - 273.15
            celciusfile.save(os.path.join(outputfolder, filename))

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Bulk VHI Data Processing - WFP Indonesia V1.0"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(displayName="EVI Folder",name="in_folder",datatype="DEFolder",parameterType="Required",direction="Input")
        param1 = arcpy.Parameter(displayName="LTS Folder",name="LTS_Folder",datatype="DEFolder",parameterType="Required",direction="Input")
        param2 = arcpy.Parameter(displayName="Output Folder",name="out_features",datatype="DEFolder",parameterType="Required",direction="Output")
        param3 = arcpy.Parameter(displayName="Subset Shapefile",name="boundary",datatype="DEFeatureClass",parameterType="Required",direction="Input")
        param4 = arcpy.Parameter(displayName="Long Term Average Calculated",name="LTSYear",datatype="Field",parameterType="Required",direction="Input")
        param4.value = 2015
        params = [param0, param1, param2, param3, param4]
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
        #============ defining parameter ================#
        lst_year = parameters[4].valueAsText
        messages.addmessage("Long term average is calculated until " +lst_year)
        mod13a3_folder = parameters[0].valueAsText
        mod11c3_folder = parameters[1].valueAsText
        messages.addmessage("data MOD13A3 folder is in " +mod13a3_folder)
        messages.addmessage("data MOD11C3 folder is in " +mod11c3_folder)
        messages.addmessage("checking input data...")
        messages.addmessage("checking data naming format...")
        messages.addmessage("counting data for long term average...")
        output_folder = parameters[2].valueAsText
        messages.addmessage("output folder is in " +output_folder)
        subset_file = parameters[3].valueAsText
        messages.addmessage("subset file is in " +subset_file)

        #============== Start Calculating Long term EVI =================#

        messages.addmessage("Calculating data for Long term EVI....")
        month_list = ['01','02','03','04', '05', '06', '07', '08', '09', '10', '11', '12']
        data_array = []
        month_year_lta_mod13a3 = []
        for filename in os.listdir(mod13a3_folder):
            if filename.endswith(".tif"):
                data_array.append(filename)
                parseString = filename.split('_')
                filename_my = parseString[6]
                yearString = filename_my[3:7]
                if int(yearString) <= int(lst_year):
                    month_year_lta_mod13a3.append(filename)
        num_of_years_lst = ((int(lst_year)-2000)*12)+11
        messages.addmessage("data needed to calculate long term average until "+lst_year+" is "+str(num_of_years_lst))
        messages.addmessage("data available is "+str(len(month_year_lta_mod13a3)))
        if num_of_years_lst == len(month_year_lta_mod13a3):
            messages.addmessage("data for calculating long term average is complete......")
            messages.addmessage("Creating output folder......")
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            messages.addmessage("Starts Creating Long Term Average for EVI Data......")
            dictionary = {}
            for i in month_list:
                content = []
                for file_monthly in os.listdir(mod13a3_folder):
                    if file_monthly.endswith(".tif"):
                        parseString1 = file_monthly.split('_')
                        DYear = parseString1[6][3:7]
                        J_date = parseString1[6][7:10]
                        #messages.addmessage(DYear +J_date)
                        Dmonth,jd,y = JulianDate_to_MMDDYYY(int(DYear), int(J_date))
                        if str(Dmonth).zfill(2) == i and int(DYear) <= int(lst_year):
                            content.append(os.path.join(mod13a3_folder, file_monthly))
                dictionary[i] = content
            #messages.addmessage(dictionary)
            messages.addmessage("Creating Folder to store LTMin and LTMax for EVI Data......")
            LT_EVI_folder = output_folder+ "\\LTA_EVI_folder"
            if not os.path.exists(LT_EVI_folder):
                os.mkdir(LT_EVI_folder)
                messages.addmessage("Long Term EVI Data Folder Created......")
            for k in month_list:
                index = k
                listoffile = dictionary[index]
                ext = ".tif"
                years_num = int(lst_year)-1999
                newfilename_min = 'MOD13A3.006__1_km_monthly_EVI_2000-{0}.{1}.monthly.{2}yrs.min{3}'.format(lst_year, k, years_num, ext)
                newfilename_max = 'MOD13A3.006__1_km_monthly_EVI_2000-{0}.{1}.monthly.{2}yrs.max{3}'.format(lst_year, k, years_num, ext)

                if arcpy.Exists(os.path.join(LT_EVI_folder, newfilename_min)):
                    print(newfilename_min + " exists")
                else:
                    outCellStatistics_min = CellStatistics(listoffile, "MINIMUM", "DATA")
                    #outCellStatistics_min.save(os.path.join(LT_EVI_folder, newfilename_min))

                if arcpy.Exists(os.path.join(LT_EVI_folder, newfilename_max)):
                    print(newfilename_max + " exists")
                else:
                    outCellStatistics_max = CellStatistics(listoffile, "MAXIMUM", "DATA")
                    #outCellStatistics_max.save(os.path.join(LT_EVI_folder, newfilename_max))
            messages.addmessage("Finish Creating Long Term Average Data........")

            #=============== Preparing Land Surface Temperature Data===============#
            messages.addmessage("Processing Land Surface Temperature Data......")
            messages.addmessage("Calculating Data for Long term LST......")
            LST_data_array = []
            month_year_lta_mod11c3 = []
            for filename_11c3 in os.listdir(mod11c3_folder):
                if filename_11c3.endswith(".hdf"):
                    data_array.append(filename_11c3)
                    parseString = filename_11c3.split('.')
                    filename_my_11c3 = parseString[1]
                    yearString = filename_my_11c3[1:5]
                    messages.addmessage(yearString)
                    if int(yearString) <= int(lst_year):
                        month_year_lta_mod11c3.append(filename_11c3)
            messages.addmessage("data needed to calculate long term average until "+lst_year+" is "+str(num_of_years_lst))
            messages.addmessage("data available is "+str(len(month_year_lta_mod11c3)))
            messages.addmessage("data available is "+str(len(month_year_lta_mod11c3)))
            if num_of_years_lst == len(month_year_lta_mod13a3):
                messages.addmessage("data LST for calculating long term average is complete......")
                messages.addmessage("Start Processing MODIS Land Surface Temperature......")
                messages.addmessage("Creating Folder to store day and night LST......")
                LST_folder = output_folder+ "\\lta_LST"
                LST_folder_day = output_folder+ "\\lta_LST\\Day"
                LST_folder_night = output_folder+ "\\lta_LST\\Night"
                if not os.path.exists(LST_folder_day):
                    os.mkdir(LST_folder)
                    os.mkdir(LST_folder_day)
                    messages.addmessage("LST Day Folder Created......")
                if not os.path.exists(LST_folder_night):
                    os.mkdir(LST_folder_night)
                    messages.addmessage("LST Night Folder Created......")
                messages.addmessage("Extracting LST Day......")
                mod13a3Process(mod11c3_folder, 0, LST_folder_day, 'lst_day')
                messages.addmessage("LST Day data are created")
                messages.addmessage("Extracting LST Night......")
                mod13a3Process(mod11c3_folder, 5, LST_folder_night, 'lst_night')
                messages.addmessage("LST Night data are created")
                messages.addmessage("Calculating LST Average......")
                messages.addmessage("Creating Folder to store LST Average......")
                LST_folder_avg = LST_folder_day = output_folder+ "\\lta_LST\\Average"
                if not os.path.exists(LST_folder_avg):
                    os.mkdir(LST_folder_avg)
                    messages.addmessage("LST Average Folder Created......")
                LSTAverage(LST_folder_day,LST_folder_night,LST_folder_avg)
                messages.addmessage("LST Average calculation are done......")
                messages.addmessage("Calculating LST Average in celcius......")
                messages.addmessage("Creating Folder to store LST Average......")
                LST_folder_avg_cel = LST_folder_day = output_folder+ "\\lta_LST\\Average_Celcius"
                if not os.path.exists(LST_folder_avg_cel):
                    os.mkdir(LST_folder_avg_cel)
                    messages.addmessage("LST Average Celcius Folder Created......")
                kelvintocelcius(LST_folder_avg, LST_folder_avg_cel)
                messages.addmessage("Calculating LST Average in celcius are done......")
                messages.addmessage("Masking LST Average to subset file......")

                #============== Calculating Long Term Data for Land Surface Temperature ===============#
                messages.addmessage("Creating Folder to store LST Average......")
                Masked_LST_folder_avg_cel = LST_folder_day = output_folder+ "\\lta_LST\\Masked_Average_Celcius"
                if not os.path.exists(Masked_LST_folder_avg_cel):
                    os.mkdir(Masked_LST_folder_avg_cel)
                    messages.addmessage("Masked LST Average Celcius Folder Created......")
                messages.addmessage("Start Masking LST Average to subset file......")
                for file_global in os.listdir(LST_folder_avg_cel):
                    masking_filename = 'mask_{0}'.format(file_global)
                    if file_global.endswith(".tif"):
                        extractbymask = ExtractByMask(os.path.join(LST_folder_avg_cel, file_global) , subset_file)
                        extractbymask.save(os.path.join(Masked_LST_folder_avg_cel, masking_filename))

                messages.addmessage("Starts Creating Long Term Calculation Data for LST Data......")
                messages.addmessage("Creating Folder to store LSTmin and LSTmax......")
                LST_LTA_folder = output_folder+ "\\lta_LST\\Statistic"
                if not os.path.exists(LST_LTA_folder):
                    os.mkdir(LST_LTA_folder)
                    messages.addmessage("LSTmin and LSTmax Folder is Created......")

                dictionary = {}
                for i in month_list:
                    content = []
                    for file_monthly in os.listdir(Masked_LST_folder_avg_cel):
                        if file_monthly.endswith(".tif"):
                            parseString1 = file_monthly.split('.')
                            filename_my_11c3 = parseString[1]
                            DYear = filename_my_11c3[1:5]
                            J_date = filename_my_11c3[5:8]
                            #messages.addmessage(DYear +J_date)
                            Dmonth,jd,y = JulianDate_to_MMDDYYY(int(DYear), int(J_date))
                            if str(Dmonth).zfill(2) == i and int(DYear) <= int(lst_year):
                                content.append(os.path.join(Masked_LST_folder_avg_cel, file_monthly))
                    dictionary[i] = content
                #messages.addmessage(dictionary)
                for k in month_list:
                    index = k
                    listoffile = dictionary[index]
                    ext = ".tif"
                    years_num = int(lst_year)-1999
                    newfilename_min = 'MOD11C3.006__1_km_monthly_EVI_2000-{0}.{1}.monthly.{2}yrs.min{3}'.format(lst_year, k, years_num, ext)
                    newfilename_max = 'MOD13C3.006__1_km_monthly_EVI_2000-{0}.{1}.monthly.{2}yrs.max{3}'.format(lst_year, k, years_num, ext)

                    if arcpy.Exists(os.path.join(LST_LTA_folder, newfilename_min)):
                        print(newfilename_min + " exists")
                    else:
                        outCellStatistics_min = CellStatistics(listoffile, "MINIMUM", "DATA")
                        outCellStatistics_min.save(os.path.join(LST_LTA_folder, newfilename_min))

                    if arcpy.Exists(os.path.join(LST_LTA_folder, newfilename_max)):
                        print(newfilename_max + " exists")
                    else:
                        outCellStatistics_max = CellStatistics(listoffile, "MAXIMUM", "DATA")
                        outCellStatistics_max.save(os.path.join(LST_LTA_folder, newfilename_max))
                messages.addmessage("Finish Calculating LSTmin and LSTmax........")

                #========================== Starts Calculating TCI===========================#
                messages.addmessage("Start Calculating TCI........")

                for each_mask_file in os.listdir(Masked_LST_folder_avg_cel):
                    if each_mask_file.endswith(".tif"):
                        parse_string_mask = each_mask_file.split('.')
                        j_date_mask = parse_string_mask[1][5:8]
                        year_mask = parse_string_mask[1][1:5]
                        month_mask,jd,y = JulianDate_to_MMDDYYY(int(year_mask), int(j_date_mask))
                        for each_lta_file in os.listdir(LST_LTA_folder):
                            if each_lta_file.endswith(".tif"):
                                parse_string_lta = each_lta_file.split('.')
                                if parse_string_lta[3] == month_mask:
                                    lta_used = os.path.join(lta_folder, each_lta_file)
                        ext = ".tif"
                        ra_filename = 'mask_cli_chirps-v2.0.{0}.{1}.ratio_anom{2}'.format(year_mask, month_mask, ext)

                        if arcpy.Exists(os.path.join(ra_folder, ra_filename)):
                            messages.addmessage("file " + ra_filename + " is already exist")
                        else:
                            newRaster = Int(100 * Raster(os.path.join(masking_folder, each_mask_file)) / Raster(lta_used))
                            newRaster.save(os.path.join(ra_folder, ra_filename))
                            messages.addmessage("file " + ra_filename + " is created")
                arcpy.CheckInExtension("spatial")
        return
