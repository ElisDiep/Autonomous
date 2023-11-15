import time
import os
import math
import multiprocessing
import subprocess
import exiftool
from pymavlink import mavutil
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
from array import array
import pymavlink.dialects.v20.all as dialect
from haversine import haversine, Unit

class CLASS:
    def __init__(self):
        """
        Initializes the CLASS object.

        This method initializes the class and establishes connections to UAS and the camera.

        :return: None
        """
        #PARAMTERS
        self.ALTITUDE = 25.0
        self.WAYPOINT_RADIUS = 7.5
        self.PAYLOAD_RADIUS = 2
        self.SEARCH_AREA_RADIUS = 2
        #connecting to UAS with dronekit
        print("Connecting to UAS")
        #self.connection_string = 'udpin:localhost:14540'
        self.connection_string = "/dev/ttyACM0" #usb to micro usb
        self.UAS_dk = connect(self.connection_string, baud=57600, wait_ready=True)
        print("Connected with DroneKit")

        #connecting to mavlink
        print('Connecting MavLink')
        self.UAS_mav = mavutil.mavlink_connection(self.connection_string, baud=57600)
        #self.UAS_mav.wait_heartbeat()
        print("hearbeat from system {system %u compenent %u}" %(self.UAS_mav.target_system, self.UAS_mav.target_component))
        print("Mavlink Connected")


        
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

        #connect the camera
        print("Connecting to the camera")
        self.command = ["gphoto2", "--auto-detect"]
        self.subprocess_execute(self.command)
        print('Camera Connected')

        #declaring initial variable
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        self.image_number = 1
        self.drone_sensory = [self.pitch, self.roll, self.yaw, self.lat, self.lon, self.alt]
        self.currWP_index = 0
        self.lap = 0
        self.filename = f"image"
        self.waypoint_lap_latitude = [
            21.4002232, 21.4004455, 21.4007302, 21.4004929
        ]
        self.waypoint_lap_longitude = [
            -157.7645463, -157.7646348, -157.7639616, -157.7637658
        ]


        #predefined search area value for Kawainui test
        self.search_area_latitude = [
            21.4002344, 21.4003056, 21,4004118, 21.4004817, 
            21.4005753, 21.4007576, 21.4006702, 21.4006128, 
            21.4005541, 21.4004842, 21.4004530, 21.4005753
        ]

        self.search_area_longitude = [
            -157.7644624, -157.7642258, -157.7640527, -157.7638744, 
            -157.7637121, -157.7638395, -157.7640112, -157.7641936,  
            -157.7643558, -157.7645986, -157.7642298, -157.7639160
        ]
        #self.user_waypoint_input()
        '''
        print("AUTONOMOUS SCRIPT IS READY")
        while self.IS_ARMED != True:
            print("Waiting for arming....")
            time.sleep(0.5)

        print("UAS IS NOW ARMED")
        while self.IS_AUTO != True:
            print("Waiting for UAS to be in AUTO MODE.........")
            time.sleep(0.5)
        print("UAS IS NOW IN AUTO MODE")
        print("!------------------ MISSION STARTING ----------------------!")
        '''


    def trigger_camera(self, image_name):
        """
        Trigger the camera to capture an image.

        This method triggers the camera to capture an image and saves it with the provided filename.

        :param filename: The filename to use for the captured image.
        :return: None
        """
        start = time.time()
        print(f'{image_name} IS BEING TAKEN')
        cmd = ('gphoto2', '--capture-image-and-download', '--filename', image_name)
        self.subprocess_execute(cmd)
        end = time.time()
        difference = end - start
        self.trigger_camera_time.append(difference)
        return print(f'{image_name} Captured \n')

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
        self.image_number += 1 #doesnt work
        #executing the tag command in ssh
        '''
        subprocess.run(tag_pyr_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        subprocess.run(tag_lat_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        subprocess.run(tag_long_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        subprocess.run(tag_alt_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                
        '''
        
        p1 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_pyr_command,))
        p2 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_lat_command,))
        p3 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_long_command,))
        p4 = multiprocessing.Process(target = self.subprocess_execute, args = (tag_alt_command,))
        

        p1.start()
        p2.start()
        p3.start()
        p4.start()
        

        end = time.time()
        difference = end - start

        self.geotag_time.append(difference)
        return print(f"{image_name} GEOTAGGED")

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

    # def haversine(self, lon1, lat1):
    #     """
    #     Use the Haversine formula to calculate the distance between two coordinates.

    #     Args:
    #         lon1 (float): Longitude of the first coordinate.
    #         lat1 (float): Latitude of the first coordinate.

    #     Returns:
    #         float: The distance between the two coordinates in meters.
    #     """
    #     start = time.time()
    #     curr_location = self.UAS_dk.location.global_relative_frame
    #     lat1 = self.toRadian(lat1)
    #     lon1 = self.toRadian(lon1)
    #     lat2 = self.toRadian(curr_location.lat)
    #     lon2 = self.toRadian(curr_location.lon)

    #     end = time.time()
    #     difference = end - start

    #     self.haversine_time.append(difference)
    #     # feet conversion * earth radius * something
    #     return 5280 * 3963.0 * math.acos( (math.sin(lat1)*math.sin(lat2)) + (math.cos(lat1) * math.cos(lat2)) * math.cos(lon2 - lon1) )

    def haversine(self, lat1, lon1):
        """
        Use the Haversine formula to calculate the distance between two coordinates.

        Args:
            lon1 (float): Longitude of the first coordinate.
            lat1 (float): Latitude of the first coordinate.

        Returns:
            float: The distance between the two coordinates in meters.
        """
        start = time.time()
        curr_lat = 0
        curr_lon = 0
        message = self.UAS_mav.recv_match(type=[dialect.MAVLink_position_target_global_int_message.msgname,
                                       dialect.MAVLink_global_position_int_message.msgname],
                                 blocking=True)   
        #print(message)
        # message = message.to_dict()
        # if message["mavpackettype"] == dialect.MAVLink_global_position_int_message.msgname:
        #     curr_lat = message["lat"] * 1e-7
        #     curr_lon = message["lon"] * 1e-7
        print(f'{lat1},{lon1}')
        curr_location = self.UAS_dk.location.global_relative_frame

        distance = haversine((curr_location.lat * 1e-7,curr_location.lon * 1e-7),(lat1 * 1e-7,lon1 * 1e-7), unit = 'ft')
        end = time.time()
        difference = end - start
        self.haversine_time.append(difference)
        return distance

    def IS_ARMED(self):
        """
        Check if the UAS is "ARMED" mode.

        Returns:
            bool: True if the UAS is ARMED, False otherwise.
        """  
        return self.UAS_dk.ARMED

    def IS_AUTO(self):
        """
        Check if the UAS is in "AUTO" mode.

        Returns:
            bool: True if the UAS is in AUTO, False otherwise.
        """        
        return self.UAS_dk.mode == "AUTO"

    def RTL_stat( self ):
        """
        Check if the UAS is in "Return to Launch" mode.

        Returns:
            bool: True if the UAS is in RTL mode, False otherwise.
        """
        return self.UAS_dk.mode == "RTL"

    def spline_waypoint_command(self, latitude, longitude, seq):
        """
        Define a spline waypoint command.

        Args:
            latitude (float): The latitude coordinate.
            longitude (float): The longitude coordinate.
            seq (int): The number sequence according to mission.

        Returns:
            None
        """ 

        command = dialect.MAV_CMD_NAV_SPLINE_WAYPOINT

        message = dialect.MAVLink_mission_item_int_message(
            self.UAS_mav.target_system,  #target_system
            self.UAS_mav.target_component, #target_component
            seq,
            dialect.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            command, #MAV_CMD_NAV_WAYPOINT (16) or try to change it to  waypoint_command
            0,
            1, #auto continue 
            0, #hold (s)
            self.PAYLOAD_RADIUS, #Accept radius (m)
            self.PAYLOAD_RADIUS, #pass radius (m)
            0, #yaw (deg)
            int(latitude*1e7),  
            int(longitude*1e7),
            self.ALTITUDE,
            0
            )

        # Send the message
        self.UAS_mav.mav.send(message)
        #msg = self.UAS_mav.recv_match(type = dialect.MAVLink_mission_item_int_message.msgname, blocking = True)

    def count(self, waypoints):
        self.UAS_mav.mav.mission_count_send(
        self.UAS_mav.target_system,  #target_system
        self.UAS_mav.target_component,#target_component
        waypoints,#total number of commands in the mission
        0 #0-main mission
    )
        

    def mission_start(self):
        command = mavutil.mavlink.MAV_CMD_MISSION_START
        self.UAS_mav.mav.command_long_send(
        self.UAS_mav.target_system,  #target_system
        self.UAS_mav.target_component,#target_component
        command,#command
        0,0,0,0,0,0,0,0
        )
        return True
    
    def waypoint_command(self, latitude, longitude, seq):
        """
        Define a waypoint command.

        Args:
            latitude (float): The latitude coordinate.
            longitude (float): The longitude coordinate.
            seq (int): The number sequence according to mission.

        Returns:
            None
        """ 

        command = dialect.MAV_CMD_NAV_WAYPOINT

        message = dialect.MAVLink_mission_item_int_message(
            self.UAS_mav.target_system,  #target_system
            self.UAS_mav.target_component, #target_component
            seq,
            dialect.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            command, #MAV_CMD_NAV_WAYPOINT (16) or try to change it to  waypoint_command
            0,
            1, #auto continue 
            0, #hold (s)
            self.WAYPOINT_RADIUS, #Accept radius (m)
            self.WAYPOINT_RADIUS, #pass radius (m)
            math.nan, #yaw (deg)
            int(latitude*1e7),  
            int(longitude*1e7),
            self.ALTITUDE,
            0
            )

        # Send the message
        self.UAS_mav.mav.send(message)
        #msg = self.UAS_mav.recv_match(type = dialect.MAVLink_mission_item_int_message.msgname, blocking = True)

    
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
            self.UAS_mav.target_system,  #target_system
            self.UAS_mav.target_component, #target_component
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

        #self.UAS_mav.mav.command_long_send(LONG_SEND_WAYPOINT_parameter)
        #msg = self.UAS_mav.recv_msg(type = 'COMMAND_ACK', blocking = True)
        return print('SERVO ACTIVATED')

    
    def waypoint_reached (self, latitude_deg, longitude_deg, radius ):
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
        while(distance > radius):

            #distance between 2 points retuirn value in feet    
            distance = self.haversine(latitude_deg, longitude_deg)            
            print(f"Distance to waypoint: {distance}")
            time.sleep(.5)

        print("REACHED WAYPOINT")
        
        return True

    
    def waypoint_lap( self ):
        """
        Define a sequence of waypoints to be followed by the UAS in a lap.

        Returns:
            str: A message indicating lap completion.

        """
        self.count(len(self.waypoint_lap_latitude)+1)
        self.waypoint_command(self.waypoint_lap_latitude[ 0 ], self.waypoint_lap_longitude[ 0 ],0)

        for wp in range(len(self.waypoint_lap_latitude)):
            self.waypoint_command(self.waypoint_lap_latitude[ wp ], self.waypoint_lap_longitude[ wp ],wp+1)
            #self.waypoint_reached(self.waypoint_lap_latitude[ 0 ], self.waypoint_lap_longitude[ 0 ], self.WAYPOINT_RADIUS)

        self.mission_start()
        self.response("MISSION_ACK")
        for reached in range(len(self.waypoint_lap_latitude)):
            self.response("MISSION_ITEM_REACHED")
        self.UAS_dk.commands.clear()
        self.UAS_dk.commands.upload()
        return print("DONE with lap")
    
    def response(self, keyword):
        return print("-- Message Read " + str(self.UAS_mav.recv_match(type = keyword, blocking = True)))

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
    


    def deliver_payload(self, servo_x, latitude, longitude):
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

        self.waypoint_command(latitude,longitude)
        self.waypoint_reached(latitude,longitude,self.PAYLOAD_RADIUS)
        self.servo_command(servo_x)
        
        
        end = time.time()
        difference = end - start
        self.deliver_payload_time.append(difference)


        return print(f"Payload {servo_x} Delivered")

    def search_area_waypoint(self):
        """
        Define a search area waypoint.

        This method defines a search area waypoint.

        :return: None
        """
        start= time.time()
        print('Now Conducting the search area')
        self.UAS_dk.commands.clear()
        self.UAS_dk.commands.upload()
        #print(self.UAS_dk.location.global_frame)
        self.UAS_dk.mode = VehicleMode("GUIDED")
        target_locaton=LocationGlobalRelative(self.search_area_latitude[0],self.search_area_longitude[0], self.ALTITUDE)
        #self.waypoint_reached(self.search_area_latitude[0],self.search_area_longitude[0],self.PAYLOAD_RADIUS)

        target_locaton=LocationGlobalRelative(self.search_area_latitude[1],self.search_area_longitude[1], self.ALTITUDE)
        target_locaton=LocationGlobalRelative(self.search_area_latitude[2],self.search_area_longitude[2], self.ALTITUDE)


        #self.UAS_dk.simple_goto(LocationGlobalRelative(self.search_area_latitude[2],self.search_area_longitude[2], self.ALTITUDE))
        # for wp in range(len(self.search_area_latitude)-1):
        #     target_locaton=LocationGlobalRelative(self.search_area_latitude[wp],self.search_area_longitude[wp], self.ALTITUDE)
        #     self.UAS_dk.simple_goto(target_locaton)
            #self.waypoint_reached(self.search_area_latitude[wp],self.search_area_longitude[wp],self.PAYLOAD_RADIUS)
            #print(wp)
            #print(self.UAS_dk.location.global_frame)
            #self.response("MISSION_ITEM_REACHED")
            #self.waypoint_reached(self.search_area_latitude[wp],self.search_area_longitude[wp], self.SEARCH_AREA_RADIUS)
            #get attitide data
            #p1 = multiprocessing.Process(target=self.attitude())
            #self.attitude()
            #self.trigger_camera(f'image{wp+1}.jpg')
            #take image
            #p2 = multiprocessing.Process(target=self.trigger_camera, args= (f"image{x+1}.jpg",))
            #start the execution and wait 
            #p1.start()
            #p2.start()
            #p1.join()
            #p2.join()
            #geotag
            #self.geotag(f'image{x+1}.jpg')

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
    
