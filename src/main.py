'''
Project : Noz'Num
Description : A simple interactive application to display a map with a marker and graphs with the data from a tcx file

Author : Lucas BRAND
'''
import sys
import os
import folium
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from xml.etree import ElementTree as ET
import time
from datetime import timedelta
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
import mplcursors


##~##~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ TXC TO DF ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

# Convert datetime from txc file into seconds
def TimeToSeconds(t):
    t_txt = t.text[11:19]
    t_strip = time.strptime(t_txt.split(',')[0],'%H:%M:%S')
    t_sec = timedelta(hours=t_strip.tm_hour,minutes=t_strip.tm_min,seconds=t_strip.tm_sec).total_seconds()
    return t_sec

def TimeToHour(t):
    t_txt = t.text[11:19]
    return t_txt
    #print('T_TXT : ', t_txt)

# Generate a csv file from tcx
def tcx_to_df(tcx_file_path):
    csv_line = []
    all_items = []
    tree = ET.parse(tcx_file_path)
    root = tree.getroot()
    trackTree = root[0][0][1][5] # Track is located at : root[0][0][1][5]

    # On crée un namespace car le liens dans xmlns nous dérange
    ns = {'TrainingCenterDatabase': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
    for trackpoint in trackTree.findall('TrainingCenterDatabase:Trackpoint', ns):
        if(trackpoint):
            time = trackpoint.find('TrainingCenterDatabase:Time', ns)
            time_hours = TimeToHour(time)
            time_seconds = TimeToSeconds(time) # Pour transformer un temps du type "hh,mm,ss" en secondes
            position = trackpoint.find('TrainingCenterDatabase:Position', ns)
            latitude = position.find('TrainingCenterDatabase:LatitudeDegrees', ns)
            longitude = position.find('TrainingCenterDatabase:LongitudeDegrees', ns)
            altitude = trackpoint.find('TrainingCenterDatabase:AltitudeMeters', ns)
            distance = trackpoint.find('TrainingCenterDatabase:DistanceMeters', ns)
            hr = trackpoint.find('TrainingCenterDatabase:HeartRateBpm', ns)
            hr_val = hr.find('TrainingCenterDatabase:Value', ns)
            csv_line = [time.text, time_hours, time_seconds , latitude.text, longitude.text, altitude.text, distance.text, hr_val.text]
            all_items.append(csv_line)
    df = pd.DataFrame(all_items, columns=[
        'time','time_in_hours','time_in_seconds','latitude','longitude','altitude', 'distance', 'heart_rate'],
        dtype=float)
    return df


##~##~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ GENERATE MAP ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

# Generate a folium map with a specific marker
def GenerateMap(data_object, zoom_level=13):
    # Update the folium map with new data or changes
    if not (data_object.df.empty):
        map = folium.Map(location=data_object.map_center, zoom_start=zoom_level, tiles=None)
        folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(map)
        folium.PolyLine(data_object.points, color='red', weight=5, opacity=0.7).add_to(map)
        folium.Marker(location=data_object.marker_coord).add_to(map)
        return map
    else:
        pass

def AxesNames(data, ax):
    if not (data.df.empty):
        axes_dict = {
            'lat' : data.lat,
            'lon' : data.lon,
            'hr' : data.hr,
            'alt' : data.alt,
            'dt' : data.dt,
            't' : data.t,
            'ts' : data.ts,
            'th' : data.th
        }
        return axes_dict.get(ax, "No info available")
    else:
        return 0
    


##~##~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ DATA CLASS ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

class Data():
    def __init__(self, df):
        super().__init__()
        self.df = df
        if not (self.df.empty):
            self.t = self.df['time'] # full date time
            self.th = self.df['time_in_hours']
            self.ts = self.df['time_in_seconds']
            self.lat = self.df['latitude']
            self.lon = self.df['longitude']
            self.alt = self.df['altitude']
            self.hr = self.df['heart_rate']
            self.dist = self.df['distance']
            self.dt = self.ts - self.ts[0] # time in seconds that starts at 0 second
            self.start_loc = [self.lat.iloc[0], self.lon.iloc[0]]
            self.end_loc = [self.lat.iloc[-1], self.lon.iloc[-1]]
            self.marker_coord = self.start_loc
            self.points = []

            # Calculate the center of the map (according to the route)
            self.lon_min, self.lon_max = self.lon.min(), self.lon.max()
            self.lat_min, self.lat_max = self.lat.min(), self.lat.max()
            self.map_center = [((self.lat_min+self.lat_max)/2), ((self.lon_min+self.lon_max)/2)]
            
            # Put all data longitude and latitude in a "points" array
            for i in range(self.lat.size):
                a = (self.lat[i], self.lon[i])
                self.points.append(a)


##~##~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ MAP CLASS ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

class MapWidget(QWebEngineView):
    def __init__(self, data=None, zoom_level=13):
        super().__init__()
        self.data = data # Data class
        if not (self.data.df.empty):
            map = GenerateMap(self.data, zoom_level=zoom_level)
            map_html = map.get_root().render()
            self.setHtml(map_html)

    def update_map(self, new_data, zoom_level):
        if not (new_data.df.empty):
            map = GenerateMap(self.data,zoom_level)
            # Add the map to the web view widget
            map_html = map.get_root().render()
            self.setHtml(map_html)
            self.data = new_data


##~##~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ PLOT CLASS ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100, map_instance=None, zoom_slider_instance=None, data=None, x='lon',y='lat', x_label='Longitude (degrees °)', y_label='Latitude (degrees °)', line_color='-ro', last_clicks_array=None, waiting_for_clicks=False, file_name=None, confirm_fct=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.map_instance = map_instance
        self.zoom_slider_instance = zoom_slider_instance
        self.data = data
        self.line_color = line_color
        self.x = AxesNames(self.data, x)
        self.y = AxesNames(self.data, y)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)

        self.confirm_fct = confirm_fct
        self.file_name = file_name
        self.last_clicks_array = last_clicks_array
        self.waiting_for_clicks = waiting_for_clicks

        self.axes.plot(self.x, self.y, self.line_color, picker=5)
        #mplcursors.cursor(self.axes, hover=True)
        self.fig.canvas.mpl_connect('pick_event', self.on_click)
        self.cursor = mplcursors.cursor(self.axes, hover=True)
        self.cursor.connect('add', self.show_annotation)
        self.clickable_bool = True # Set to False to disable the clickable points

    # Hover annotation function
    def show_annotation(self, sel):
        xi = sel.target[0]
        vertical_line = self.axes.axvline(xi, color='red', ls=':', lw=1)
        sel.extras.append(vertical_line)
        y1 = np.interp(xi, self.x, self.y) # interpolate the points (maybe not necessary)
        # print('xi: ', xi) # max 2632.0
        # print('last elem : ', self.data.dt.tail(1).index[0])

        # Closest value to the clicked point (xi)
        df_closest = self.data.df.iloc[(self.data.dt-xi).abs().argsort()[:1]]
        closest_val = df_closest['time_in_seconds'].values[0]
        dt = closest_val - self.data.ts[0] 
        result_df = self.data.dt.loc[self.data.dt == dt]
        if not result_df.empty:
            closest_index = result_df.index[0]
            closest_y = self.y[closest_index]
            t_hours = self.data.th[closest_index]
            dist_from_start = round(self.data.dist[closest_index], 2)
        else:
            t_hours = self.data.th.iloc[-1]
            closest_y = self.y[closest_index]
            dist_from_start = round(self.data.dist.iloc[-2], 2)
        
        # annotation_str = f'{self.axes.get_xlabel()}: {xi}\n{self.axes.get_ylabel()}: {y1}\nTime (hours): {t_hours}' # this one is with interpolation
        # annotation_str = f'Time: {self.data.dt[xi]} seconds\nHeart rate: {self.data.hr[xi]} bpm\nAltitude: {self.data.alt[xi]} meters'
        annotation_str = f'{self.axes.get_xlabel()}: {dt}\n{self.axes.get_ylabel()}: {closest_y}\nTime (hours): {t_hours}\nDistance from start: {dist_from_start} meters'
        sel.annotation.set_text(annotation_str)

    # Function to click on a point and get its data
    def on_click(self, event):
        if self.clickable_bool:
            ind = event.ind[0]
            self.data.marker_coord = [self.data.lat[ind], self.data.lon[ind]]
            point_hr = self.data.hr[ind]
            point_alt = self.data.alt[ind]
            point_dt = self.data.dt[ind]
            print(f"Clicked on point {self.data.marker_coord}")
            print(f"Distance from start: {self.data.dist[ind]} meters")
            # print(f"Heart rate is {point_hr} bpm at time {point_dt} seconds")
            # print(f"Altitude is {point_alt} meters at time {point_dt} seconds")
            self.map_instance.update_map(self.data, zoom_level=self.zoom_slider_instance.slider.value())

            if (self.waiting_for_clicks == True):
                print("got a click")
                self.last_clicks_array.append(ind)
                if len(self.last_clicks_array) == 2:
                    print("Got two clicks")
                    self.waiting_for_clicks = False
                    print('last_clicks_array: ', self.last_clicks_array)
                    self.save_selected_points_to_csv(id_1=self.last_clicks_array[0], id_2=self.last_clicks_array[1])
                    return self.last_clicks_array
    
    # saves the data between the two selected point to a pandas dataframe then to a csv file
    def save_selected_points_to_csv(self, id_1, id_2):
        print('Saving data to csv')

        # Compute participant speed on the segmented part
        #dist = max(self.data.dist[id_1], self.data.dist[id_2]) - min(self.data.dist[id_1], self.data.dist[id_2])
        dist = abs(self.data.dist[id_1] - self.data.dist[id_2])
        print('DIST : ', dist, 'meters')
        dt = abs(self.data.dt[id_1] - self.data.dt[id_2])
        print('DT : ', dt, 'seconds')
        speed = dist / dt
        # ISSUE : The distances data are broken for some reason. A kilometer is around 47 meters according to the data...

        # Make a subdataframe with the data between the two selected points of the main dataframe 
        sub_data = self.data.df.loc[id_1:id_2] 
        df = pd.DataFrame(sub_data)
        df['label'] = self.file_name
        df['speed'] = speed
        #print("Selected Dataframe: \n", df)
        df.to_csv(self.file_name+'.csv') # Save the subdataframe to a csv file
        self.confirm_fct(text=self.file_name) # Call the confirm function to update the main dataframe

                    

##~##~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ SLIDER CLASS ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

class SliderWidget(QWidget):
    def __init__(self, map_instance=None, data=None):
        super().__init__()
        self.data = data
        self.map_instance = map_instance
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(3)
        self.slider.setMaximum(18)
        self.slider.setValue(13)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.valuechange)
        self.zoom_label = QLabel('Zoom')
        self.max_label = QLabel('18')
        self.min_label = QLabel('3')
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.zoom_label)
        self.vbox.addWidget(self.max_label)
        self.vbox.addWidget(self.slider)
        self.vbox.addWidget(self.min_label)
        self.label = QLabel('13')
        self.hbox = QHBoxLayout()
        self.hbox.addLayout(self.vbox)
        self.hbox.addWidget(self.label)
        self.setLayout(self.hbox)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
    
    def valuechange(self):
        size = self.slider.value()
        self.label.setText(str(size))
        self.map_instance.update_map(self.data, size)


##~##~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ MAIN WINDOW CLASS ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.next_data_label = None
        self.last_clicks_array = []
        self.waiting_for_clicks = False

    def initUI(self):
        self.setWindowTitle('Noz-Num Interactive Map')
        self.window_width, self.window_height = 1280, 720
        self.setMinimumSize(self.window_width, self.window_height)
        # self.showMaximized()

        # central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.lay_main = QVBoxLayout(self.central_widget)
        self.lay_map = QHBoxLayout()
        self.lay_plots = QVBoxLayout()
        
        # Add plots layer to the main layer
        self.lay_main.addLayout(self.lay_map)
        self.lay_main.addLayout(self.lay_plots)
   
        # TCX Load button
        load_button_action = QAction("&Load data from .tcx", self)
        load_button_action.setShortcut("Ctrl+O")
        load_button_action.setStatusTip('Load data from a .tcx file [Ctrl+O]')
        load_button_action.triggered.connect(self.dialog)

        # Main Menu
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('&Load Data')
        file_menu.addAction(load_button_action)

    # Opens a popup window
    def open_popup(self):
        popup = QDialog(self)
        popup.setWindowTitle("Enter Data Label")
        popup.setGeometry(200, 200, 400, 100)
        layout = QVBoxLayout()

        x = self.geometry().center().x() - popup.geometry().center().x()
        y = self.geometry().center().y() - popup.geometry().center().y()
        popup.move(x,y)

        # Add a line edit widget for text input
        self.lineEdit = QLineEdit(popup)
        self.lineEdit.setGeometry(10, 10, 380, 30)
        self.lineEdit.setGeometry(0, 0, 380, 30)
        self.lineEdit.setPlaceholderText("Enter Data Label")

        # Add a confirm button to close the popup and return the text
        confirmButton = QPushButton("Confirm", popup)
        confirmButton.setGeometry(10, 50, 200, 30)
        confirmButton.clicked.connect(lambda: self.on_confirm(popup))
        confirmButton.clicked.connect(lambda: self.wait_for_two_clicks(self.next_data_label))
        
        layout.addWidget(self.lineEdit)
        layout.addWidget(confirmButton)
        layout.setAlignment(Qt.AlignCenter)
        popup.exec_()

    # Confirm button callback function
    def on_confirm(self, popup):
        # Get the input text from the line edit widget
        self.next_data_label = self.lineEdit.text()
        print("Input Text:", self.next_data_label) # Print the input text to the terminal
        popup.close() # Close the popup window
        return self.next_data_label
    
    # Popup after saving data from selected points
    def save_confirm(self, text):
        popup = QDialog(self)
        popup.setWindowTitle("Data saved successfully")
        popup.setGeometry(200, 200, 400, 100)

        layout = QVBoxLayout()
        
        current_file = os.path.abspath(sys.argv[0])
        current_dir = os.path.dirname(current_file)

        fulltext = "Data saved successfully to " + current_dir + "\ " + text + ".csv."
        label = QLabel(fulltext, popup)
        label.setWordWrap(True)

        label_width = label.sizeHint().width()
        label_height = label.sizeHint().height()
        max_width = self.frameGeometry().width() - 10
        if label_width > max_width:
            label_width = max_width
        
        popup.resize(label_width + 20, label_height + 100)

        # Center the popup window
        x = self.geometry().center().x() - popup.geometry().center().x()
        y = self.geometry().center().y() - popup.geometry().center().y()
        popup.move(x,y)

        # Add a confirm button to close the popup
        confirmButton = QPushButton("Confirm", popup)
        confirmButton.setGeometry(0, 0, 200, 30)
        confirmButton.move(label.x(), label.height() + 20)
        confirmButton.setParent(popup)

        # Confirm button callback function
        confirmButton.clicked.connect(lambda: popup.close())

        layout.addWidget(label)
        layout.addWidget(confirmButton)
        layout.setAlignment(Qt.AlignCenter)
        popup.setLayout(layout)
        popup.exec_()

    
    # Open a dialog to load .tcx data file
    def dialog(self): # technically updates Data class
        tcx_file_path , check = QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()",
                                                "", "All Files (*);;Python Files (*.py);;Text Files (*.txt)")
        if check:
            df = tcx_to_df(tcx_file_path)
            self.load_data(data_frame = df, layout_map=self.lay_map, layout_plot=self.lay_plots)
            # print(df)

    # Remove old widgets, load new data and create new map and plots widgets
    def load_data(self, data_frame, layout_map, layout_plot):
        self.remove_widgets_from_layout(layout=layout_map)
        self.remove_widgets_from_layout(layout=layout_plot)
        self.data = Data(df=data_frame)
        self.create_map_from_data(data=self.data, layout=layout_map)
        self.plot_data(data=self.data, layout=layout_plot, web_view=self.web_view, zoom_slider=self.zoom_slider)

    # Generate a MapWidget object called web_view and add it to its layout
    def create_map_from_data(self, data, layout, zoom_level=13):
        self.web_view = MapWidget(data, zoom_level=zoom_level)
        self.zoom_slider = SliderWidget(map_instance=self.web_view, data=data)
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zoom_slider.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(self.web_view) # main layout
        layout.addWidget(self.zoom_slider) # main layout
        return self.web_view, self.zoom_slider
    
    # Generate two plots objects and add them to their layout
    def plot_data(self, data, layout, web_view, zoom_slider):
        self.plot_hr = MplCanvas(self, width=5, height=4, dpi=100, map_instance=web_view, data=data, zoom_slider_instance=zoom_slider, x='dt', y='hr', x_label='Time (seconds)', y_label='Heart Rate (bpm)',
                                  line_color='-ro', last_clicks_array=self.last_clicks_array, waiting_for_clicks=self.waiting_for_clicks, file_name=self.next_data_label, confirm_fct=self.save_confirm)
        self.plot_alt = MplCanvas(self, width=5, height=4, dpi=100, map_instance=web_view, data=data, zoom_slider_instance=zoom_slider, x='dt', y='alt', x_label='Time (seconds)', y_label='Altitude (meters)',
                                   line_color='-bo', last_clicks_array=self.last_clicks_array, waiting_for_clicks=self.waiting_for_clicks, file_name=self.next_data_label, confirm_fct=self.save_confirm)
        
        self.select_data_button = QPushButton('Select Data From Plot')
        self.select_data_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.select_data_button.clicked.connect(self.open_popup)

        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.plot_hr)
        sub_layout.addWidget(self.plot_alt)
        layout.addLayout(sub_layout)
        layout.addWidget(self.select_data_button)

        return self.plot_hr, self.plot_alt
    
    # Wait for two clicks on the plots
    def wait_for_two_clicks(self, file_name):
        print('waiting for two clicks')
        self.last_clicks_array = []
        self.waiting_for_clicks = True
        self.plot_alt.waiting_for_clicks = True
        self.plot_hr.waiting_for_clicks = True
        self.plot_hr.file_name = file_name
        self.plot_alt.file_name = file_name
        self.plot_hr.last_clicks_array = self.last_clicks_array
        self.plot_alt.last_clicks_array = self.last_clicks_array


    # Removes widgets from a layout. Used to clear old widgets when we load new data
    def remove_widgets_from_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    # rajouter heure + distance sur courbe
    # calculer vitesse moyenne et vitesse entre deux points pour comparer
    # text 250 mots sur le dev de l'app
    # Mercredi envoyer la version mac+win
    
    

            
##~##~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
#~##~~ MAIN FUNCTION ~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##
##~##~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##~~~~~~~~~~~~~~~~~~~~~~~~~~##~##

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()