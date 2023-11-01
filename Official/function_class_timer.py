import time
import os
import math
import multiprocessing
import subprocess
import gphoto2 as gp 
import exiftool
from pymavlink import mavutil
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
from array import array

class CLASS:
    def __init__(self):
        """
        Initializes the CLASS object.

        This method initializes the class and establishes connections to UAS and the camera.

        :return: None
        """
        #connecting to UAS with dronekit
        print("Connecting to UAS")
        self.connection_string = "/dev/ttyACM0" #usb to micro usb
        self.UAS_dk = connect(self.connection_string, baud=57600, wait_ready=True)
        print("Connected with DroneKit")

        #connecting to mavlink
        print('Connecting MavLink')
        self.UAS_mav = mavutil.mavlink_connection('/dev/ttyACM0', baud=57600)
        print('Connecting to mavlink')

        #connect the camera
        #self.subprocess.run('"gphoto2", "--auto-connect"')
        camera = gp.Camera()
        camera.init
        print('Camera Connected')
        
        print('CREATING IMAGE DIRECTORY')
        image_dir = f'image_{time.ctime(time.time())}'
        print(f'MADE DIRECTORY {image_dir}')
        os.mkdir(image_dir)
        os.chdir(str(image_dir))
        print(f'MOVED TO {image_dir} DIRECTORY')
        print("CREATING TEST DATA FILE")
        with open('Data_log.txt', "a") as file:
                file.write("Time Log:\n")
        
        # writing file variable
        self.attitude_time = []
        self.deliver_payload_time = []
        self.geotag_time = []
        self.haversine_time = []
        self.search_area_waypoint_time = []
        self.subprocess_execute_time = []
        self.trigger_camera_time = []
        self.waypoint_lap_time = []

        #declaring initial variable
        self.pitch = 0
        self.roll = 0
        self.yaw = 0
        self.lat = 0
        self.lon = 0
        self.alt = 0
        self.image_number = 1
        self.drone_sensory = [self.pitch, self.roll, self.yaw, self.lat, self.lon, self.alt]
        self.currWP_index = 0
        self.lap = 0
        self.filename = f"image"
        self.waypoint_lap_latitude = []
        self.waypoint_lap_longitude = []

        #predefined search area value
        self.search_area_latitude = [
            38.31455510, 38.31453830, 38.31452150, 38.31455510, 38.31453830, 38.31452150,
            38.31450570, 38.31448990, 38.31447520, 38.31445830, 38.31444260, 38.31442890,
            38.31441410, 38.31439630, 38.31438150, 38.31437100, 38.31435840, 38.31425310,
            38.31426740, 38.31428050, 38.31429730, 38.31431400, 38.31432680, 38.31434370,
            38.31436050, 38.31437420, 38.31439070, 38.31440710, 38.31442050, 38.31443710
        ]

        self.search_area_longitude = [
            -76.54514240, -76.54504980, -76.54496000, -76.54514240, -76.54504980, -76.54496000,
            -76.54486750, -76.54478030, -76.54469040, -76.54460060, -76.54451210, -76.54441950,
            -76.54432700, -76.54424120, -76.54415400, -76.54406280, -76.54396620, -76.54399840,
            -76.54408890, -76.54418350, -76.54427170, -76.54435990, -76.54445170, -76.54454130,
            -76.54463080, -76.54472400, -76.54481290, -76.54490170, -76.54499350, -76.54508310
        ]

        self.user_waypoint_input()
        while True:
            try:
                response = int(input("\nIS THE VALUE OF LATITUDE AND LONGITUDE CORRECT?\n1-YES or 2-NO\n"))
                if response in [1, 2]:
                    if (response ==2):
                        self.user_waypoint_input()
                    else:
                        break
                else:
                    raise ValueError("\nInvalid response. Please enter 1-YES or 2-NO.")

            except ValueError as e:
                print(e)

    def trigger_camera(self, image_name):
        """
        Trigger the camera to capture an image.

        This method triggers the camera to capture an image and saves it with the provided filename.

        :param filename: The filename to use for the captured image.
        :return: None
        """
        start = time.time()
        print(f'image{self.image_number} IS BEING TAKEN')
        cmd = ('gphoto2', '--capture-image-and-download', '--filename', f'image{self.image_number}')
        self.subprocess_execute(cmd)
        print("#####################",image_name, "###########################")
        print(f'Image{self.image_number} Captured \n')
        end = time.time()
        difference = end - start
        self.trigger_camera_time.append(difference)

    def attitude(self):
        """
        Retrieve attitude and GPS information.

        This method retrieves the attitude (pitch, roll, yaw) and GPS information (latitude, longitude, altitude)
        from the UAS and updates the class variables accordingly.

        :return: None
        """
        start = time.time()
        # Setting the variable with gps coordinates, yaw pitch and roll
        attitude = self.UAS_dk.attitude
        attitude = str(attitude)
        # Getting the UAS location in long and lat
        gps = self.UAS_dk.location.global_relative_frame
        gps = str(gps)
        # using split method to split string so we can get individual value of yaw, pitch, and roll
        attitude_split = attitude.split(",")
        pitch_split = attitude_split[0].split("=")
        # The pitch value
        self.pitch = pitch_split[1]
        yaw_split = attitude_split[1].split("=")
        # yaw value
        self.yaw = yaw_split[1]
        roll_split = attitude_split[2].split("=")
        # roll value
        self.roll = roll_split[1]
        # splitting the string so we can get the value of longitude and latitude
        gps_split = gps.split(",")
        lat_split = gps_split[0].split("=")
        # value of the lat
        self.lat = lat_split[1]
        lon_split = gps_split[1].split("=")
        # value of the long
        self.lon = lon_split[1]
        alt_split = gps_split[2].split("=")
        # altitude value
        self.alt = alt_split[1]
        # Send inputs as a string not int
        self.pitch = str(self.pitch)
        self.roll = str(self.roll)
        self.yaw = str(self.yaw)
        self.lat = str(self.lat)
        self.lon = str(self.lon)
        self.alt = str(self.alt)
        self.drone_sensory = [self.pitch, self.roll, self.yaw, self.lat, self.lon, self.alt]
        end = time.time()
        difference = end - start
        self.attitude_time.append(difference)


        return print("Drone Sensory Data Collected")
    
    def subprocess_execute(self, command):
        """
        Execute a subprocess command with the provided arguments and record the execution time.

        Args:
            command (str): The subprocess command to execute.

        Returns:
            None
        """
        start = time.time()
        subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        end = time.time()
        difference = end - start
        self.subprocess_execute_time.append(difference)
          
    def geotag(self, image_name):
        """
        Geotag an image with sensory data.

        This method geotags a photo with attitude (pitch, roll, yaw) and GPS (latitude, longitude, altitude)
        information.

        :param filename: The filename of the image to geotag.
        :param drone_sensory: The drone sensory data.
        :return: None
        """
        start = time.time()
        # Geotagging photo with the attitude and GPS coordinate
        pyr = ('pitch:' + str(self.drone_sensory[0]) + ' yaw:' + str(self.drone_sensory[2]) + ' roll:' + str(self.drone_sensory[1]))
        print(pyr)
        tag_pyr_command = ('exiftool', '-comment=' + str(pyr), image_name)
        tag_lat_command = ('exiftool', '-exif:gpslatitude=' + '\'' + str(self.drone_sensory[3]) + '\'', image_name)
        tag_long_command = ('exiftool', '-exif:gpslongitude=' + '\'' + str(self.drone_sensory[4]) + '\'', image_name)
        tag_alt_command = ('exiftool', '-exif:gpsAltitude=' + '\'' + str(self.drone_sensory[5]) + '\'', image_name)
        self.image_number += 1
        #executing the tag command in ssh
        # subprocess.run(tag_pyr_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # subprocess.run(tag_lat_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # subprocess.run(tag_long_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # subprocess.run(tag_alt_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                

        p1 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_pyr_command,))
        p2 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_lat_command,))
        p3 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_long_command,))
        p4 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_alt_command,))
        

        p1.start()
        p2.start()
        p3.start()
        p4.start()
        
        p1.join()
        p2.join()
        p3.join()
        p4.join()

        
        end = time.time()
        difference = end - start

        self.geotag_time.append(difference)
        return print(f"{self.filename + str(self.image_number-1)} geotagged")

    def toRadian(self, degree):
        """
        Convert from degree to radian.

        Args:
            degree (float): The angle in degrees to be converted to radians.

        Returns:
            float: The equivalent angle in radians.
        """
        pi = math.pi
        return degree * (pi / 180)

    def haversine(self, lon1, lat1):
        """
        Use the Haversine formula to calculate the distance between two coordinates.

        Args:
            lon1 (float): Longitude of the first coordinate.
            lat1 (float): Latitude of the first coordinate.

        Returns:
            float: The distance between the two coordinates in meters.
        """
        start = time.time()
        curr_location = self.UAS_dk.location.global_relative_frame
        lat1 = self.toRadian(lat1)
        lon1 = self.toRadian(lon1)
        lat2 = self.toRadian(curr_location.latitude)
        lon2 = self.toRadian(curr_location.longitude)

        end = time.time()
        difference = end - start

        self.haversine_time.append(difference)
        # feet conversion * earth radius * something
        return 5280 * 3963.0 * math.acos( (math.sin(lat1)*math.sin(lat2)) + (math.cos(lat1) * math.cos(lat2)) * math.cos(lon2 - lon1) )

    def RTL_stat( self ):
        """
        Check if the UAS is in "Return to Launch" mode.

        Returns:
            bool: True if the UAS is in RTL mode, False otherwise.
        """
        return self.UAS_dk.mode == VehicleMode("RTL")

    def spline_command(self, latitude, longitude):
        """
        Define a spline command (not implemented).

        Args:
            latitude (float): The latitude coordinate.
            longitude (float): The longitude coordinate.

        Returns:
            None
        """
        # Create a waypoint command
        command = mavutil.mavlink.MAV_CMD_NAV_SPLINE_WAYPOINT


        #parameter for waypoint
        LONG_SEND_WAYPOINT_parameter = [
            UAS_mav.target_system,  #target_system
            UAS_mav.target_component, #target_component
            command, #MAV_CMD_NAV_WAYPOINT (16) or try to change it to  waypoint_command
            0, #confirmation 
            0, #hold (s)
            0, #empty
            0, #empty
            0, #empty
            latitude,  
            longitude,  
            self.alt
            ]  

        UAS_mav.mav.command_long_send(LONG_SEND_WAYPOINT_parameter)
        msg = UAS_mav.recv_msg(type = 'COMMAND_ACK', blocking = True)
        return print(msg)

    def waypoint_command(self, latitude, longitude):
        """
        Define a waypoint command (not implemented).

        Args:
            latitude (float): The latitude coordinate.
            longitude (float): The longitude coordinate.

        Returns:
            None
        """
        # Create a waypoint command
        command = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT


        #parameter for waypoint
        LONG_SEND_WAYPOINT_parameter = [
            UAS_mav.target_system,  #target_system
            UAS_mav.target_component, #target_component
            command, #MAV_CMD_NAV_WAYPOINT (16) or try to change it to  waypoint_command
            0, #confirmation 
            0, #hold (s)
            10, #Accept radius (m)
            0, #pass radius (m)
            0, #yaw (deg)
            latitude,  
            longitude,  
            self.alt
            ]  

        UAS_mav.mav.command_long_send(LONG_SEND_WAYPOINT_parameter)
        msg = UAS_mav.recv_msg(type = 'COMMAND_ACK', blocking = True)
        return print(msg)

    def distance_command(self, latitude, longitude):
        """
        Define a distance command (not implemented).

        Args:
            latitude (float): The latitude coordinate.
            longitude (float): The longitude coordinate.

        Returns:
            None
        """
        # Create a waypoint command
        command = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT


        #parameter for waypoint
        LONG_SEND_WAYPOINT_parameter = [
            UAS_mav.target_system,  #target_system
            UAS_mav.target_component, #target_component
            command, #MAV_CMD_NAV_WAYPOINT (16) or try to change it to  waypoint_command
            0, #confirmation 
            0, #hold (s)
            10, #Accept radius (m)
            0, #pass radius (m)
            0, #yaw (deg)
            latitude,  
            longitude,  
            self.alt
            ]  

        UAS_mav.mav.command_long_send(LONG_SEND_WAYPOINT_parameter)
        msg = UAS_mav.recv_msg(type = 'COMMAND_ACK', blocking = True)
        return print(msg)
    
    def servo_command(self, servo_x):
        """
        Activate a servo to deliver payload (not implemented).

        Args:
            servo_x (int): The servo number to be activated.

        Returns:
            None
        """
        # Create a waypoint command
        command = mavutil.mavlink.MAV_CMD_DO_SET_SERVO


        #parameter for waypoint
        LONG_SEND_WAYPOINT_parameter = [
            UAS_mav.target_system,  #target_system
            UAS_mav.target_component, #target_component
            command, #action command
            0, #confirmation 
            servo_x, #servo motor number
            1000, #pulse width modulation (PWM)
            0, #empty
            0, #empty
            0, #empty  
            0, #empty  
            0 #empty
            ]  

        UAS_mav.mav.command_long_send(LONG_SEND_WAYPOINT_parameter)
        msg = UAS_mav.recv_msg(type = 'COMMAND_ACK', blocking = True)
        return print(msg)

    
    def waypoint_reached (self, latitude_deg, longitude_deg ):
        """
        Check if the UAS has reached a specified waypoint.

        Args:
            latitude_deg (float): The latitude coordinate of the waypoint.
            longitude_deg (float): The longitude coordinate of the waypoint.

        Returns:
            bool: True if the waypoint is reached, False otherwise.
        """
        #distance between 2 points retuirn value in feet    
        distance = self.haversine(latitude_deg,longitude_deg )

        #checking is UAS reached within 15 feet in diameter of the desired coordinate desitination
        while(distance > 7.5):

            if(self.RTL_stat() == True):

                while self.RTL_stat():
                    pass

                self.UAS_dk.simple_goto(LocationGlobal( latitude_deg, longitude_deg, self.alt ))
                self.waypoint_reached( latitude_deg, longitude_deg )
                break
             
            #distance between 2 points retuirn value in feet    
            distance = self.haversine(latitude_deg, longitude_deg)            
            print("HAS NOT REACHED WAYPOINT YET")
            time.sleep(.5)

        print("REACHED WAYPOINT")
        
        return True

    
    def waypoint_lap( self ):
        """
        Define a sequence of waypoints to be followed by the UAS in a lap.

        Returns:
            str: A message indicating lap completion.
        """
        nextWP_index = self.currWP_index + 1
        storedWP = None
        nextWP = LocationGlobal( self.waypoint_lap_latitude[ nextWP_index ], self.waypoint_lap_longitude[ nextWP_index ], self.alt )

        while self.currWP_index != len( self.waypoint_lap_latitude ):
            if self.RTL_stat():
                if storedWP is None:
                    storedWP = LocationGlobal( self.waypoint_lap_latitude[ self.currWP_index ], self.waypoint_lap_longitude[ self.currWP_index ], self.alt )

                while self.RTL_stat():
                    pass

                self.UAS_dk.simple_goto( storedWP )
                self.waypoint_reached( self.waypoint_lap_latitude[ nextWP_index ], self.waypoint_lap_longitude[ nextWP_index ] )

            else:
                    
                self.UAS_dk.simple_goto( nextWP )
                self.waypoint_reached( self.waypoint_lap_latitude[ nextWP_index ], self.waypoint_reached[ nextWP_index ] )

                nextWP_index += 1
                self.currWP_index += 1

                if nextWP_index == len( self.waypoint_lap_latitude ):
                    self.currWP_index = 0
                    self.lap += 1

        return f"Lap number {self.lap} is complete"

    def user_waypoint_input(self):
        """
        Allow the user to input a set of latitude and longitude coordinates for waypoints.

        Returns:
            None
        """
        # Ask for the number of coordinates and create a latitude and longitude array
        while 1:
            # Check for non-integer value
            try:
                number_of_coordinates = int(input("\nHow many coordinates?\n"))
                break
            except ValueError:
                print("Enter an integer")

        waypoint_lap_latitude  = array('i', [0] * number_of_coordinates)
        waypoint_lap_longitude = array('i', [0] * number_of_coordinates)

        # Ask for longitude and latitude coordinates and put them in their respective arrays
        for i in range(number_of_coordinates):
            while 1:
                # Check for non-integer values
                try:
                    waypoint_lap_latitude [i] = int(input(f"Enter latitude {i + 1}:\n"))
                    break
                except ValueError:
                    print("Coordinate must be an integer")

            while 1:
                # Check for non-integer values
                try:
                    waypoint_lap_longitude[i] = int(input(f"Enter longitude {i + 1}:\n"))
                    break
                except ValueError:
                    print("Coordinate must be an integer")

        # Print the coordinates in the array
        print("\nLatitudes entered:")
        for i in range(number_of_coordinates):
            if (i == number_of_coordinates-1):
                print(waypoint_lap_latitude [i])
            else:
                print(waypoint_lap_latitude [i], end=", ")
            

        print("\nLongitudes entered:")
        for i in range(number_of_coordinates):
            if (i == number_of_coordinates-1):
                print(waypoint_lap_longitude[i])
            else:
                print(waypoint_lap_longitude[i], end=", ") 
    
    def deliver_payload(self, servo_x, longitude, latitude):
        """
        Deliver a payload using a specified servo (not implemented).

        Args:
            servo_x (int): The servo number to be activated.
            longitude (float): The longitude coordinate.
            latitude (float): The latitude coordinate.

        Returns:
            None
        """
        start = time.time()

        
        #ENTER CODE HERE
        
        end = time.time()
        difference = end - start
        self.deliver_payload_time.append(difference)


        return print("NOT IMPLEMENTED")

    def search_area_waypoint(self):
        """
        Define a search area waypoint.

        This method defines a search area waypoint.

        :return: None
        """
        start = time.time()
        for x in range(len(self.search_area_latitude)):
            #go to wp
            print(f"GOING TO SEARCH AREA WAYPOINT: {x}") 
            location = LocationGlobalRelative(self.search_area_latitude[x],self.search_area_longitude[x],self.alt)
            self.UAS_dk.simple_goto( location )
            #call the waypoint reached
            self.waypoint_reached(self.search_area_latitude[x],self.search_area_longitude[x])
            #get attitide data
            p1 = multiprocessing.Process(target=self.attitude())
            #take image
            p2 = multiprocessing.Process(target=self.trigger_camera(), args= (f"image{x}.jpg",))
            #start the execution and wait 
            p1.start()
            p2.start()
            p1.join()
            p2.join()
            #geotag
            p3 = multiprocessing.Process(target = self.geotag(), args= (f"image{x}.jpg",))
            p3.start()
        end = time.time()
        difference = end - start
        self.search_area_waypoint_time.append(difference)

        return print("UAS COMPLETED SEARCH THE AREA")

    def sum(self, arr):
        """
        Calculate the sum of values in the input array.

        Args:
            arr (list): List of numeric values to be summed.

        Returns:
            float: The sum of values in the input list.
        """
        sum = 0
        for value in arr:
            sum += value
        return sum
    
    def avg(self, arr):
        """
        Calculate the average of values in the input array.

        Args:
            arr (list): List of numeric values to calculate the average from.

        Returns:
            float: The average of values in the input list.
        """
        if len(arr) == 0:
                return 0  # Avoid division by zero for an empty array

        total = sum(arr)
        average = total / len(arr)
        return average
        
    def export(self):
        """
        Export, Calculate and record the average and sum of execution times for various methods.

        Returns:
            None
        """
        #average calculation
        avg_attitude = self.avg(self.attitude_time)
        avg_deliver_payload = self.avg(self.deliver_payload_time)
        avg_geotag = self.avg(self.geotag_time)
        avg_haversine = self.avg(self.haversine_time)
        avg_search_area_waypoint = self.avg(self.search_area_waypoint_time)
        avg_subprocess_execute = self.avg(self.subprocess_execute_time)
        avg_trigger_camera = self.avg(self.trigger_camera_time)
        avg_waypoint_lap = self.avg(self.waypoint_lap_time)
        #sum calcualtion
        sum_attitude = self.sum(self.attitude_time)
        sum_deliver_payload = self.sum(self.deliver_payload_time)
        sum_geotag = self.sum(self.geotag_time)
        sum_haversine = self.sum(self.haversine_time)
        sum_search_area_waypoint = self.sum(self.search_area_waypoint_time)
        sum_subprocess_execute = self.sum(self.subprocess_execute_time)
        sum_trigger_camera = self.sum(self.trigger_camera_time)
        sum_waypoint_lap = self.sum(self.waypoint_lap_time)

            
        data_averages_and_time = [
            ("attitude", self.attitude_time, avg_attitude, sum_attitude),
            ("deliver_payload", self.deliver_payload_time, avg_deliver_payload,sum_deliver_payload),
            ("geotag", self.geotag_time, avg_geotag,sum_geotag),
            ("haversine", self.haversine_time, avg_haversine,sum_haversine),
            ("search_area_waypoint", self.search_area_waypoint_time, avg_search_area_waypoint,sum_search_area_waypoint),
            ("subprocess_execute", self.subprocess_execute_time, avg_subprocess_execute,sum_subprocess_execute),
            ("trigger_camera", self.trigger_camera_time, avg_trigger_camera,sum_trigger_camera),
            ("waypoint_lap", self.waypoint_lap_time, avg_waypoint_lap,sum_waypoint_lap)
        ]
        with open('Data_log.txt', 'a') as file:
                for data_name, data_values, data_average, data_sum in data_averages_and_time:
                        file.write(f"{data_name}: {data_values}\n")
                        file.write(f"{data_name} average: {data_average} seconds\n")
                        file.write(f"{data_name} sum: {data_sum} seconds\n\n")

    def KAMIKAZE():
        """
        Kills the UAS by completely cutting power to drone

        Returns:
            None
        """
        #send signal to relay to kill drone
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⠤⠖⠛⣷⣶⣶⠿⢿⣿⣿⣶⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡴⣾⣿⠋⠀⠀⠀⢾⣿⠏⠀⠀⠀⠀⠈⠛⠻⣿⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡾⠋⠀⠙⠛⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⢻⣷⣶⣦⣤⡀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⢀⣠⣤⣤⣠⣶⣿⡅⠀⠀⠀⣤⣤⣴⣶⠗⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⠆⠀⠹⣷⣤⡀⠀⠀⠀⠀⠀")
        print("⠀⠀⣰⡿⠋⠉⢹⣿⠁⠉⠀⠀⠀⠀⠀⣿⠏⠀⠀⠀⠀⢀⣠⣤⠀⠀⠀⠀⠲⣤⣄⣀⣀⠀⠀⠀⠙⢻⣷⣦⡀⠀⠀")
        print("⠀⣰⣿⠇⠀⠀⠸⠿⠂⠀⠀⠀⠀⠀⠀⠟⠀⠀⠀⠀⠠⣿⡏⠁⠀⠀⠀⠀⠀⠈⢿⠁⠀⠀⠀⠀⠀⠸⣿⠉⢿⣆⠀")
        print("⢰⣿⡁⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣦⡀⠛⢿⣦⠀⠀⡀⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠛⢀⠀⣿⡄")
        print("⢸⡿⠁⠀⠀⢿⣄⠀⡀⠀⠀⠀⠀⢀⣤⣀⣀⣀⣤⣿⣷⣶⡿⠻⣿⣿⠿⣷⣦⣄⣸⣷⠀⠀⠀⢠⣄⠀⠀⠈⠛⠿⣿")
        print("⠸⣿⣾⠃⠀⠀⠛⠿⠃⠀⠀⠰⣤⣴⣿⠿⠿⠿⠛⠉⠉⠀⠀⡄⠀⢰⣿⠟⢿⣿⣿⣄⡀⢰⣿⡟⠀⠀⠀⠀⠀⢹⡇")
        print("⠀⢸⣿⢸⡆⠀⠶⠿⠀⣀⡀⠠⣬⣭⣭⣀⠀⣆⠀⠀⢠⠀⠀⣰⠃⣰⣿⣿⠏⠀⠀⣉⣿⣿⠀⠙⠷⠀⠀⢠⣶⡀⣸⣧")
        print("⠀⠸⣿⣿⣷⡄⠀⠀⠘⠋⠁⠀⠀⠀⠉⡛⢷⣽⣦⠀⢸⡄⠀⣿⢀⣿⣿⣿⡶⠒⠛⢋⡅⠀⠀⠀⢀⣴⢀⡼⠟⠛⠟⠁")
        print("⠀⠀⠈⠙⠻⣷⣶⣦⣴⡾⠛⠶⠦⣶⠾⢿⣶⣬⣿⡆⠸⣧⢠⡇⢸⣿⣣⣥⣄⣀⣈⣤⣶⣦⣴⣿⠟⠋⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⣽⣿⠀⢿⠈⣧⣼⢹⣿⣀⣀⠉⠛⠛⠉⠀⠈⠉⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡶⢿⡛⢹⣿⡄⠸⠇⣿⡇⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣶⡿⢛⣉⣣⣾⣿⠛⣿⣷⠀⡀⢸⣇⢸⡟⠛⣿⡇⢠⡟⢿⣷⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣅⠀⠀⡉⠛⢿⣅⣀⣿⣿⠀⣿⣄⣉⣹⣧⡴⢾⣯⡀⠈⠋⠉⢻⣿⡀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣏⣀⣾⣏⠀⠀⠈⠙⠿⠿⠋⢻⡟⠋⠛⢿⡀⠀⠸⠀⠀⣀⠀⠀⣽⣿⡆⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠿⠿⢿⣷⣀⣀⣼⣦⠀⠀⠀⢁⣀⣠⣶⡀⠀⣀⣀⣀⣼⣤⣾⣿⡿⠇⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠿⠿⣿⣷⣶⣿⠿⠟⣿⠛⠿⣶⣿⣿⠿⠋⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⡇⠀⣰⠃⣿⡇⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⢻⣇⠀⣿⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠘⣿⠀⣿⠀⢿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢿⣿⠀⣿⠀⣿⡆⠸⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣯⣾⡟⠀⠁⠀⢿⣇⠀⢻⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠋⣻⣷⠿⠋⠀⡀⠀⠀⠸⢿⡄⠀⢻⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠖⠛⠁⠀⠀⣰⠇⠀⠀⠀⠀⠀⠀⠀⠈⠙⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")



        return print("万歳")


if __name__ == '__main__':
    pass
    
