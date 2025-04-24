import gspread
import json
import pandas as pd
import openpyxl
import os
import sys
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt, QSize, QFile, QTextStream
from PySide6.QtWidgets import QSizePolicy, QListWidgetItem, QListWidget, QMessageBox, QDialog, QFrame, QScrollArea, QGridLayout, QSpinBox, QLabel,  QApplication, QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton
import numpy as np
from datetime import datetime, timedelta, date
import math

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

#scrolling would often cause spinbox values to increase accidentally.
class SpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

#Not in use.
class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WARNING!!!")

        self.layout = QVBoxLayout()
        message = QLabel("Are you sure you want to reallocate this weeks build schedule?\nThis will delete the daily build list!")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)




class Forecast(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Wicker Shop Helper')

        

        #Etsy and shopify have diffent item names. Shopify has a value in its dictionary to plug into the etsy build list
        self.shopify_build_list = {
            'The Elliott Turntable Station' : [[0, 0, 0, 0, 0, 0], 'The Elliott Turntable Station: For Easy Listening with Soft Close Drawers - Solid Wood 12" Vinyl Record Storage', [], []],
            'The Irving Turntable Station With Sliding Doors' : [[0, 0, 0, 0, 0, 0], 'The Irving Turntable Station With Sliding Doors: Record Player Stand with Bookshelf Vinyl Record Storage and Flip Forward Bins', [], []],
            'The Speaker Stand Set' : [[0, 0, 0, 0, 0, 0], 'Custom Speaker Stand set of 2 handmade in Portland Oregon // Solid Oak and Steel // Fits any Speaker', [], []],
            'The Irving Tallboy' : [[0, 0, 0, 0, 0, 0], 'The Irving Tallboy - Vinyl Listening Station with Flip Forward Bins and Record Player Stand', [], []],
            'The Tallboy Turntable Station: Record Player Stand With Vinyl Record Storage' : [[0, 0, 0, 0, 0, 0], 'The Tallboy Turntable Station: Record Player Stand With Vinyl Record Storage', [], []],
            'The Zenith Tallboy - Vinyl Record Storage Turntable Stand' : [[0, 0, 0, 0, 0, 0], 'The Zenith Tallboy - Vinyl Record Storage Turntable Stand', [], []],
            'The Deluxe Tallboy Vinyl Record Storage': [[0, 0, 0, 0, 0, 0], 'The Deluxe Tallboy Vinyl Record Storage: Flip Bins that Display Your Collection of 120+ Vinyl Records', [], []],
            'The Hamilton Turntable Station' : [[0, 0, 0, 0, 0, 0], 'The Hamilton Turntable Station: By Collectors, For Collectors', [], []],
            'The Irving Turntable Station' : [[0, 0, 0, 0, 0, 0], 'The Irving Turntable Station: Bookshelf Style Vinyl Record Storage', [], []],
            'The Turntable Station' : [[0, 0, 0, 0, 0, 0], 'The Turntable Station: Vinyl Record Storage', [], []],
            'The HalfStack Turntable Station' : [[0, 0, 0, 0, 0, 0], 'The Halfstack Turntable Station: Vinyl Record Storage', [], []],
            'The Deluxe Vinyl Record Storage' : [[0, 0, 0, 0, 0, 0], 'The Deluxe Vinyl Record Storage : Elevate Your Space', [], []],
            'The Vinyl Storage End Table' : [[0, 0, 0, 0, 0, 0], 'The Vinyl Storage End Table', []],
            'The Deluxe Jr. Vinyl Record Storage' : [[0, 0, 0, 0, 0, 0], 'The Deluxe Jr. : Vinyl Record Storage For Your Growing Collection', [], []],
            'The Milk Crate Alternative: 12" Vinyl Record Storage' : [[0, 0, 0, 0, 0, 0], 'The Milk Crate Alternative: 12-Inch Vinyl Record Storage', [], []],
            'The Cube : 12" Vinyl Storage Crate' : [[0, 0, 0, 0, 0, 0], 'The Cube: 12-Inch Record Storage Crate', [], []],
            'The 7inch Crate' : [[0, 0, 0, 0, 0, 0], '7-Inch Record Storage Crate', [], []],
            'The Hawthorne Coffee Table' : [[0, 0, 0, 0, 0, 0], 'The Hawthorne Coffee Table', [], []],
            'The Clinton End Table' : [[0, 0, 0, 0, 0, 0], 'The Clinton End Table - Made by hand from Solid Wood In Portland Oregon', [], []],
            'BN1' : [[0, 0, 0, 0, 0, 0], 'BN1'],
            'BN2' : [[0, 0, 0, 0, 0, 0], 'BN2'],
            'BN3' : [[0, 0, 0, 0, 0, 0], 'BN3'],
            'BN4' : [[0, 0, 0, 0, 0, 0], 'BN4'],
            'BN5' : [[0, 0, 0, 0, 0, 0], 'BN5'],
            'Vinyl Record Display Wall Hanger' : [[0, 0, 0, 0, 0, 0], 'WickerWoodWorks Vinyl Record Display Wall Hanger - Make your Collection a Work of Art - Record Ledge / Vinyl Shelf', [], []],
            'Oak Vinyl Record Display' : [[0, 0, 0, 0, 0, 0], 'Oak Vinyl Record Display - As solid as a 180 gram repress, your great grand children will be displaying your collection on this', [], []],
            'Wire Divider Retrofit Kit' : [[0, 0, 0, 0, 0, 0], 'Wire Divider Add-on', [], []],
            'The Vinyl Record Dividers' : [[0, 0, 0, 0, 0, 0], 'new! Vinyl Record Divider Set - Alphabetize your collection - Vinyl Record Genre Dividers - Custom Sets Available - Record Collector Gifts', [], []],
            'wood leg set' : [[0, 0, 0, 0, 0, 0], 'wood leg set', [], []],
            'Custom Stain or Paint Color' : [[0, 0, 0, 0, 0, 0], 'Custom Stain or Paint Color', [], []],
        }
        

        #The below not is a reference to the spread sheet and which values relate to it. ID is for history tracking.
        self.build_list = { # 'var' : [row], [col, c, ,c, c , c], [quantity week 1, quanity week 2, ...], [IDs]
            'The Elliott Turntable Station: For Easy Listening with Soft Close Drawers - Solid Wood 12" Vinyl Record Storage' : [0, [], [0, 0, 0, 0, 0, 0], []],
            'The Irving Turntable Station With Sliding Doors: Record Player Stand with Bookshelf Vinyl Record Storage and Flip Forward Bins' : [1, [], [0, 0, 0, 0, 0, 0], []],
            'Custom Speaker Stand set of 2 handmade in Portland Oregon // Solid Oak and Steel // Fits any Speaker' : [2, [], [0, 0, 0, 0, 0, 0], []],
            'The Irving Tallboy - Vinyl Listening Station with Flip Forward Bins and Record Player Stand' : [3, [], [0, 0, 0, 0, 0, 0], []],
            'The Tallboy Turntable Station: Record Player Stand With Vinyl Record Storage' : [4, [], [0, 0, 0, 0, 0, 0], []],
            'The Zenith Tallboy - Vinyl Record Storage Turntable Stand' : [5, [], [0, 0, 0, 0, 0, 0], []],
            'The Deluxe Tallboy Vinyl Record Storage: Flip Bins that Display Your Collection of 120+ Vinyl Records' : [6, [], [0, 0, 0, 0, 0, 0], []],
            'The Hamilton Turntable Station: By Collectors, For Collectors' : [7, [], [0, 0, 0, 0, 0, 0], []],
            'The Irving Turntable Station: Bookshelf Style Vinyl Record Storage' : [8, [], [0, 0, 0, 0, 0, 0], []],
            'The Turntable Station: Vinyl Record Storage' : [9, [], [0, 0, 0, 0, 0, 0], []],
            'The Halfstack Turntable Station: Vinyl Record Storage' : [10, [], [0, 0, 0, 0, 0, 0], []],
            'The Deluxe Vinyl Record Storage : Elevate Your Space' : [11, [], [0, 0, 0, 0, 0, 0], []],
            'The Vinyl Storage End Table' : [12, [], [0, 0, 0, 0, 0, 0], []],
            'The Deluxe Jr. : Vinyl Record Storage For Your Growing Collection' : [13, [], [0, 0, 0, 0, 0, 0], []],
            'The Milk Crate Alternative: 12-Inch Vinyl Record Storage' : [14, [], [0, 0, 0, 0, 0, 0], []],
            'The Cube: 12-Inch Record Storage Crate' : [15, [], [0, 0, 0, 0, 0, 0], []],
            '7-Inch Record Storage Crate' : [16, [], [0, 0, 0, 0, 0, 0], []],
            'The Hawthorne Coffee Table' : [17, [], [0, 0, 0, 0, 0, 0], []],
            'The Clinton End Table - Made by hand from Solid Wood In Portland Oregon' : [18, [], [0, 0, 0, 0, 0, 0], []],
            'BN1' : [19, [], [0, 0, 0, 0, 0, 0], []],
            'BN2' : [20, [], [0, 0, 0, 0, 0, 0], []],
            'BN3' : [21, [], [0, 0, 0, 0, 0, 0], []],
            'BN4' : [22, [], [0, 0, 0, 0, 0, 0], []],
            'BN5' : [23, [], [0, 0, 0, 0, 0, 0], []],
            'WickerWoodWorks Vinyl Record Display Wall Hanger - Make your Collection a Work of Art - Record Ledge / Vinyl Shelf' : [24, [], [0, 0, 0, 0, 0, 0], []],
            'Oak Vinyl Record Display - As solid as a 180 gram repress, your great grand children will be displaying your collection on this' : [25, [], [0, 0, 0, 0, 0, 0], []],
            'Wire Divider Add-on' : [26, [], [0, 0, 0, 0, 0, 0], []],
            'new! Vinyl Record Divider Set - Alphabetize your collection - Vinyl Record Genre Dividers - Custom Sets Available - Record Collector Gifts' : [27, [], [0, 0, 0, 0, 0, 0], []],
            'wood leg set' : [28, [], [0, 0, 0, 0, 0, 0], []],
            'Custom Stain or Paint Color' : [29, [], [0, 0, 0, 0, 0, 0], []],
        }

        self.shopify_build_list = {k.lower(): v for k, v in self.shopify_build_list.items()}
        self.build_list =  {k.lower(): v for k, v in self.build_list.items()}

        

        
        self.forecast_numbers = []
        #alert if product was missed in build.
        self.alert_list = []
        #alert if product hasn't been shipped after two weeks of build date.
        self.two_week_built_alert = []
        #History tracker item
        self.item_ids = {}
        #Used for total label and item allocation for history.
        self.product_numers_by_week = []

        '''
        if getattr(sys, "frozen", False):
            current_dir = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        '''

        current_dir = os.path.dirname(os.path.abspath(__file__))
    
        #Working directory for hisothyr file.
        self.history_path = 'C:\Coding\WickerShops\history\history.json'
        #self.history_path = os.path.join(current_dir, 'history', 'history.json')

        #Cheker if there's a hisotry file.
        try:
            with open(self.history_path, 'r') as f:
                self.item_ids = json.load(f)
        except FileNotFoundError:
            print('No history file found.')

        #Google authenticator
        access = gspread.oauth()

        #getting google sheet info by its key
        sheet_id = '1ut2CdoU3ZF--pN-UQDLXvE240dTFXZqM6DvuB_VcSdY'
        wb = access.open_by_key(sheet_id)

        #extracting a sheet of info
        sheet_id = 0
        self.sheet = wb.get_worksheet_by_id(sheet_id)

        #Acessing etsy csv info. Joining new info to master sheet.
        spreadsheet_path = 'C:\Coding\WickerShops\spreadSheets'
        try:
            etsy_path = os.path.join(spreadsheet_path, 'Etsy CSVs')

            # Get a list of all CSV files in the folder
            csv_files = [f for f in os.listdir(etsy_path) if f.endswith('.csv')]

            # Create an empty list to store the dataframes
            etsy_list = []
            # Read each CSV file and append it to the list
            for csv_file in csv_files:
                file_path = os.path.join(etsy_path, csv_file)
                df = pd.read_csv(file_path)
                etsy_list.append(df)
                os.remove(file_path)
            try:
                master_etsy_path = os.path.join(spreadsheet_path, 'Master CSVs', 'EtsyMaster.csv')
                master_etsy = pd.read_csv(master_etsy_path)
                etsy_list.append(master_etsy)
            except:
                print("first time making master etsy csv.")
            # Concatenate all dataframes into one
            combined_df = pd.concat(etsy_list, ignore_index=True)
            
            # Save the combined dataframe to a new CSV file (optional)
            combined_df.to_csv(master_etsy_path, index=False)
            
        except FileNotFoundError:
            print('No new etsy CSV file found.')
        
        #Acessing Shopify csv info. Joining new info to master sheet.
        try:
            shopify_path = os.path.join(spreadsheet_path, 'Shopify CSVs')

            # Get a list of all CSV files in the folder
            csv_files = [f for f in os.listdir(shopify_path) if f.endswith('.csv')]

            # Create an empty list to store the dataframes
            shopify_list = []

            # Read each CSV file and append it to the list
            for csv_file in csv_files:
                file_path = os.path.join(shopify_path, csv_file)
                df = pd.read_csv(file_path)
                shopify_list.append(df)
                os.remove(file_path)
            try:
                master_shopify_path = os.path.join(spreadsheet_path, 'Master CSVs', 'ShopifyMaster.csv')
                master_shopify = pd.read_csv(master_shopify_path)
                shopify_list.append(master_shopify)
            except:
                print("making master shopify csv.")
            # Concatenate all dataframes into one
            combined_df = pd.concat(shopify_list, ignore_index=True)

            # Save the combined dataframe to a new CSV file (optional)
            combined_df.to_csv(master_shopify_path, index=False)
        except FileNotFoundError:
            print('No new etsy CSV file found.')


        #Opening and sorting CSVs by oldest date
        master_shopify_path = os.path.join(spreadsheet_path, 'Master CSVs', 'ShopifyMaster.csv')
        shopify_sold = pd.read_csv(master_shopify_path)
        shopify_buyers = shopify_sold.iloc[::]
        shopify_buyers['Created at'] = pd.to_datetime(shopify_buyers['Created at']) 
        shopify_buyers['Created at'] = shopify_buyers['Created at'].dt.strftime('%m/%d/%y')
        shopify_buyers = shopify_buyers.sort_values(by='Created at')

 


        master_etsy_path = os.path.join(spreadsheet_path, 'Master CSVs', 'EtsyMaster.csv')
        buyers = pd.read_csv(master_etsy_path)
        buyers = buyers.iloc[::]
        buyers['Sale Date'] = pd.to_datetime(buyers['Sale Date'], format='%m/%d/%y')
        buyers['Sale Date'] = buyers['Sale Date'].dt.strftime('%m/%d/%y')
        buyers = buyers.sort_values(by='Sale Date')



        #Date checkers to be used in mulitple spots 
        self.today =datetime.now()
        self.to_monday = self.today.weekday()
        monday_delta = timedelta(days=self.to_monday)
        sunday_delta = timedelta(days=6)
        self.full_monday = self.today - monday_delta
        self.full_sunday = self.full_monday + sunday_delta
        self.string_sunday = datetime.strftime(self.full_sunday, '%m/%d/%y')
        self.sunday_ = datetime.strptime(self.string_sunday, '%m/%d/%y')
        self.month_name = self.full_monday.strftime("%B")
        self.monday = self.full_monday.strftime('%d')
        if self.monday[0] == '0':
            self.monday = self.monday [1:]

        first_week = shopify_buyers['Created at'][0]
        first_week = datetime.strptime(first_week, '%m/%d/%y')
        the_day = first_week.weekday()
        sunday_value = 6
        to_sunday = sunday_value - the_day
        add_delta = timedelta(days=to_sunday)
        self.shopify_sunday = first_week + add_delta
        self.shopify_monday = self.shopify_sunday - timedelta(days=6)


        #Shopify parses items to proper place (build_list, hiostry_checker, item_ids). Checks dates to set alerts.
        #Check if shipped and stores data in long term history. It does it all.
        shopify_csv_finished = []
        self.weekly_label = []
        shopify_days_step = 0
        shopify_build_list_week = 0
        shopify_alert_time = timedelta(weeks=5)
        print('Shopify:')
        for i in range(len(shopify_buyers)):
            if shopify_build_list_week == 6:
                break
            date_shipped = shopify_buyers.iloc[i]['Fulfillment Status']
            if pd.isna(date_shipped) == 'fullfilled':
                print('skipped shoify')
                shopify_csv_finished.append(i)
                continue
            sale_date = shopify_buyers.iloc[i]['Created at']
            shopify_date = datetime.strptime(sale_date, '%m/%d/%y')
            #Date manager. 
            if shopify_date > self.shopify_sunday - timedelta(days=shopify_days_step):
                monday_label = self.full_sunday - timedelta(days=shopify_days_step)
                shopify_days_step += 7
                #shopify_build_list_week is the location for the build_list its in
                shopify_build_list_week += 1
                #6 Week forecast.
                if shopify_build_list_week == 6:
                    break
            shopify_id = shopify_buyers.iloc[i]['Name']
            shopify_buyer = shopify_buyers.iloc[i]['Billing Name']
            shopify_item_name = shopify_sold.iloc[i]['Lineitem name'].lower()
            string_slice = shopify_item_name.find('-') - 1
            shopify_item_name = shopify_item_name[:string_slice]
            if shopify_item_name not in self.shopify_build_list:
                print('item not in shopify build  list')
                continue
            id_name = self.shopify_build_list[shopify_item_name][1].lower()
            #Checking if item should have been shipped already.
            if shopify_id in self.item_ids:
                if id_name in self.item_ids[shopify_id]:
                    date = self.item_ids[shopify_id][id_name][0][0]
                    date = datetime.strptime(str(date), '%m/%d/%y')
                    if date < self.sunday_:
                        if date < self.sunday_ - timedelta(weeks=2):
                            self.two_week_built_alert.append([shopify_id, id_name])
                        continue
            shopidfy_quantity = shopify_buyers.iloc[i]['Lineitem quantity']
            #hisotry checker and alloocator. If build a build date was changed this is to keep track
            if shopify_id in self.item_ids and id_name in self.item_ids[shopify_id]:
                    count = 0
                    for s in self.item_ids[shopify_id][id_name]:
                        datetime_holder = datetime.strptime(s[0], '%m/%d/%y')
                        print((datetime_holder , self.sunday_))
                        week = (datetime_holder - self.sunday_).days / 7
                        week = int(week)
                        self.build_list[id_name][2][week] += int(s[1])
                        self.build_list[id_name][3].append([shopify_id, self.sunday_])
                        self.item_ids[shopify_id][id_name][count][0] = self.sunday_
                        count += 1
                    count = 0
            #If no history, CSV info is used instead.
            #Item_ids is a nested dictiopnary to keep track of large orders and individual items in them.
            else:
                self.build_list[id_name][2][shopify_build_list_week] += int(shopidfy_quantity)
                if shopify_id not in self.item_ids:
                    self.item_ids[shopify_id] =  {id_name : [[self.sunday_, shopidfy_quantity]]} 
                elif id_name not in self.item_ids[shopify_id]:
                    self.item_ids[shopify_id][id_name] = [[self.sunday_, shopidfy_quantity]]
                else:
                    self.item_ids[shopify_id][id_name].append([self.sunday_, shopidfy_quantity])
                #This is used to keep track of which item to pull first and keep track of its info.
                self.build_list[id_name][3].append([shopify_id, shopify_date])  
            #If an item isn't in the build list after 4 weeks of being order theres an alert
            if shopify_date + shopify_alert_time <= self.today:
                self.alert_list.append(shopify_id)


        first_week = buyers['Sale Date'][0]
        first_week = datetime.strptime(first_week, '%m/%d/%y')
        the_day = first_week.weekday()
        sunday_value = 6
        to_sunday = sunday_value - the_day
        add_delta = timedelta(days=to_sunday)
        self.etsy_sunday = first_week + add_delta

        #Shopify parses items to proper place (build_list, hiostry_checker, item_ids). Checks dates to set alerts.
        #Check if shipped and stores data in long term history. It does it all.
        #line by line explanation in shopify.
        alert_time = timedelta(weeks=5)
        build_list_week = 0
        days_step = 0
        etsy_csv_finished = []
        print("etsy:")
        for i in range(len(buyers)):
            if build_list_week == 6:
                break
            date_shipped = buyers.iloc[i]['Date Shipped']
            if pd.isna(date_shipped) == False:
                print('skipped etsy')
                etsy_csv_finished.append(i)
                continue
            sale_date = buyers.iloc[i]['Sale Date']
            csv_date = datetime.strptime(sale_date, '%m/%d/%y')
            if csv_date > self.etsy_sunday + timedelta(days=days_step):
                build_list_week += 1
                days_step += 7
                if build_list_week == 6:
                    break
            buyer = buyers.iloc[i]['Buyer']
            item_name = buyers.iloc[i]['Item Name'].lower()
            transaction_id = str(buyers.iloc[i]['Transaction ID'])
            if transaction_id in self.item_ids:
                if item_name in self.item_ids[shopify_id]:
                    date = self.item_ids[transaction_id][item_name][0][0]
                    date = datetime.strptime(str(date), '%m/%d/%y')
                    if date < self.sunday_:
                        if date < self.sunday_ - timedelta(weeks=2):
                            self.two_week_built_alert.append([transaction_id, item_name])
                        continue
            quantity = buyers.iloc[i]['Quantity']
            if transaction_id in self.item_ids and item_name in self.item_ids[transaction_id]:
                count = 0
                for s in self.item_ids[transaction_id][item_name]:
                    datetime_holder = datetime.strptime(s[0], '%m/%d/%y')
                    week = (datetime_holder - self.sunday_).days / 7
                    week = int(week)
                    print(datetime_holder, self.sunday_)
                    print(item_name)
                    print(week)
                    self.build_list[item_name][2][week] += int(s[1])
                    six_week_place = self.sunday_ + timedelta(weeks=week)
                    self.build_list[item_name][3].append([transaction_id, self.sunday_])
                    self.item_ids[transaction_id][item_name][count][0] = self.sunday_
                    count += 1
                count = 0
            else: 
                self.build_list[item_name][2][build_list_week] += int(quantity)   
                if transaction_id not in self.item_ids:
                    self.item_ids[transaction_id] =  {item_name : [[self.sunday_, quantity]]}
                elif item_name not in self.item_ids[transaction_id]:
                    self.item_ids[transaction_id][item_name] = [[self.sunday_, quantity]]
                else:
                    self.item_ids[transaction_id][item_name].append([self.sunday_, quantity])
                self.build_list[item_name][3].append([transaction_id, csv_date])
            if csv_date + alert_time <= self.today:
                self.alert_list.append(transaction_id)
        
        #Organizes item pull order. The seperate parsers makes them split.
        for i in self.build_list:
            self.build_list[i][3].sort(key=lambda x: x[1])
        
        #Label maker for 6 week forecast
        days_step = 0
        for i in range(6):
            sunday_label = self.full_sunday + timedelta(days=days_step)
            monday_label = sunday_label - timedelta(days=6)
            self.weekly_label.append([str(monday_label.month) + '.' + str(monday_label.day) + ' - ' + str(sunday_label.month) + '.' +str(sunday_label.day)])
            days_step += 7
        
        long_term_history = []
        for i in shopify_csv_finished:
            shopify_buyers.iloc[i].append(long_term_history)
            shopify_buyers.drop(index=i, inplace=True) 
        shopify_buyers.to_csv(master_shopify_path, index=False) 

        for i in etsy_csv_finished:
            buyers.iloc[i].append(long_term_history)
            buyers.drop(index=i, inplace=True)
        buyers.to_csv(master_etsy_path, index=False)         

        finished_history_path = os.path.join(self.history_path, 'Finished Orders', 'Finished.json')
        if long_term_history != []:
            with open(finished_history_path, "r") as f:  # reading a file
                stored_history = json.load(f)  # deserialization

            stored_history.append(long_term_history)

            with open(finished_history_path, "w") as f:
                json.dump(stored_history, f) 
            

        #Side Labels / Procut Labels
        label1 = QLabel('Elliott')
        label2 = QLabel('Irving \n& Doors')
        label3 = QLabel('Speaker\nStand')
        label4 = QLabel('Irving\nTallboy')
        label5 = QLabel('Tallboy')
        label6 = QLabel('Zenith')
        label7 = QLabel('Deluxe\nTallboy')
        label8 = QLabel('Hamilton')
        label9 = QLabel('Irving')
        label10 = QLabel('Turntable\nStation')
        label11 = QLabel('Halfstack')
        label12 = QLabel('Deluxe')
        label13 = QLabel('End Table')
        label14 = QLabel('Deluxe Jr.')
        label15 = QLabel('Milk Crate')
        label16 = QLabel('Cube')
        label17 = QLabel('7-Inch')
        label18 = QLabel('Hawthorne')
        label19 = QLabel('Clinton')
        label20 = QLabel('BN1')
        label21 = QLabel('BN2')
        label22= QLabel('BN3')
        label23 = QLabel('BN4')
        label24 = QLabel('BN5')
        label25 = QLabel('Wall Hanger')
        label26 = QLabel('Record\nDisplay')
        label27 = QLabel('Wire\nDivider')
        label28 = QLabel('Record\nDivider')
        label29 = QLabel('wood leg')
        label30 = QLabel('Custom\nColor')
        #made into a list to iterate over.
        self.product_label_list = [label1, label2, label3, label4, label5, label6, label7, label8, label9, label10, label11, label12, label13, label14, label15, label16, label17, label18, label19, label20, label21, label22, label23, label24, label25, label26, label27, label28, label29, label30]
        
        #Item weekly total put in a list [week1, week2, ...]
        self.product_count = []
        for i in self.build_list:
            self.product_count.append(self.build_list[i][2])
        
        


        #side bar
        
        self.full_list = QListWidget()

        self.menu_list = [
            {
                "name": "Six Week Forecast",
                "icon": "./icon/six_week.svg"
            },
            {
                "name": "Current Week",
                "icon": "./icon/currnet_week.svg"
            },
            {
                "name": "Past Orders",
                "icon": "./icon/PastOrders.svg"
            },
        ]

        for menu in self.menu_list:
        

            # Set items for the side menu with icons and text
            item_new = QListWidgetItem()
            #item_new.setIcon(QIcon(menu.get("icon")))
            item_new.setText(menu.get("name"))
            self.full_list.addItem(item_new)
            self.full_list.setCurrentRow(0)


        self.full_list.currentRowChanged['int'].connect(self.row_change)

        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_label = QLabel("Title")
        title_icon = QLabel('.png ipsum')
        collapse_button = QPushButton('png collapse')
        title_layout.addWidget(title_label)
        title_layout.addWidget(collapse_button)

        #Top label maker
        self.product_background = QFrame()
        self.product_layout = QHBoxLayout(self.product_background)
        self.top_product_label = QLabel('Products:')
        self.top_product_label.setWordWrap(True)
        self.top_product_label.setFixedSize(QSize(90, 45))
        self.top_product_label.setAlignment(Qt.AlignCenter)
        self.product_layout.addWidget(self.top_product_label)
        for i in self.product_label_list:
            spacer_frame = QFrame()
            self.button_spacer_layout = QVBoxLayout(spacer_frame)
            self.button_spacer = QPushButton("-", self)
            self.button_spacer.setVisible(False)
            self.button_spacer.setFocusPolicy(Qt.NoFocus)
            self.button_spacer_layout.addWidget(self.button_spacer)
            self.product_layout.addWidget(spacer_frame)
            self.product_layout.addWidget(i)
            i.setFixedSize(QSize(90, 45))
            i.setAlignment(Qt.AlignCenter)
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            line.setVisible(False)
            self.product_layout.addWidget(line)




        #Makes GUI by weekly rows. This will be doccumentaion for all 6 weeks. Weeks 2-5 have one more button since they have move build dates two ways.
        #I could make a method to creat all of these. Similar to spinbox logic.
        self.background_labels_wk1 = []    
        self.buttons_week1 = []
        self.week_one_total = 0
        for i in self.product_count:
            #Counters total items to build this week
            self.week_one_total += i[0]
        self.background1 = QFrame()
        self.background1.setObjectName('background1')
        self.week1_layout = QHBoxLayout(self.background1)
        #self.background1.setStyleSheet('background-color: #bedaf7; border: 1px solid black;')

        #Week label and total label
        self.week1_label = QLabel(self.weekly_label[0][0] + '\n' + 'Total: ' + str(self.week_one_total), ObjectName='week1_label')
        self.week1_layout.addWidget(self.week1_label)
        self.week1_label.setFixedSize(QSize(90, 45))
        self.week1_label.setAlignment(Qt.AlignCenter)
        #seperator for column
        total_seperator = QFrame(ObjectName='total_seperator')
        total_seperator.setFrameShape(QFrame.VLine)
        total_seperator.setFrameShadow(QFrame.Plain)
        total_seperator.setLineWidth(1)
        self.week1_layout.addWidget(total_seperator)
        for i in self.build_list:
            self.button_background_week1 = QFrame(ObjectName='button_background_week1')
            #button layout and logic
            self.button_layout_week1 = QVBoxLayout(self.button_background_week1)
            self.button_bottom_week1 = QPushButton("-", self, ObjectName='button_bottom_week1')
            self.button_bottom_week1.setStyleSheet('background-color: #deecfb;')
            #NEEDED! Without this button clickes would randomly snap scroll area to a seemingly random place.
            self.button_bottom_week1.setFocusPolicy(Qt.NoFocus)
            self.button_layout_week1.addWidget(self.button_bottom_week1)
            self.background1_label = QLabel(str(self.build_list[i][2][0]), ObjectName='background1_label')
            #Turns buttons off is at 0
            if self.background1_label.text() == '0':
                self.button_bottom_week1.setEnabled(False)
            self.background1_label.setFixedSize(QSize(90, 45))
            self.background1_label.setAlignment(Qt.AlignCenter)
            self.background_labels_wk1.append(self.background1_label)
            self.week1_layout.addWidget(self.button_background_week1)
            self.week1_layout.addWidget(self.background1_label)
            #connects to button logic
            self.button_bottom_week1.clicked.connect(self.week1_mover)
            self.buttons_week1.append(self.button_bottom_week1)
            #Column seperator.
            line = QFrame(ObjectName='mulit_seperator')
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            self.week1_layout.addWidget(line)
        self.background1.setFrameStyle(QFrame.Box | QFrame.Plain)

       
        self.background_labels_wk2 = []
        self.buttons_week2 = []
        self.week_two_total = 0
        for i in self.product_count:
            self.week_two_total += i[1]
        self.background2 = QFrame(ObjectName='background2')
        
        self.week2_layout = QHBoxLayout(self.background2)
        self.week2_label = QLabel(self.weekly_label[1][0] + '\n' + 'Total: ' + str(self.week_two_total))
        self.week2_label.setFixedSize(QSize(90, 45))
        self.week2_label.setAlignment(Qt.AlignCenter)
        self.week2_layout.addWidget(self.week2_label)
        total_seperator2 = QFrame()
        total_seperator2.setFrameShape(QFrame.VLine)
        total_seperator2.setFrameShadow(QFrame.Plain)
        total_seperator2.setLineWidth(1)
        self.week2_layout.addWidget(total_seperator2)
        for i in self.build_list:
            self.button_background_week_2 = QFrame()
            self.button_layout_week2 = QVBoxLayout(self.button_background_week_2)
            self.button_top_week2 = QPushButton('+', self)
            self.button_top_week2.setStyleSheet('background-color: #deecfb;')
            self.button_top_week2.setFocusPolicy(Qt.NoFocus)
            self.button_bottom_week2 = QPushButton("-", self)
            self.button_bottom_week2.setStyleSheet('background-color: #deecfb;')
            self.button_bottom_week2.setFocusPolicy(Qt.NoFocus)
            self.button_layout_week2.addWidget(self.button_top_week2)
            self.button_layout_week2.addWidget(self.button_bottom_week2)            
            self.background2_label = QLabel(str(self.build_list[i][2][1]))
            if self.background2_label.text() == '0':
                self.button_top_week2.setEnabled(False)
                self.button_bottom_week2.setEnabled(False)
            self.background2_label.setFixedSize(QSize(90, 45))
            self.background2_label.setAlignment(Qt.AlignCenter)
            self.background_labels_wk2.append(self.background2_label)
            self.week2_layout.addWidget(self.button_background_week_2)
            self.week2_layout.addWidget(self.background2_label)
            self.button_top_week2.clicked.connect(self.week2_mover)
            self.button_bottom_week2.clicked.connect(self.week2_mover)
            self.buttons_week2.append(self.button_top_week2)
            self.buttons_week2.append(self.button_bottom_week2)
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            self.week2_layout.addWidget(line)
        self.background2.setFrameStyle(QFrame.Box | QFrame.Plain)


        self.background_labels_wk3 = []
        self.buttons_week3 = []
        self.week_three_total = 0
        for i in self.product_count:
           self.week_three_total += i[2]
        self.background3 = QFrame(ObjectName='background3')
        self.week3_layout = QHBoxLayout(self.background3)
        self.week3_label = QLabel(self.weekly_label[2][0] + '\n' + 'Total: ' + str(self.week_three_total))
        self.week3_label.setFixedSize(QSize(90, 45))
        self.week3_label.setAlignment(Qt.AlignCenter)
        self.week3_layout.addWidget(self.week3_label)
        total_seperator3 = QFrame()
        total_seperator3.setFrameShape(QFrame.VLine)
        total_seperator3.setFrameShadow(QFrame.Plain)
        total_seperator3.setLineWidth(1)
        self.week3_layout.addWidget(total_seperator3)
        for i in self.build_list:
            self.button_background_week_3 = QFrame()
            self.button_layout_week3 = QVBoxLayout(self.button_background_week_3)
            self.button_top_week3 = QPushButton('+', self)
            self.button_top_week3.setStyleSheet('background-color: #deecfb;')
            self.button_top_week3.setFocusPolicy(Qt.NoFocus)
            self.button_bottom_week3 = QPushButton("-", self)
            self.button_bottom_week3.setStyleSheet('background-color: #deecfb;')
            self.button_bottom_week3.setFocusPolicy(Qt.NoFocus)
            self.button_layout_week3.addWidget(self.button_top_week3)
            self.button_layout_week3.addWidget(self.button_bottom_week3)      
            self.background3_label = QLabel(str(self.build_list[i][2][2]))
            if self.background3_label.text() == '0':
                self.button_top_week3.setEnabled(False)
                self.button_bottom_week3.setEnabled(False)
            self.background3_label.setFixedSize(QSize(90, 45))
            self.background3_label.setAlignment(Qt.AlignCenter)
            self.background_labels_wk3.append(self.background3_label)
            self.week3_layout.addWidget(self.button_background_week_3)
            self.week3_layout.addWidget(self.background3_label)
            self.button_top_week3.clicked.connect(self.week3_mover)
            self.button_bottom_week3.clicked.connect(self.week3_mover)
            self.buttons_week3.append(self.button_top_week3)
            self.buttons_week3.append(self.button_bottom_week3)
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            self.week3_layout.addWidget(line)
        self.background3.setFrameStyle(QFrame.Box | QFrame.Plain)
       # self.week3_layout.setContentsMargins(0, 0, 0, 0)

        self.background_labels_wk4 = []
        self.buttons_week4 = []
        self.week_four_total = 0
        for i in self.product_count:
            self.week_four_total += i[3]
        self.background4 = QFrame(ObjectName='background4')
        self.week4_layout = QHBoxLayout(self.background4)
        self.week4_label = QLabel(self.weekly_label[3][0] + '\n' + 'Total: ' + str(self.week_four_total))
        self.week4_label.setFixedSize(QSize(90, 45))
        self.week4_label.setAlignment(Qt.AlignCenter)
        self.week4_layout.addWidget(self.week4_label)
        total_seperator4 = QFrame()
        total_seperator4.setFrameShape(QFrame.VLine)
        total_seperator4.setFrameShadow(QFrame.Plain)
        total_seperator4.setLineWidth(1)
        self.week4_layout.addWidget(total_seperator4)
        for i in self.build_list:
            self.button_background_week_4 = QFrame()
            self.button_layout_week4 = QVBoxLayout(self.button_background_week_4)
            self.button_top_week4 = QPushButton('+', self)
            self.button_top_week4.setStyleSheet('background-color: #deecfb;')
            self.button_top_week4.setFocusPolicy(Qt.NoFocus)
            self.button_bottom_week4 = QPushButton("-", self)
            self.button_bottom_week4.setStyleSheet('background-color: #deecfb;')
            self.button_bottom_week4.setFocusPolicy(Qt.NoFocus)
            self.button_layout_week4.addWidget(self.button_top_week4)
            self.button_layout_week4.addWidget(self.button_bottom_week4)      
            self.background4_label = QLabel(str(self.build_list[i][2][3]))
            if self.background4_label.text() == '0':
                self.button_top_week4.setEnabled(False)
                self.button_bottom_week4.setEnabled(False)
            self.background4_label.setFixedSize(QSize(90, 45))
            self.background4_label.setAlignment(Qt.AlignCenter)
            self.background_labels_wk4.append(self.background4_label)
            self.week4_layout.addWidget(self.button_background_week_4)
            self.week4_layout.addWidget(self.background4_label)
            self.button_top_week4.clicked.connect(self.week4_mover)
            self.button_bottom_week4.clicked.connect(self.week4_mover)
            self.buttons_week4.append(self.button_top_week4)
            self.buttons_week4.append(self.button_bottom_week4)
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            self.week4_layout.addWidget(line)
        self.background4.setFrameStyle(QFrame.Box | QFrame.Plain)
        #self.week4_layout.setContentsMargins(0, 0, 0, 0)

        self.background_labels_wk5 = []
        self.buttons_week5 = []
        self.week_five_total = 0
        for i in self.product_count:
            self.week_five_total += i[4]
        self.background5 = QFrame(ObjectName='background5')
        self.week5_layout = QHBoxLayout(self.background5)
        self.week5_label = QLabel(self.weekly_label[4][0] + '\n' + 'Total: ' + str(self.week_five_total))
        self.week5_label.setFixedSize(QSize(90, 45))
        self.week5_label.setAlignment(Qt.AlignCenter)
        self.week5_layout.addWidget(self.week5_label)
        total_seperator5 = QFrame()
        total_seperator5.setFrameShape(QFrame.VLine)
        total_seperator5.setFrameShadow(QFrame.Plain)
        total_seperator5.setLineWidth(1)
        self.week5_layout.addWidget(total_seperator5)
        for i in self.build_list:
            self.button_background_week_5 = QFrame()
            self.button_layout_week5 = QVBoxLayout(self.button_background_week_5)
            self.button_top_week5 = QPushButton('+', self)
            self.button_top_week5.setStyleSheet('background-color: #deecfb;')
            self.button_top_week5.setFocusPolicy(Qt.NoFocus)
            self.button_bottom_week5 = QPushButton("-", self)
            self.button_bottom_week5.setStyleSheet('background-color: #deecfb;')
            self.button_bottom_week5.setFocusPolicy(Qt.NoFocus)
            self.button_layout_week5.addWidget(self.button_top_week5)
            self.button_layout_week5.addWidget(self.button_bottom_week5)      
            self.background5_label = QLabel(str(self.build_list[i][2][4]))
            if self.background5_label.text() == '0':
                self.button_top_week5.setEnabled(False)
                self.button_bottom_week5.setEnabled(False)
            self.background5_label.setFixedSize(QSize(90, 45))
            self.background5_label.setAlignment(Qt.AlignCenter)
            self.background_labels_wk5.append(self.background5_label)
            self.week5_layout.addWidget(self.button_background_week_5)
            self.week5_layout.addWidget(self.background5_label)
            self.button_top_week5.clicked.connect(self.week5_mover)
            self.button_bottom_week5.clicked.connect(self.week5_mover)
            self.buttons_week5.append(self.button_top_week5)
            self.buttons_week5.append(self.button_bottom_week5)
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            self.week5_layout.addWidget(line)
        self.background5.setFrameStyle(QFrame.Box | QFrame.Plain)
        #self.week5_layout.setContentsMargins(0, 0, 0, 0)

        self.background_labels_wk6 = []
        self.buttons_week6 = []
        self.week_six_total = 0
        for i in self.product_count:
            self.week_six_total += i[5]
        self.background6 = QFrame(ObjectName='background6')
        self.week6_layout = QHBoxLayout(self.background6)
        self.week6_label = QLabel(self.weekly_label[5][0] + '\n' + 'Total: ' + str(self.week_six_total))
        self.week6_label.setFixedSize(QSize(90, 45))
        self.week6_label.setAlignment(Qt.AlignCenter)
        self.week6_layout.addWidget(self.week6_label)
        total_seperator6 = QFrame()
        total_seperator6.setFrameShape(QFrame.VLine)
        total_seperator6.setFrameShadow(QFrame.Plain)
        total_seperator6.setLineWidth(1)
        self.week6_layout.addWidget(total_seperator6)
        for i in self.build_list:
            self.button_background_week_6 = QFrame()
            self.button_layout_week6 = QVBoxLayout(self.button_background_week_6)
            self.button_top_week6 = QPushButton('+', self)
            self.button_top_week6.setStyleSheet('background-color: #deecfb;')
            self.button_top_week6.setFocusPolicy(Qt.NoFocus)
            self.button_layout_week6.addWidget(self.button_top_week6)     
            self.background6_label = QLabel(str(self.build_list[i][2][5]))
            if self.background6_label.text() == '0':
                self.button_top_week6.setEnabled(False)
            self.background6_label.setFixedSize(QSize(90, 45))
            self.background6_label.setAlignment(Qt.AlignCenter)
            self.background_labels_wk6.append(self.background6_label)
            self.week6_layout.addWidget(self.button_background_week_6)
            self.week6_layout.addWidget(self.background6_label)
            self.button_top_week6.clicked.connect(self.week6_mover)
            self.buttons_week6.append(self.button_top_week6)
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            self.week6_layout.addWidget(line)
        self.background6.setFrameStyle(QFrame.Box | QFrame.Plain)
        #self.week6_layout.setContentsMargins(0, 0, 0, 0)

        #self.button = QPushButton('Current Week', self)
        #self.button.setText('Go To Current Week')
        #self.button.clicked.connect(self.current_week_button)

        #Pyside grid set up
        self.main_background = QWidget()
        self.scroll_background = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_background)
        palette = self.main_background.palette()
        palette.setColor(QPalette.Window, '#deecfb')
        self.main_background.setPalette(palette)
        self.main_layout = QGridLayout(self.main_background)
        self.main_layout.setColumnStretch(0, 2)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.scroll_background)
        self.scroll.setWidgetResizable(True)
        self.setCentralWidget(self.main_background)

        self.scroll_layout.addWidget(self.product_background)
        self.scroll_layout.addWidget(self.background1)
        self.scroll_layout.addWidget(self.background2)
        self.scroll_layout.addWidget(self.background3)
        self.scroll_layout.addWidget(self.background4)
        self.scroll_layout.addWidget(self.background5)
        self.scroll_layout.addWidget(self.background6)

        list_layout = QVBoxLayout()
        list_layout.addWidget(title_frame)
        
        #self.main_layout.addWidget(title_frame, 0, 0, 1, 2)
        #title_frame.hide()
        self.main_layout.addWidget(self.full_list, 0, 0, 6, 1)

        #self.main_layout.addWidget(self.full_list, 1, 0, 6, 1)
        self.main_layout.addWidget(self.scroll, 0, 2, 0, 29)

        #Putting together all the rows into one layout.
        '''
        self.main_layout.addWidget(title_frame, 0, 0, 1, 2)
        self.main_layout.addWidget(self.full_list, 1, 0, 6, 1)
        self.main_layout.addWidget(self.product_background, 0, 2, 1, 29)
        self.main_layout.addWidget(self.background1, 1, 2, 1, 29)
        self.main_layout.addWidget(self.background2, 2, 2, 1, 29)
        self.main_layout.addWidget(self.background3, 3, 2, 1, 29)
        self.main_layout.addWidget(self.background4, 4, 2, 1, 29)
        self.main_layout.addWidget(self.background5, 5, 2, 1, 29)
        self.main_layout.addWidget(self.background6, 6, 2, 1, 29)
        '''

        
        
        
   
    
    #button logic. This could benefit from what I learned from spinbox logic. Could make the all movers one function.
    #Allows adjusmtent of weekly item totals. 
    def week1_mover(self):
        button_index = self.sender()
        button_clicked = self.buttons_week1.index(button_index)
        label_to_int = self.background_labels_wk2[button_clicked].text()
        label_to_int = int(label_to_int) + 1
        self.background_labels_wk2[button_clicked].setText(str(label_to_int))
        subtract_label = self.background_labels_wk1[button_clicked].text()
        subtract_label = int(subtract_label)
        self.background_labels_wk1[button_clicked].setText(str(subtract_label-1))
        #
        text_holder = self.week1_label.text()
        slicer = -abs(len(str(self.week_one_total)))
        self.week_one_total -= 1
        number_holder = int(text_holder[slicer:]) - 1
        self.week1_label.setText(text_holder[:slicer] + str(number_holder))
        text_holder2 = self.week2_label.text()
        slicer2 = -abs(len(str(self.week_two_total)))
        self.week_two_total += 1
        number_holder2 = int(text_holder2[slicer2:]) + 1
        self.week2_label.setText(text_holder2[:slicer2] + str(number_holder2))
        if self.background_labels_wk1[button_clicked].text() == '0':
            self.buttons_week1[button_clicked].setEnabled(False)
        if button_clicked == 0:
            self.buttons_week2[button_clicked].setEnabled(True)
            self.buttons_week2[button_clicked+1].setEnabled(True)
        else:   
            self.buttons_week2[button_clicked*2].setEnabled(True)
            self.buttons_week2[button_clicked*2+1].setEnabled(True)
        forecast.repaint()      

    def week2_mover(self):
        button_index = self.sender()
        button_clicked = self.buttons_week2.index(button_index)
        if button_clicked == 0:
            self.buttons_week1[button_clicked].setEnabled(True)
            self.buttons_week1[button_clicked+1].setEnabled(True)
        if button_clicked %2 == 0:
            label_to_int = self.background_labels_wk1[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk1[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week1[int(button_clicked/2)].setEnabled(True)
            label_subtract = self.background_labels_wk2[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk2[int(button_clicked/2)].setText(str(label_subtract - 1))
            #
            current_week_label = self.week2_label.text()
            number_slicer = -abs(len(str(self.week_two_total)))
            self.week_two_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week2_label.setText(current_week_label[:number_slicer] + str(number_holder))
            last_week_label = self.week1_label.text()
            number_slicer_next = -abs(len(str(self.week_one_total)))
            self.week_one_total += 1
            number_holder2 = int(last_week_label[number_slicer_next:]) + 1
            self.week1_label.setText(last_week_label[:number_slicer_next] + str(number_holder2))

            if self.background_labels_wk2[int(button_clicked/2)].text() == '0':
                self.buttons_week2[button_clicked].setEnabled(False)
                self.buttons_week2[button_clicked + 1].setEnabled(False)
        else:
            button_clicked -= 1
            label_to_int = self.background_labels_wk3[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk3[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week3[button_clicked].setEnabled(True)
            self.buttons_week3[button_clicked + 1].setEnabled(True)
            label_subtract = self.background_labels_wk2[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk2[int(button_clicked/2)].setText(str(label_subtract - 1))
            #
            current_week_label = self.week2_label.text()
            number_slicer = -abs(len(str(self.week_two_total)))
            self.week_two_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week2_label.setText(current_week_label[:number_slicer] + str(number_holder))
            next_week_label = self.week3_label.text()
            number_slicer_next = -abs(len(str(self.week_three_total)))
            self.week_three_total += 1 
            number_holder2 = int(next_week_label[number_slicer_next:]) + 1
            self.week3_label.setText(next_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk2[int(button_clicked/2)].text() == '0':
                self.buttons_week2[button_clicked].setEnabled(False)
                self.buttons_week2[button_clicked + 1].setEnabled(False)
                
        forecast.update()

    def week3_mover(self):
        button_index = self.sender()
        button_clicked = self.buttons_week3.index(button_index)
        if button_clicked %2 == 0:
            label_to_int = self.background_labels_wk2[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk2[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week2[button_clicked].setEnabled(True)
            self.buttons_week2[button_clicked + 1].setEnabled(True)
            label_subtract = self.background_labels_wk3[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk3[int(button_clicked/2)].setText(str(label_subtract - 1))
            #
            current_week_label = self.week3_label.text()
            number_slicer = -abs(len(str(self.week_three_total)))
            self.week_three_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week3_label.setText(current_week_label[:number_slicer] + str(number_holder))
            last_week_label = self.week2_label.text()
            number_slicer_next = -abs(len(str(self.week_two_total)))
            self.week_two_total += 1
            number_holder2 = int(last_week_label[number_slicer_next:]) + 1
            self.week2_label.setText(last_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk3[int(button_clicked/2)].text() == '0':
                self.buttons_week3[button_clicked].setEnabled(False)
                self.buttons_week3[button_clicked + 1].setEnabled(False)
        else:
            button_clicked -= 1
            label_to_int = self.background_labels_wk4[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk4[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week4[button_clicked].setEnabled(True)
            self.buttons_week4[button_clicked + 1].setEnabled(True)
            label_subtract = self.background_labels_wk3[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk3[int(button_clicked/2)].setText(str(label_subtract - 1))
            #
            current_week_label = self.week3_label.text()
            number_slicer = -abs(len(str(self.week_three_total)))
            self.week_three_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week3_label.setText(current_week_label[:number_slicer] + str(number_holder))
            next_week_label = self.week4_label.text()
            number_slicer_next = -abs(len(str(self.week_four_total)))
            self.week_four_total += 1 
            number_holder2 = int(next_week_label[number_slicer_next:]) + 1
            self.week4_label.setText(next_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk3[int(button_clicked/2)].text() == '0':
                self.buttons_week3[button_clicked].setEnabled(False)
                self.buttons_week3[button_clicked + 1].setEnabled(False)
        forecast.update()

    def week4_mover(self):
        button_index = self.sender()
        button_clicked = self.buttons_week4.index(button_index)
        if button_clicked %2 == 0:
            label_to_int = self.background_labels_wk3[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk3[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week3[button_clicked].setEnabled(True)
            self.buttons_week3[button_clicked + 1].setEnabled(True)
            label_subtract = self.background_labels_wk4[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk4[int(button_clicked/2)].setText(str(label_subtract - 1))
            #
            current_week_label = self.week4_label.text()
            number_slicer = -abs(len(str(self.week_four_total)))
            self.week_four_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week4_label.setText(current_week_label[:number_slicer] + str(number_holder))
            last_week_label = self.week3_label.text()
            number_slicer_next = -abs(len(str(self.week_three_total)))
            self.week_three_total += 1
            number_holder2 = int(last_week_label[number_slicer_next:]) + 1
            self.week3_label.setText(last_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk4[int(button_clicked/2)].text() == '0':
                self.buttons_week4[button_clicked].setEnabled(False)
                self.buttons_week4[button_clicked + 1].setEnabled(False)
        else:
            button_clicked -= 1
            label_to_int = self.background_labels_wk5[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk5[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week5[button_clicked].setEnabled(True)
            self.buttons_week5[button_clicked + 1].setEnabled(True)
            label_subtract = self.background_labels_wk4[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk4[int(button_clicked/2)].setText(str(label_subtract - 1))
             #
            current_week_label = self.week4_label.text()
            number_slicer = -abs(len(str(self.week_four_total)))
            self.week_four_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week4_label.setText(current_week_label[:number_slicer] + str(number_holder))
            next_week_label = self.week5_label.text()
            number_slicer_next = -abs(len(str(self.week_five_total)))
            self.week_five_total += 1 
            number_holder2 = int(next_week_label[number_slicer_next:]) + 1
            self.week5_label.setText(next_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk4[int(button_clicked/2)].text() == '0':
                self.buttons_week4[button_clicked].setEnabled(False)
                self.buttons_week4[button_clicked + 1].setEnabled(False)
        forecast.update()
    
    def week5_mover(self):
        button_index = self.sender()
        button_clicked = self.buttons_week5.index(button_index)
        if button_clicked %2 == 0:
            label_to_int = self.background_labels_wk4[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk4[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week4[button_clicked].setEnabled(True)
            self.buttons_week4[button_clicked + 1].setEnabled(True)
            label_subtract = self.background_labels_wk5[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk5[int(button_clicked/2)].setText(str(label_subtract - 1))
             #
            current_week_label = self.week5_label.text()
            number_slicer = -abs(len(str(self.week_five_total)))
            self.week_five_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week5_label.setText(current_week_label[:number_slicer] + str(number_holder))
            last_week_label = self.week4_label.text()
            number_slicer_next = -abs(len(str(self.week_four_total)))
            self.week_four_total += 1
            number_holder2 = int(last_week_label[number_slicer_next:]) + 1
            self.week4_label.setText(last_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk5[int(button_clicked/2)].text() == '0':
                self.buttons_week5[button_clicked].setEnabled(False)
                self.buttons_week5[button_clicked + 1].setEnabled(False)
        else:
            button_clicked -= 1
            label_to_int = self.background_labels_wk6[int(button_clicked/2)].text()
            label_to_int = int(label_to_int)
            self.background_labels_wk6[int(button_clicked/2)].setText(str(label_to_int + 1))
            self.buttons_week6[int(button_clicked/2)].setEnabled(True)
            label_subtract = self.background_labels_wk5[int(button_clicked/2)].text()
            label_subtract = int(label_subtract)
            self.background_labels_wk5[int(button_clicked/2)].setText(str(label_subtract - 1))
            #
            current_week_label = self.week5_label.text()
            number_slicer = -abs(len(str(self.week_five_total)))
            self.week_five_total -= 1
            number_holder = int(current_week_label[number_slicer:]) - 1
            self.week5_label.setText(current_week_label[:number_slicer] + str(number_holder))
            next_week_label = self.week6_label.text()
            number_slicer_next = -abs(len(str(self.week_six_total)))
            self.week_six_total += 1 
            number_holder2 = int(next_week_label[number_slicer_next:]) + 1
            self.week6_label.setText(next_week_label[:number_slicer_next] + str(number_holder2))
            if self.background_labels_wk5[int(button_clicked/2)].text() == '0':
                self.buttons_week5[button_clicked].setEnabled(False)
                self.buttons_week5[button_clicked + 1].setEnabled(False)
        forecast.update()

    def week6_mover(self):
        button_index = self.sender()
        button_clicked = self.buttons_week6.index(button_index)
        label_to_int = self.background_labels_wk5[button_clicked].text()
        label_to_int = int(label_to_int) + 1
        self.background_labels_wk5[button_clicked].setText(str(label_to_int))
        subtract_label = self.background_labels_wk6[button_clicked].text()
        subtract_label = int(subtract_label)
        self.background_labels_wk6[button_clicked].setText(str(subtract_label-1))
         #
        current_week_label = self.week6_label.text()
        number_slicer = -abs(len(str(self.week_six_total)))
        self.week_six_total -= 1
        number_holder = int(current_week_label[number_slicer:]) - 1
        self.week6_label.setText(current_week_label[:number_slicer] + str(number_holder))
        last_week_label = self.week5_label.text()
        number_slicer_next = -abs(len(str(self.week_five_total)))
        self.week_five_total += 1
        number_holder2 = int(last_week_label[number_slicer_next:]) + 1
        self.week5_label.setText(last_week_label[:number_slicer_next] + str(number_holder2))
        if self.background_labels_wk6[button_clicked].text() == '0':
            self.buttons_week6[button_clicked].setEnabled(False)
        if button_clicked == 0:
            self.buttons_week5[button_clicked].setEnabled(True)
            self.buttons_week5[button_clicked+1].setEnabled(True)
        else:   
            self.buttons_week5[button_clicked*2].setEnabled(True)
            self.buttons_week5[button_clicked*2+1].setEnabled(True)
        forecast.update()
    


    def five_week_alert(self):
        if self.alert_list != []:
            dlg = QMessageBox(self)
            dlg.resize(800, 800)
            dlg.setWindowTitle("ALERT: High Priority Products")
            alert_string = ''
            for i in self.alert_list:
                alert_string += str(i) + '\n'
            dlg.setText(alert_string)
            dlg.exec()
    
    def two_weeks_after_built_alert(self):
        if self.alert_list != []:
            dlg = QMessageBox(self)
            dlg.resize(800, 800)
            dlg.setWindowTitle("ALERT: This product should have been build two week ago.")
            alert_string = ''
            for i in self.two_week_built_alert:
                alert_string += str(i[0]) + ' ' + str(i[1]) + '\n'
            dlg.setText(alert_string)
            dlg.exec()
    

    #Changes to current weeks build.

    def row_change(self):
        list_check = main.label_counter_list
        if self.full_list.currentRow() == 0:
            pass
        if self.full_list.currentRow() == 1:
            main.full_list_2.setCurrentRow(1)
            self.forecast_numbers = []
            for i in self.background_labels_wk1:
                    #Used for current week item totals.
                    self.forecast_numbers.append(int(i.text()))
                    #Used for history
            for i in self.background_labels_wk1, self.background_labels_wk2, self.background_labels_wk3, self.background_labels_wk4, self.background_labels_wk5, self.background_labels_wk6:
                    self.product_numers_by_week.append(i)
            
            if list_check == []:
                main.forecast_numbers_updater()
                main.product_numers_by_week_updater()
                main.row_maker()
                main.show()
                forecast.hide()
            else:
                main.forecast_numbers_updater()
                main.product_numers_by_week_updater()
                main.row_updater()
                main.update()
                main.show()
                forecast.hide()
                


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Wicker Shop Helper')
        
        self.central_widget = QWidget()
        self.product_amount = []
        self.label_counter_list = []
        self.label_max_list = []
        self.backgorund_widgets = []

        #Top labels / Day Labels
        label_product = QLabel('Product:')
        label_mon = QLabel('Mon')
        label_tue = QLabel('Tues')
        label_wed = QLabel('Wed')
        label_thur = QLabel('Thru')
        label_fri = QLabel('Fri')
        
        
        self.grid_layout = QGridLayout(self.central_widget)
        self.scroll_background = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_background)
        self.setCentralWidget(self.central_widget)
        
        #Generating all needed spinboxes to adjust orders by day
        self.spinboxes = []
        for i in range(150):
            self.spinbox = SpinBox()
            self.spinbox.setMinimum(0)
            self.spinbox.valueChanged.connect(self.row_max)
            self.spinboxes.append(self.spinbox) 
        

        self.full_list_2 = QListWidget()

        self.menu_list = [
            {
                "name": "Six Week Forecast",
                "icon": "./icon/six_week.svg"
            },
            {
                "name": "Current Week",
                "icon": "./icon/currnet_week.svg"
            },
            {
                "name": "Past Orders",
                "icon": "./icon/PastOrders.svg"
            },
        ]

        for menu in self.menu_list:
            # Set items for the side menu with icons and text
            item_new = QListWidgetItem()
            #item_new.setIcon(QIcon(menu.get("icon")))
            item_new.setText(menu.get("name"))
            self.full_list_2.addItem(item_new)
            self.full_list_2.setCurrentRow(0)

        self.full_list_2.setStyleSheet("""
            max-width: 150px;
        """)
        self.full_list_2.setCurrentRow(1)
        self.full_list_2.currentRowChanged['int'].connect(self.row_change_2)
        
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_label = QLabel("Title")
        title_icon = QLabel('.png ipsum')
        collapse_button = QPushButton('png collapse')
        title_layout.addWidget(title_label)
        title_layout.addWidget(collapse_button)
        #title_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        title_frame.setStyleSheet("""
            max-width: 150px;
        """)
      

        #self.grid_layout.addWidget(title_frame, 0, 0, 1, 1)
        #title_frame.hide()
        #self.grid_layout.addWidget(self.full_list_2, 1, 0, 30, 0)

        self.grid_layout.addWidget(self.full_list_2, 0, 0, 30, 0)
        #self.grid_layout.addWidget(self.stacked_widget, 0, 2, 2, 1)

        self.label_frame = QFrame()
        self.label_layout = QHBoxLayout(self.label_frame)
        self.label_layout.addWidget(label_product)
        self.label_layout.addWidget(label_mon)
        self.label_layout.addWidget(label_tue)
        self.label_layout.addWidget(label_wed)
        self.label_layout.addWidget(label_thur)
        self.label_layout.addWidget(label_fri)
        self.grid_layout.addWidget(self.label_frame, 0, 1, 1, 4)

        
     
    
    def row_change_2(self):
        if self.full_list_2.currentRow() == 0:
            forecast.full_list.setCurrentRow(0)
            forecast.show()
            main.hide()

 
        
    
    def row_maker(self):
            count = 0
            self.product_label_list = forecast.product_label_list
            #Initial set up of rows
            for i in range(30):
                self.background_widget = QFrame()
                self.label_counter = QLabel(self.product_label_list[i].text() + '\n' + str(0) + '/'+ str(self.forecast_numbers[i]))
                self.background_layout = QHBoxLayout(self.background_widget)
                self.label_counter_list.append(self.label_counter)
                self.background_layout.addWidget(self.label_counter)
                for i  in range(5):
                    self.background_layout.addWidget(self.spinboxes[count])
                    count += 1 
                self.background_widget.setFrameStyle(QFrame.Box | QFrame.Plain)
                self.background_layout.setContentsMargins(0, 0, 0, 0)
                self.backgorund_widgets.append(self.background_widget)
        
            row = 1
            column = 1
            #Better way of putting rows together.
            for i in self.backgorund_widgets:
                self.scroll_layout.addWidget(i)
                row += 1

   

            
            # add wrapper widget and set its layout
            scroll = QScrollArea()
            scroll.setWidget(self.scroll_background)
            scroll.setWidgetResizable(True)
            self.grid_layout.addWidget(scroll, 1, 1, 1, 4)
            #self.setCentralWidget(self.scroll_main)


            self.product_count = forecast.product_count
            for i in range(len(self.product_count)):
                if self.product_count[i][0] == 0:
                    #Color that a row is done.
                    self.backgorund_widgets[i].setStyleSheet("background-color:#2eb872;")
            

    def row_updater(self):    
        count = 0
        self.product_label_list = forecast.product_label_list
        self.forecast_numbers = forecast.forecast_numbers
        for i in range(30):
            label_updater = self.product_label_list[i].text() + '\n' + str(0) + '/'+ str(self.forecast_numbers[i])
            self.label_counter_list[count].setText(str(label_updater))
            count += 1
        
    def spinbox_connect(self):
        #Makes nested list for how much product each day needs to be built
        spinbox_count = 0
        day = 0
        list_count = 0
        for i in self.build_list:
            self.product_amount.append([])
            while day < 5:
                self.build_list[i][1].append(day)
                day_product = self.spinboxes[spinbox_count]
                self.product_amount[list_count].append(int(day_product.value()))
                day += 1
                spinbox_count += 1
            day = 0
            list_count += 1
        
    #Logic to make keep spinbox buttons in proper range.
    def row_max(self):
        self.forecast_numbers = forecast.forecast_numbers
        self.product_label_list = forecast.product_label_list
        self.product = self.sender()
        spin_group = self.spinboxes.index(self.product)
        spin_start = spin_group % 5
        spin_start = spin_group - spin_start
        spin_end = spin_start + 6
        group = self.spinboxes[spin_start:spin_end]
        total = 0
        for i in group:
            total += i.value()
        build_item = int(spin_start / 5)
        build_total = self.forecast_numbers[build_item]
        text_holder = self.product_label_list[build_item].text() + '\n' + str(total) + '/'+ str(build_total)
        self.label_counter_list[build_item].setText(text_holder)
        #print('spin group range:'+str(spin_start) + '-' + str(spin_end), 'build item #' + str(build_item), 'Total items: ' + str(build_total), 'current total: ' + str(total))
        #Color change to indicate all items have been put in.
        if total > build_total:
            self.product.setValue(self.product.value()-1)
        if total == build_total:
            self.backgorund_widgets[build_item].setStyleSheet("background-color:#2eb872;")
        if total < build_total:
            self.backgorund_widgets[build_item].setStyleSheet("background-color:;")
    
    #Saves how items were distributed into a json folder.
    def six_week_memory(self):
        product_place = 0
        id_count = 0
        self.build_list = forecast.build_list
        for i in self.build_list:
            week_increment = 0
            for s in self.product_numers_by_week:
                product_count = int(s[product_place].text())
                total = 0
                if product_count == 0:
                    week_increment += 1
                    continue
                while total < product_count:
                    #print('Week Increment: ' + str(week_increment))
                    id_holder = self.build_list[i][3][0][0]
                    #print('Products in order: ' + str(self.item_ids[id_holder]))
                    self.item_ids = forecast.item_ids
                    original_week = self.item_ids[id_holder][i][0][0]
                    if isinstance(original_week, str):
                        week_added = datetime.strptime(original_week, '%m/%d/%y')
                    else:
                        week_added = original_week
                    week_added += timedelta(weeks=week_increment)
                    week_added = datetime.strftime(week_added, '%m/%d/%y')
                    quantity = self.item_ids[id_holder][i][id_count][1]
                    if total + quantity > product_count:
                        #print(str(id_holder) + ': splitting an order')
                        difference = product_count - total
                        total += difference
                        new_quantity = quantity - difference
                        self.build_list[i][3].insert(1, [id_holder, week_added])
                        self.item_ids[id_holder][i].pop(0)
                        self.item_ids[id_holder][i].append([week_added, difference])
                        self.item_ids[id_holder][i].insert(0, [original_week, new_quantity])
                        self.build_list[i][3].pop(0)
                    else:
                        #print(str(id_holder) + ': order week adjusted by ' + str(quantity))
                        self.item_ids[id_holder][i].pop(0)
                        self.item_ids[id_holder][i].append([week_added, quantity])
                        total += quantity
                        self.build_list[i][3].pop(0)
                week_increment += 1
            product_place += 1  


    def google_update(self):
        total_counter = 0
        #plugging build_list into spreadsheet
        #have to excel_plug_location[find] - 29 to iput build_list into proper location.
        self.sheet = forecast.sheet
        start  = len(self.sheet.get_all_values()) + 1
        #First item on the list. Used to find date.
        date_check = self.sheet.findall("elliott")
        date_check = date_check[-1].row - 1
        data = self.sheet.get(str(date_check)+':'+str(date_check+30))
        spreadsheet_month = self.sheet.cell(date_check, 1).value
        spreadsheet_monday = self.sheet.cell(date_check, 2).value
        self.month_name = forecast.month_name
        self.monday = forecast.monday
        #Checking if date on sheet is same as this monday, if not it makes a new week.
        if spreadsheet_month + spreadsheet_monday != self.month_name + self.monday:
            data[0][0] = self.month_name
            counter = 1
            monday = int(self.monday)
            while counter < 6:
                data[0][counter] = str(monday)
                monday += 1
                counter += 1
            self.sheet.batch_update([{
                        'range' : str(start)+':'+str(start+30),
                        'values': data
                            }])
            date_check = start
        label_holder = ['elliott','Irving Doors',',Speaker Stand','Irving Tallboy','Tallboy','Zenith','Deluxe Tallboy','Hamilton','Irving','Turntablle sta.','Halfstack','Deluxe','End Table','Deluxe Jr','Milk Crate','Cube','7-Inch','Hawthorne','Clinton','BN DTB','BN CS','BN Cube','BN WH','BN something','Wall Hanger','Record Display','Wire Divider', 'Record Divider', 'wood leg set', 'stain']
        function_holder = []
        #Making row logic to add a total to final row.
        for i in range(1,31):
            function_holder.append(['=SUM(B'+str(date_check+i)+':''F'+str(date_check+i)+')'])
        for i in range(len(function_holder)):
            self.product_amount[i].insert(0, label_holder[i])
            self.product_amount[i].append(function_holder[i][0])
        #Data is stored in self.product_amount. Batch update is made at the right row/columnn size.
        self.sheet.batch_update([{
                    'range' : 'A'+str(date_check+1)+':''G'+str(date_check+30),
                    'values': self.product_amount,
                        }], value_input_option=gspread.utils.ValueInputOption.user_entered)
        #Color format to organize work departments.
        self.sheet.format('A' + str(date_check+1) + ':' + 'G' + str(date_check+8), { 'backgroundColor': {
                'red':0.24705882352941178,
                'green':0.7725490196078432,
                'blue':0.9411764705882353}})
        self.sheet.format('A' + str(date_check+9)+':'+ 'G' +str(date_check+19), { 'backgroundColor': {
                'red':0.42745098039215684,
                'green':0.9254901960784314,
                'blue':0.7254901960784313}})
        self.sheet.format('A' + str(date_check+25)+':'+ 'G' + str(date_check+28), { 'backgroundColor': {
                'red':0.9333333333333333,
                'green':0.9607843137254902,
                'blue':0.6980392156862745}})
        
    def forecast_numbers_updater(self):
        self.forecast_numbers = forecast.forecast_numbers

    def product_numers_by_week_updater(self):
        self.product_numers_by_week = forecast.product_numers_by_week
    
    #not used.
    def key_to_json(self, data):
        if data is None or isinstance(data, (bool, int, str)):
            return data
        if isinstance(data, (tuple, frozenset)):
            return str(data)
        
    #not used
    def to_json(self, data):
        if data is None or isinstance(data, (bool, int, tuple, range, str, list)):
            return data
        if isinstance(data, (set, frozenset)):
            return sorted(data)
        if isinstance(data, dict):
            return {self.key_to_json(key): self.to_json(data[key]) for key in data}
        


    def submit(self):
        self.six_week_memory()
        self.history_path = forecast.history_path
        with open(self.history_path, "w+") as f:
            json.dump(self.item_ids, f, cls=NpEncoder)
        self.spinbox_connect()
        self.google_update()
        main.close()





app = QApplication(sys.argv)

forecast = Forecast()

with open("C:\Coding\WickerShops\StyleSheet.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

forecast.resize(800, 600)
forecast.five_week_alert()
main = Main()
main.resize(800, 600)


forecast.show()


app.exec()
        