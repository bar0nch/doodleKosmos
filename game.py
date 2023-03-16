import os, sys

assets_path = os.path.join(os.getcwd(), 'assets')
data_path = os.path.join(os.getcwd(), 'data')
os.chdir(assets_path)
sys.path.insert(0, assets_path)
sys.path.insert(2, data_path)

import libraries
import pygame
import pygame_textinput
from pygame.locals import *
from libraries import planet_image_generator as PIG
import time, random, math, copy, shelve

pygame.init()

'''
VERY IMPORTANT NOTES


The main map of a planet must not contain pitch black pixels or they will be displayed transparent.
'''

#========================================================================BUGLOG========================================================================

'''
New technology is researched istantly at the beginning of the game some times.

If switched too fast from scene "planet view / main" to scene "planet view / building view" the planet moving animation automatically gets permission to reset in the original state
in every future activation.

when switching from planet earth to other planets the buil new base button still appears until scrolling the other buildings

Rarely when expanding a scrolldown menu it's options all get the hovered state at the same time
'''

#===================================================================GAME PARAMETERS====================================================================

#ordered alphabetically
bg_col = (240, 240, 240)
cur_win_size = (1500, 750) #current window size
dim_txt_col = (167, 190, 190)
general_menus_txt_font = 'Exo-ExtraLight.ttf'
general_txt_font = 'Future18.ttf'
general_txt_col = (29, 115, 201)
general_widget_col1 = (166, 212, 242)
general_widget_col2 = (210, 233, 249)
hover_delta_col = 50 #how much the color of the hovered option darkens or lightens in pop up menus
planet_building_display_pos = (610, 350, 500, 500)
planet_buildings_menu_underline = pygame.image.load(os.path.join("images", "planet building menu underline.png"))
planet_buildings_menus_default_y = 430
planet_buildings_menu_font_size = 40
planet_buildings_menus_squares_height = 100
planet_buildings_menus_squares_width = 500
planets_win_center_x_default = 1150 #the x coordinate of a 0Km radius planet's center
planets_win_center_y = 500
pop_up_menus_bg_col = (30, 30, 40)
pop_up_menus_txt_col = (121, 179, 236)
pop_up_menus_txt_font = 'FutureSpace.ttf'
pygame.key.set_repeat(400, 30)
research_slowness = 6 #higher the number less the probability to research technologies
structure_names_display_font_size = 52
structures_abs_padding_in_display = 80
structures_font_size_in_buildings_display = 32
upper_permanent_menu_polygon_width = 500
win_size = (1500, 750) #default window size

#====================================================================MISCELLANEOUS=====================================================================

win = pygame.display.set_mode(win_size, flags=pygame.FULLSCREEN)
cur_win_size = win.get_size()
pygame.display.set_caption('lil python game')

planet_upper_menu_txt_font = pygame.font.Font('Astromix.otf', 68) #cashing the upper menu text
date_upper_menu_txt_font = pygame.font.Font(pop_up_menus_txt_font, 30)
planet_upper_menu_txt_obj = planet_upper_menu_txt_font.render("no planet found", True, general_txt_col)
planet_upper_menu_txt_rect = planet_upper_menu_txt_obj.get_rect()
planet_upper_menu_txt_rect.center = (cur_win_size[0] // 2, 50)

building_menu_line1_img = pygame.image.load(os.path.join('images','planet building display line 1.png'))
building_menu_line1_rect = building_menu_line1_img.get_rect()
building_menu_line1_rect.topright = (planet_building_display_pos[0] + planet_building_display_pos[2], planet_building_display_pos[1])
building_menu_line3_img = pygame.image.load(os.path.join('images','planet building display line 3.png'))
building_menu_line3_rect = building_menu_line3_img.get_rect()
building_menu_line3_rect.topleft = (planet_building_display_pos[0], planet_building_display_pos[1])

earth_bases_txt_obj = pygame.font.Font(general_txt_font, 50).render("bases of operation", True, general_txt_col)
earth_bases_txt_rect = earth_bases_txt_obj.get_rect()
earth_bases_txt_rect.topleft = (180, 200)

globalcoins_upper_menu_icon_img = pygame.image.load(os.path.join('images','globalcoins permanent menu icon.png'))

#NOTE: menus dict currently is only used to manage textual input options
#WARNING: currently not every menu in the game is in the menus dict and on top of that it is a dated feature (if redone it would be a class attribute not a global dict)
run = True
current_scene = "planet view / main"
ref_time = time.time()
menus = {} #contains all the menus object
text_inputs = []
pause_menu_open = False #indicator variable
selected_menu = None #if a menu is fixed it must be selected to be updated
key_cooldown = {} #to add some delay between a key press and another press of the same key (doesn't affect fps)
selected_planet = current_planet = selected_scene = None #selected planet contains the string of the name while current planet contains the object itself
selected_build_menu = None
prev_selected_build = selected_build = selected_structure = planet_building_current_info_display = None
planet_building_current_info_display_menu = None
unit_measurements = {
                     "radius":"Km",
                     "temperature":"mK",
                     "pressure":"mbar",
                     "mass":"M'",
                     "surface gravity":"m/s'2"
                     }

#======================================================================GAME STATS======================================================================

globalcoins = 10000

#================================================================MULTIPURPOSE FUNCTIONS================================================================

def iter_operation(iterable, operation : str, value):
    iter_type = type(iterable)
    return iter_type([eval(str(obj) + operation + str(value)) for obj in iterable])
    

def compress_number_value_in_str(number, round_approx=4):
    '''
    Returns a number in the form of a string to be displayed and rounds the thousands millions billions... with the letters K M B...
    '''
    if round_approx < 4:
        raise ValueError("round approximation (round_approx) of the function compress_number_value_in_str must not be less than 4")
    if number < 1000:
        number_str = str(number)
        number_list = number_str.split('.')
        if len(number_list) == 1:
            if not len(number_list[0]) == round_approx + 1:
                number_str += '.'
                while len(number_str) <= round_approx + 1:
                    number_str += '0'
        else:
            while len(number_str) - 1 < round_approx + 1:
                number_str += '0'
            if len(number_str) - 1 > round_approx + 1:
                number_str = number_str[:round_approx+2]
        return number_str
    elif number < 1000000:
        number_str = str(number / 1000)
        while len(number_str) - 1 < round_approx:
            number_str += '0'
        if len(number_str) - 1 > round_approx:
            number_str = number_str[:round_approx+1]
        return number_str + 'K'
    elif number < 1000000000:
        number_str = str(number / 1000000)
        while len(number_str) - 1 < round_approx:
            number_str += '0'
        if len(number_str) - 1 > round_approx:
            number_str = number_str[:round_approx+1]
        return number_str + 'M'
    elif number < 1000000000000:
        number_str = str(number / 1000000000)
        while len(number_str) - 1 < round_approx:
            number_str += '0'
        if len(number_str) - 1 > round_approx:
            number_str = number_str[:round_approx+1]
        return number_str + 'T'
    else:
        number_str = str(number / 1000000000000)
        while len(number_str) - 1 < round_approx:
            number_str += '0'
        if len(number_str) - 1 > round_approx:
            number_str = number_str[:round_approx+1]
        return number_str + 'Q'


def change_surface_col(surface, new_color : tuple):
    w, h = surface.get_size()
    r, g, b = new_color
    for x in range(w):
        for y in range(h):
            a = surface.get_at((x, y))[3]
            surface.set_at((x, y), Color(r, g, b, a))
    return (r, g, b)

def change_surface_py_col(surface, new_color : Color):
    w, h = surface.get_size()
    r, g, b, _ = new_color
    for x in range(w):
        for y in range(h):
            a = surface.get_at((x, y))[3]
            surface.set_at((x, y), Color(r, g, b, a))
    return (r, g, b)

#===================================================================GENERAL CLASSES====================================================================

class GameException(Exception):
    pass



class Animation:
    def __init__(self):
        self.is_active = False


    def activate(self):
        '''
        Activates the animation without any procedure or condition (use begin instead).
        '''
        self.is_active = True


    def deactivate(self):
        '''
        Dectivates the animation without any procedure or condition (use interrupt instead).
        '''
        self.is_active = False


    def begin(self, event_verified=None):
        if not self.is_active:
            if event_verified == None or event_verified == True:
                self.activate()
                return True
        return False


    def interrupt(self, event_verified=None):
        if self.is_active:
            if event_verified == None or event_verified == True:
                self.deactivate()
                return True
        return False


    def animation_update(self):
        if self.is_active:
            return True
        else:
            return False


    def animation_update_GFX(self):
        if self.is_active:
            return True
        else:
            return False



class VerticalScrollBarAnimation(Animation):
    def __init__(self, scrollbar):
        super().__init__()
        self.begin_lock = False
        
        self.scrollbar = scrollbar
        self.initial_pos = None
        self.initial_mouse_pos = None
        if self.scrollbar.bar_thickness:
            self.bar_rect = Rect(self.scrollbar.x - self.scrollbar.bar_thickness // 2,
                                 self.scrollbar.bar_y - self.scrollbar.bar_height // 2,
                                 self.scrollbar.bar_thickness,
                                 self.scrollbar.bar_height)
        else:
            self.bar_rect = Rect(self.scrollbar.x - self.scrollbar.thickness // 2,
                                 self.scrollbar.bar_y - self.scrollbar.bar_height // 2,
                                 self.scrollbar.thickness,
                                 self.scrollbar.bar_height)


    def begin(self, event):
        if not self.begin_lock:
            event_verified = event.type == pygame.MOUSEBUTTONDOWN and self.bar_rect.collidepoint(pygame.mouse.get_pos())
            if super().begin(event_verified):
                self.initial_pos = self.scrollbar.bar_y
                self.initial_mouse_pos = pygame.mouse.get_pos()[1]
                self.begin_lock = True
                self.scrollbar.selected = True


    def interrupt(self, event):
        if super().interrupt(event.type == pygame.MOUSEBUTTONUP):
            self.begin_lock = False
            self.initial_pos = None
            self.initial_mouse_pos = None
            self.scrollbar.selected = False


    def animation_update(self):
        if self.scrollbar.bar_thickness:
            self.bar_rect = Rect(self.scrollbar.x - self.scrollbar.bar_thickness // 2,
                                 self.scrollbar.bar_y - self.scrollbar.bar_height // 2,
                                 self.scrollbar.bar_thickness,
                                 self.scrollbar.bar_height)
        else:
            self.bar_rect = Rect(self.scrollbar.x - self.scrollbar.thickness // 2,
                                 self.scrollbar.bar_y - self.scrollbar.bar_height // 2,
                                 self.scrollbar.thickness,
                                 self.scrollbar.bar_height)
        if super().animation_update():
            return self.initial_pos - (self.initial_mouse_pos - pygame.mouse.get_pos()[1])
        else:
            return self.scrollbar.bar_y



class MoveAnimation(Animation): #WARNING: do not set the speed higher than the distance to travel
    def __init__(self, obj, objective : list, speed, back_n_fourth=False, stasis_time=0, reverse=False, reverse_speed=1, wait_for_instruction=False):
        super().__init__()

        self.phase = None #the action that the animation pursues
        self.obj = obj
        self.back_n_fourth = back_n_fourth #wether the animation has a "stasis" phase
        if back_n_fourth:
            self.reverse = reverse #wether to repeat the animation backwards when the stasis phase is complete
            self.wait_for_instruction = wait_for_instruction
            if wait_for_instruction:
                self.stasis_permission = False #when this variable is set to True the object will be able to go in return phase
            if reverse:
                self.reverse_speed = reverse_speed
            self.stasis_time = stasis_time
            self.begin_time = -1
            
        self.initial_pos = [obj.x, obj.y]
        self.objective = objective #the goal position of the object
        self.speed = speed

        self.ideal_pos = [obj.x, obj.y] #stores the real position in float type getting rounded later so in the long run the floating point part loss doesn't accumulate


    def __str__(self):
        return "active:"+str(self.is_active)+"\t"\
               "phase:"+str(self.phase)+"\t"\
               "initial position: "+str(str(self.initial_pos))+"\t"\
               "objective: "+str(self.objective)+"\t"\
               "ideal position: "+str(tuple(self.ideal_pos))+"\t"\


    def begin(self, event_verified):
        if super().begin(event_verified):
            self.phase = "move"
            self.initial_pos = [self.obj.x, self.obj.y]
            self.ideal_pos = [self.obj.x, self.obj.y]
            if self.back_n_fourth:
                self.begin_time = -1
                

    def interrupt(self, event_verified):
        if super().interrupt(event_verified):
            self.phase = None
            self.obj.x, self.obj.y = self.initial_pos
            self.ideal_pos = [self.obj.x, self.obj.y]


    def move_to_objective(self, objective, speed):
        angle = math.atan2(objective[1] - self.ideal_pos[1], objective[0] - self.ideal_pos[0]) #angle with the objective
        
        if not Rect(self.obj.x - abs(speed), self.obj.y - abs(speed), abs(speed) * 2, abs(speed) * 2).collidepoint(tuple(objective)):
            self.ideal_pos[0] += speed * math.cos(angle) #operations are done with the imaginary position first so the function itself does not actually move anything
            self.ideal_pos[1] += speed * math.sin(angle)
            return False
        else:
            self.ideal_pos = objective[:]
            return True


    def animation_update(self):
        if super().animation_update():
            self.obj.x, self.obj.y = round(self.ideal_pos[0]), round(self.ideal_pos[1])
            if self.phase == "move":
                if self.move_to_objective(self.objective, self.speed): #move_to_objective function must be called every update cycle
                    if self.back_n_fourth:
                        self.phase = "stasis"
                        self.begin_time = time.time()
                    else:
                        self.phase = None
                        self.obj.x, self.obj.y = round(self.ideal_pos[0]), round(self.ideal_pos[1])
                        self.deactivate()
                        return True

            elif self.phase == "stasis":
                if (time.time() - self.begin_time) >= self.stasis_time:
                    if self.wait_for_instruction:
                        if self.stasis_permission:
                            if self.reverse:
                                self.phase = "return"
                            else:
                                self.obj.x, self.obj.y = self.initial_pos #if it has no return phase just returns to the initial pos
                                self.phase = None
                                if self.wait_for_instruction:
                                    self.stasis_permission = False
                                self.deactivate()
                                return True
                    else:
                        if self.reverse:
                            self.phase = "return"
                        else:
                            self.obj.x, self.obj.y = self.initial_pos
                            self.phase = None
                            if self.wait_for_instruction:
                                self.stasis_permission = False
                            self.deactivate()
                            return True

            elif self.phase == "return":
                if self.move_to_objective(self.initial_pos.copy(), self.reverse_speed): #moves to initial pos
                    self.phase = None
                    if self.wait_for_instruction:
                        self.stasis_permission = False
                    self.obj.x, self.obj.y = round(self.ideal_pos[0]), round(self.ideal_pos[1]) #the last operation of move_to_objective() is to set the position to the objective
                    self.deactivate()                                                           #however since this clause is the last operation done in this update, the first
                    return True                                                                 #operation (setting the position to the ideal position) will never be executed and so
                                                                                                #begin() will set initial_pos to a wrong value, shifting the animation over time
            return False
        return False



class MoveAnimationGroup:
    def __init__(self, delta=None, objective=None, objectives=None, speed=1, back_n_fourth=False, stasis_time=0, reverse=False, reverse_speed=1, wait_for_instruction=False):
        self.delta = delta
        self.objective = objective
        self.objectives = objectives
        self.speed = speed
        self.back_n_fourth = back_n_fourth
        self.stasis_time = stasis_time
        self.reverse = reverse
        self.reverse_speed = reverse_speed
        self.wait_for_instruction = wait_for_instruction

        if (self.delta and self.objective) or (self.delta and self.objectives) or (self.objective and self.objectives):
            raise GameException("can't assign multiple target position parameters at the same time to a MoveAnimationGroup object\nchoose between delta, objective, objectives.")
        self.animations = []

        self.warning = False


    def append(self, obj):
        if self.delta:
            target = (obj.x + self.delta[0], obj.y + self.delta[1])
        elif self.objective:
            target = self.objective
        elif self.objectives:
            target = self.objectives[len(self.animations)]
        self.animations.append(MoveAnimation(obj, target, self.speed, self.back_n_fourth, self.stasis_time, self.reverse, self.reverse_speed, self.wait_for_instruction))


    def begin(self, event_verified):
        for animation in self.animations:
            animation.begin(event_verified)


    def animation_update(self):
        if not self.animations and not self.warning:
            print("WARNING: MoveAnimationGroup object ", self, " hasn't got any MoveAnimation object linked!")
            self.warning = True
        for animation in self.animations:
            animation.animation_update()

 
                                                                                                            
class GameObject:    
    def __init__(self):
        self.event_update_blocked = False
        self.update_blocked = False
        self.draw_blocked = False


    def event_update(self, event):
        pass


    def update(self):
        pass


    def draw(self):
        pass



class TestDummy(GameObject):
    def __init__(self,x,y,ball_radius=100):
        super().__init__()
        self.x = x
        self.y = y
        self.ball_radius = ball_radius
        self.color = [100, 100, 100]
        #self.mousedown_animation = MoveAnimation(self, [200, 100], speed=5, back_n_fourth=True, stasis_time=1, reverse=True, reverse_speed=50)


    def event_update(self, event):
        super().event_update(event)
        #self.mousedown_animation.begin(event.type == pygame.MOUSEBUTTONDOWN)


    def update(self):
        super().update()
        self.color[0] += random.randint(-20, 20)
        if self.color[0] < 0:
            self.color[0] = 0
        elif self.color[0] > 255:
            self.color[0] = 255
        self.color[1] += random.randint(-20, 20)
        if self.color[1] < 0:
            self.color[1] = 0
        elif self.color[1] > 255:
            self.color[1] = 255
        self.color[2] += random.randint(-20, 20)
        if self.color[2] < 0:
            self.color[2] = 0
        elif self.color[2] > 255:
            self.color[2] = 255
        
        #self.mousedown_animation.animation_update()


    def draw(self):
        super().draw()
        pygame.draw.circle(win, tuple(self.color), (self.x, self.y), self.ball_radius)


    
class Planet(GameObject):
    #side-note: planets are saved externally so changes made in this object's program will not be applied on old objects
    @staticmethod
    def activate_all_map_features():
        global planets
        
        for planet in planets.values():
            for planet_map in planet["object"].maps.values():
                planet_map.features.activate()

        
    def __init__(self, name, planet_dict):
        super().__init__()
        self.name = name
        self.planet_dict = planet_dict
        if self.name not in planet_dict.keys(): #if the planet is inexistent
            raise KeyError("The planet is not present in the selected planet dictionary.")
        self.dictionary = planet_dict[name] #be very cautious of the difference between dictionary and planet_dict, the first is the specific planet while the second contains every planet
        
        self.x = planets_win_center_x_default + self.dictionary["radius"] // 40 + 200
        self.y = planets_win_center_y
        self.GFXradius = self.x - planets_win_center_x_default #pseudo-realistic dimensions in scale (because they are ponderated not accurate, for visual appeal reasons)
        self.structure_view_animation = MoveAnimation(self, [self.x + 200, self.y], speed=2, back_n_fourth=True, stasis_time=0.6, reverse=True, reverse_speed=8, wait_for_instruction=True)

        self.temperature = self.dictionary["temperature"]
        self.pressure = self.dictionary["pressure"]

        self.mass = self.dictionary["mass"]
        self.radius = self.dictionary["radius"]
        self.surface_gravity = self.dictionary["surface gravity"]

        self.atmosphere = self.dictionary["atmosphere"]

        #acquifers levels: none; scarse; few; moderate; numerous; aboundant
        self.oceans = self.dictionary["oceans"]

        self.colonies  = []
        self.cities = []
        self.industrial_zones = []
        self.bases = []

        self.maps = self.dictionary["maps"]


        if "main" in self.maps:
            self.fixed_display_map = pygame.Surface(self.maps["main"].surface.get_size()) #makes a surface to display the planet
            self.fixed_display_map.blit(self.maps["main"].surface, (0, 0))
            self.fixed_display_map_rect = self.fixed_display_map.get_rect()
            reduction_scale = (int(self.fixed_display_map_rect.w * self.GFXradius * 2 / self.fixed_display_map_rect.h), self.GFXradius * 2) #matches the surface size with the GFXradius
            self.fixed_display_map = pygame.transform.scale(self.fixed_display_map, reduction_scale)
            self.fixed_display_map_rect = self.fixed_display_map.get_rect()
            crop_surf = pygame.Surface((self.fixed_display_map_rect.w, self.fixed_display_map_rect.h)) #crops it as a circle in the middle
            crop_surf.fill((255,255,255))
            pygame.draw.circle(crop_surf, (0,0,0), self.fixed_display_map_rect.center, self.GFXradius)
            crop_surf.blit(self.fixed_display_map, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
            self.fixed_display_map = crop_surf
            self.fixed_display_map_rect.center = (self.x, self.y) #positions it at the correct coordinates
        else:
            print("WARNING: planet", self.name, "has no main map to display")


    def enter_save_mode(self):
        self.planet_dict = None
        self.dictionary = None
        
        if "main" in self.maps:
            self.fixed_display_map = pygame.image.tostring(self.fixed_display_map, 'RGB')

        for planet_map in self.maps.values():
            planet_map.enter_save_mode()


    def exit_save_mode(self, planet_dict):
        self.planet_dict = planet_dict
        self.dictionary = planet_dict[self.name]
        
        if "main" in self.maps:
            self.fixed_display_map = pygame.image.fromstring(self.fixed_display_map, (self.fixed_display_map_rect.w, self.fixed_display_map_rect.h), 'RGB')

        for planet_map in self.maps.values():
            planet_map.exit_save_mode()


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.fixed_display_map_rect.center = (self.x, self.y)
            self.structure_view_animation.animation_update()

            
    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if "main" in self.maps:
                win.blit(self.fixed_display_map, self.fixed_display_map_rect, special_flags=pygame.BLEND_RGB_MIN)
            else:
                pygame.draw.circle(win, (0,0,0), (self.x, self.y), self.GFXradius)



class PlanetBuilding(GameObject): #only used to recycle code for the classes Colony City and IndustrialZone
    def __init__(self, view_structure_button, name, x, y, txt_x, txt_y, font_size=planet_buildings_menu_font_size, color=general_txt_col):
        super().__init__()
        self.is_selected = False
        self.view_structure_button = view_structure_button
        self.view_structure_button.hidden = True
        self.name = name
        self.x = x
        self.y = y
        self.hitbox = Rect(x, y, planet_buildings_menus_squares_width, planet_buildings_menus_squares_height)
        self.txt_x = txt_x
        self.txt_y = txt_y
        self.font_size = font_size
        self.color = color

        self.structures = []

        self.txt_font = pygame.font.Font(general_txt_font, font_size)
        if name:
            self.txt_object = self.txt_font.render(name, True, color)
            self.txt_rect = self.txt_object.get_rect()
            self.txt_rect.topleft = (self.txt_x, self.txt_y)
        else:
            self.txt_object = self.txt_font.render('', True, color)
            self.txt_rect = self.txt_object.get_rect()
            self.txt_rect.topleft = (self.txt_x, self.txt_y)


    def select(self):
        global selected_build
        if not self.is_selected:
            self.is_selected = True
            self.view_structure_button.hidden = False
            selected_build = self
            self.color = (self.color[0]+hover_delta_col,self.color[1]+hover_delta_col,self.color[2]+hover_delta_col)
            self.txt_object = self.txt_font.render(self.name, True, self.color)
            for colony in current_planet.colonies:
                if colony != self:
                    colony.deselect()
            for city in current_planet.cities:
                if city != self:
                    city.deselect()
            for industrial_zone in current_planet.industrial_zones:
                if industrial_zone != self:
                    industrial_zone.deselect()
            for base in current_planet.bases:
                if base != self:
                    base.deselect()


    def deselect(self):
        global selected_build
        if self.is_selected:
            self.is_selected = False
            self.view_structure_button.hidden = True
            if selected_build == self:
                selected_build = None
            self.color = (self.color[0]-hover_delta_col,self.color[1]-hover_delta_col,self.color[2]-hover_delta_col)
            self.txt_object = self.txt_font.render(self.name, True, self.color)


    def change_position(self, amount):
        self.x += amount[0]
        self.txt_x += amount[0]
        self.y += amount[1]
        self.txt_y += amount[1]
        if self.name:
            self.txt_rect.topleft = (self.txt_x, self.txt_y)
        else:
            self.txt_rect.topleft = (self.txt_x, self.txt_y)
        self.hitbox = Rect(self.x, self.y, planet_buildings_menus_squares_width, planet_buildings_menus_squares_height)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()


#=====================================================================GUI CLASSES======================================================================

class VerticalScrollBar(GameObject):
    def __init__(self, min_value, max_value, x, y, height, thickness, bg_col, bar_col, rounded=None, bar_thickness=None, capsule_bar=True, selection_inflate=0):
        super().__init__()
        self.selected = False
        self.min_value = min_value
        self.max_value = max_value
        self.x = x #x coordinate of the center of the background of the scrollbar
        self.y = y #y coordinate of the top of it
        self.height = height
        self.thickness = thickness
        self.rounded = rounded
        self.bar_thickness = bar_thickness
        self.bg_col = bg_col
        self.bar_col = bar_col
        self.capsule_bar = capsule_bar
        self.selection_inflate = selection_inflate

        self.bar_height = self.height // (self.max_value - self.min_value)
        self.bar_y = self.y + self.bar_height // 2 #y coordinate of the center of the bar
        self.bar_limits = (self.y + self.bar_height // 2, self.y + self.height - self.bar_height // 2)
        self.base_bar_thickness = bar_thickness
        self.selected_bar_thickness = self.base_bar_thickness + self.selection_inflate

        self.bg_rect = Rect(self.x - self.thickness // 2, self.y, self.thickness, self.height)
        self.animation = VerticalScrollBarAnimation(self)


    def draw_bar(self):
        '''
        Draws the movable bar according to the parameters and the action of the player.
        '''
        if self.bar_thickness:
            bar_rect = Rect(self.x - self.bar_thickness // 2, self.bar_y - self.bar_height // 2, self.bar_thickness, self.bar_height)
        else:
            bar_rect = Rect(self.x - self.thickness // 2, self.bar_y - self.bar_height // 2, self.thickness, self.bar_height)

        if self.capsule_bar:
            pygame.draw.rect(win, self.bar_col, bar_rect)
            if self.bar_thickness:
                pygame.draw.circle(win, self.bar_col, (self.x, self.bar_y - self.bar_height // 2), self.bar_thickness // 2)
                pygame.draw.circle(win, self.bar_col, (self.x, self.bar_y + self.bar_height // 2), self.bar_thickness // 2)
            else:
                pygame.draw.circle(win, self.bar_col, (self.x, self.bar_y - self.bar_height // 2), self.thickness // 2)
                pygame.draw.circle(win, self.bar_col, (self.x, self.bar_y + self.bar_height // 2), self.thickness // 2)
        else:
            if self.rounded:
                pygame.draw.rect(win, self.bar_col, bar_rect, border_radius=self.rounded)
            else:
                pygame.draw.rect(win, self.bar_col, bar_rect)


    def get_value(self):
        '''
        Gets the variable value from the position of the movable bar.
        '''
        return ((self.bar_y - self.bar_limits[0]) * self.max_value) / (self.bar_limits[1] - self.bar_limits[0])


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            self.animation.begin(event)
            self.animation.interrupt(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.selected_state_thickness = self.base_bar_thickness + self.selection_inflate
            if self.bar_thickness:
                if self.selected:
                    self.bar_thickness = self.selected_bar_thickness
                else:
                    self.bar_thickness = self.base_bar_thickness
            self.bar_height = self.height // (self.max_value - self.min_value)
            self.bar_limits = (self.y + self.bar_height // 2, self.y + self.height - self.bar_height // 2)
            self.bar_y = self.animation.animation_update()
            if self.bar_y < self.bar_limits[0]:
                self.bar_y = self.bar_limits[0]
            elif self.bar_y > self.bar_limits[1]:
                self.bar_y = self.bar_limits[1]
            self.bg_rect = Rect(self.x - self.thickness // 2, self.y, self.thickness, self.height)


    def draw(self):
        if not self.draw_blocked:
            super().draw()

            if self.rounded:
                pygame.draw.rect(win, self.bg_col, self.bg_rect, border_radius=self.rounded)
            else:
                pygame.draw.rect(win, self.bg_col, self.bg_rect)

            self.draw_bar()



class InventoryObject(GameObject):
    default_icon_image = pygame.image.load(os.path.join("images", "inventory icon - default.png"))
    bg_images = [os.path.join("images", "inventory object - 1.png"),
                 os.path.join("images", "inventory object - 2.png"),
                 os.path.join("images", "inventory object - 3.png")]

    all_objects = []

    usages = {"common":(102, 217, 255), "uncommon":(255, 153, 102), "special":(198, 121, 236)}

    obj_templates = {"test1":{"size":3,
                              "usage":"common"},
                     "test2":{"size":1,
                              "usage":"uncommon"},
                     "test3":{"size":2,
                              "usage":"special"}}
    
    def __init__(self, name, inventory):
        super().__init__()
        InventoryObject.all_objects.append(self)
        self.is_hovered = False
        self.is_selected = False
        self.x = 0
        self.y = 0
        self.inventory = inventory
        self.inventory_coords = None

        self.name = name
        if self.name in InventoryObject.obj_templates:
            self.inventory_size = InventoryObject.obj_templates[self.name]["size"] #space occupied inside the inventory
            self.bg_col = InventoryObject.usages[InventoryObject.obj_templates[self.name]["usage"]]
        else:
            self.inventory_size = 2
            self.bg_col = (200, 200, 200)
        self.offset = 5 #offset from cell rects of the inventory

        random.shuffle(InventoryObject.bg_images)
        self.bg_image = pygame.image.load(InventoryObject.bg_images[0]) #the image is scaled in the draw function
        change_surface_py_col(self.bg_image, Color(self.bg_col))
        self.bg_image_rect = self.bg_image.get_rect()
        self.last_size = self.bg_image.get_size()
        try:
            self.icon_image = pygame.image.load(os.path.join("images", "inventory icon - " + self.name + ".png"))
        except:
            self.icon_image = InventoryObject.default_icon_image
        self.icon_image_rect = self.icon_image.get_rect()
        self.name_txt_obj = pygame.font.Font(general_txt_font, 22).render(self.name, True, (240, 240, 240))
        self.name_txt_rect = self.name_txt_obj.get_rect()


    def event_update(self, event):
        if not self.event_update_blocked and not self.inventory.event_update_blocked:
            super().event_update(event)

            hitbox = Rect(self.x, self.y, self.last_size[0], self.last_size[1])
    
            if event.type == pygame.MOUSEBUTTONUP: #deselects the object
                if self.is_selected:
                    for inv in Inventory.all_inventories:
                        if not inv.event_update_blocked:
                            if Rect(inv.x, inv.y, inv.lenght * (inv.cell_size + inv.cell_spacing), inv.height * (inv.cell_size + inv.cell_spacing) + inv.name_padY + inv.name_txt_rect.h).collidepoint(pygame.mouse.get_pos()):
                                for y, row in enumerate(inv.inventory_space): #checks if the mouse is released on top of any cell of the inventory
                                    for x, cell in enumerate(row):
                                        if cell.hitbox.collidepoint(pygame.mouse.get_pos()):
                                            inv.append(self, (x, y))

                self.is_selected = False
                    
            elif event.type == pygame.MOUSEBUTTONDOWN and hitbox.collidepoint(pygame.mouse.get_pos()): #selects the object
                self.is_selected = True

            if hitbox.collidepoint(pygame.mouse.get_pos()):
                self.is_hovered = True
            else:
                self.is_hovered = False


    def update(self):
        if not self.update_blocked and not self.inventory.update_blocked:
            super().update()

            #binds the object position to it's position in the inventory
            if not self.is_selected and self.inventory_coords:
                self.x = self.inventory.x + self.inventory_coords[0] * (self.inventory.cell_size + self.inventory.cell_spacing) - self.offset
                self.y = self.inventory.y + self.inventory_coords[1] * (self.inventory.cell_size + self.inventory.cell_spacing) + self.inventory.name_padY + self.inventory.name_txt_rect[-1] - self.offset
            else:
                self.x, self.y = pygame.mouse.get_pos()
            
            self.bg_image_rect.topleft = (self.x, self.y)
            self.icon_image_rect.w, self.icon_image_rect.h = (int(self.last_size[0] * 0.7), int(self.last_size[1] * 0.7))
            self.icon_image_rect.center = (self.x + self.last_size[0] // 2, self.y + self.last_size[1] // 2)

            if self.inventory.event_update_blocked:
                self.is_hovered = False
                self.is_selected = False


    def draw(self):
        if not self.draw_blocked and not self.inventory.draw_blocked:
            super().draw()

            if self.inventory or self.is_selected:
                win.blit(pygame.transform.scale(self.bg_image, self.last_size), self.bg_image_rect) #their rects are managed in the update function
                pygame.draw.circle(win, (40, 40, 40), (self.x + self.last_size[0] // 2, self.y + self.last_size[1] // 2), self.last_size[0] // 2.5, width=10)
                icon_bg_col = ((250 * 3 + self.bg_col[0]) // 4,(250 * 3 + self.bg_col[1]) // 4, (250 * 3 + self.bg_col[2]) // 4)
                pygame.draw.circle(win, icon_bg_col, (self.x + self.last_size[0] // 2, self.y + self.last_size[1] // 2), self.last_size[0] // 2.7)
                win.blit(pygame.transform.scale(self.icon_image, (int(self.last_size[0] * 0.7), int(self.last_size[1] * 0.7))), self.icon_image_rect)

            if self.is_hovered and not self.is_selected: #draws a box with the name of the object displayed
                self.name_txt_rect.bottomleft = (pygame.mouse.get_pos()[0] + 20, pygame.mouse.get_pos()[1] - 20)
                pygame.draw.rect(win, (40, 40, 40), (self.name_txt_rect.x - 10, self.name_txt_rect.y - 10, self.name_txt_rect.w + 20, self.name_txt_rect.h + 20))
                win.blit(self.name_txt_obj, self.name_txt_rect)



class InventoryCell(GameObject):
    def __init__(self, inventory, X, Y):
        super().__init__()
        self.inventory = inventory
        self.X = X
        self.Y = Y
        self.object = None

        self.size = self.inventory.cell_size
        self.x = self.inventory.x + (self.size + self.inventory.cell_spacing) * self.X
        self.y = self.inventory.y + (self.size + self.inventory.cell_spacing) * self.Y + self.inventory.name_txt_rect.h + self.inventory.name_padY
        self.hitbox = Rect(self.x - self.inventory.cell_spacing, self.y - self.inventory.cell_spacing, self.size + self.inventory.cell_spacing, self.size + self.inventory.cell_spacing)
        self.image = pygame.transform.scale(pygame.image.load(os.path.join("images", "inventory slot.png")), (self.size, self.size))
        self.image_rect = self.image.get_rect()
        self.image_rect.topleft = (self.x, self.y)
        change_surface_col(self.image, self.inventory.color)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            win.blit(self.image, self.image_rect)



class Inventory(GameObject):
    all_inventories = []
    def __init__(self, name, x, y, lenght, height, cell_size, cell_spacing, color=general_txt_col):
        super().__init__()
        Inventory.all_inventories.append(self)
        self.hidden = False
        
        self.name = name
        self.x = x
        self.y = y
        self.lenght = lenght #lenght and height measured in cell number
        self.height = height
        self.cell_size = cell_size
        self.cell_spacing = cell_spacing
        self.color = color #color of all the gui
        self.name_padY = 40

        self.name_txt_font = pygame.font.Font(general_txt_font, round(self.cell_size / 1.2))
        self.name_txt_obj = self.name_txt_font.render(self.name, True, self.color)
        self.name_txt_rect = self.name_txt_obj.get_rect()
        self.name_txt_rect.topleft = (self.x, self.y)
        self.inventory_space = [[InventoryCell(self, x, y) for x in range(self.lenght)] for y in range(self.height)]


    def append(self, obj, coords=None):
        '''
        Links an inventory object to a cell of the inventory.
        A position may be specified in coords parameter but if omitted the object will be appended in the first free slots available.
        Returns True if the object is successfully appended otherweise returns False.
        '''
        
        def append_at(x, y, cell):
            '''
            Function made to recycle code.
            '''
            if x + obj.inventory_size - 1 < self.lenght and y + obj.inventory_size - 1 < self.height:
                cache_cell_list = [self.inventory_space[y+y_range][x+x_range] for x_range in range(obj.inventory_size) for y_range in range(obj.inventory_size)] #to check if space is clear
                space_clear = True
                for inv_cell in cache_cell_list:
                    if not (inv_cell.object is None or inv_cell.object is obj): #an object can be shifted by 1 or more cells even if technically that space is occupied (by the object itself)
                        space_clear = False
                        break
                if space_clear: #if the object overlaps another it can't be appended in that position
                    obj.inventory.remove(obj)
                    for y_range in range(obj.inventory_size):
                        for x_range in range(obj.inventory_size):
                            self.inventory_space[y + y_range][x + x_range].object = obj #links the object to the cells occupied
                    obj.inventory = self
                    obj.inventory_coords = (x, y)
                    obj.last_size = (self.cell_size * obj.inventory_size + (obj.inventory_size - 1) * self.cell_spacing,) * 2
                    return True
            return False
        
        if coords:
            x, y = coords
            return append_at(x, y, self.inventory_space[y][x])
        else:
            for y, row in enumerate(self.inventory_space):
                for x, cell in enumerate(row):
                    if append_at(x, y, cell):
                        return True
            return False


    def remove(self, obj):
        removed_links = 0
        for y, row in enumerate(self.inventory_space):
            for x, cell in enumerate(row):
                if self.inventory_space[y][x].object is obj:
                    self.inventory_space[y][x].object = None
                    removed_links += 1
        if removed_links == obj.inventory_size ** 2: #checks that the right amount of cells is unlinked
            return True
        else:
            return False


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()

            if not self.hidden:
                win.blit(self.name_txt_obj, self.name_txt_rect)

                pygame.draw.line(win, self.color, #horizontal line
                                 (self.x, self.y+(self.cell_size+self.cell_spacing)*self.height-self.cell_spacing+20+self.name_txt_rect.h+self.name_padY),
                                 (self.x+(self.cell_size+self.cell_spacing)*self.lenght-self.cell_spacing+50, self.y+(self.cell_size+self.cell_spacing)*self.height-self.cell_spacing+20+self.name_txt_rect.h+self.name_padY),
                                 width=4)
                pygame.draw.line(win, self.color, #vertical line
                                 (self.x+(self.cell_size+self.cell_spacing)*self.lenght-self.cell_spacing+20, self.y-20+self.name_txt_rect.h+self.name_padY),
                                 (self.x+(self.cell_size+self.cell_spacing)*self.lenght-self.cell_spacing+20, self.y+(self.cell_size+self.cell_spacing)*self.height-self.cell_spacing+40+self.name_txt_rect.h+self.name_padY),
                                 width=4)

                for row in self.inventory_space:
                    for cell in row:
                        cell.draw()



class PlanetBuildingDisplay(GameObject):
    def __init__(self, building, stack):
        super().__init__()
        self.x = planet_building_display_pos[0]
        self.y = planet_building_display_pos[1]
        self.w = planet_building_display_pos[2]
        self.h = planet_building_display_pos[3]
        self.building = building
        self.stack = stack #a stack menu containing all building details

        self.space_remain_txt_font = pygame.font.Font(general_txt_font, structures_font_size_in_buildings_display)

        self.building_name_font_size = int(88 - len(building.name) * 3) #building name text
        self.building_name_font = pygame.font.Font(general_txt_font, self.building_name_font_size)
        self.building_name_txt_obj = self.building_name_font.render(self.building.name, True, general_txt_col)
        self.building_name_rect = self.building_name_txt_obj.get_rect()
        self.building_name_rect.center = (self.x + self.w // 2, self.y + self.building_name_font_size // 2 + 10)

        caption_font_size = 22 #building caption text
        self.caption_font = pygame.font.Font(general_txt_font, caption_font_size)
        self.caption_txt_obj = self.caption_font.render('building site info', True, general_txt_col)
        self.caption_rect = self.caption_txt_obj.get_rect()
        self.caption_rect.midright = (self.x + self.w, self.y + self.building_name_font_size // 2 + 75)

        self.line2_img = pygame.image.load(os.path.join('images','planet building display line 2.png')) #graphic separator for caption
        self.line2_rect = self.line2_img.get_rect()
        self.line2_rect.topright = (self.x + self.w, self.y + self.building_name_font_size // 2 + 50)

        self.stack_objs_font = pygame.font.Font(general_txt_font, structures_font_size_in_buildings_display) #objects in the stack
        self.stack_objs = []
        self.stack_rects = []
        for i, stack_dict in enumerate(self.stack):
            txt = [key for key in stack_dict.keys()][0] + ": " + str([value for value in stack_dict.values()][0])
            txt_obj = self.stack_objs_font.render(txt, True, general_txt_col)
            txt_rect = txt_obj.get_rect()
            txt_rect.topleft = (self.x + 50,  self.y + 235 + 50 * i)
            self.stack_objs.append(txt_obj)
            self.stack_rects.append(txt_rect)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self, stack):
        if not self.update_blocked:
            super().update()
            self.stack = stack
            self.stack_objs = []
            self.stack_rects = []
            for i, stack_dict in enumerate(self.stack):
                txt = [key for key in stack_dict.keys()][0] + ": " + str([value for value in stack_dict.values()][0])
                txt_obj = self.stack_objs_font.render(txt, True, general_txt_col)
                txt_rect = txt_obj.get_rect()
                txt_rect.topleft = (self.x + 50,  self.y + 235 + 50 * i)
                self.stack_objs.append(txt_obj)
                self.stack_rects.append(txt_rect)


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            #pygame.draw.rect(win, (255,0,0), (self.x, self.y, self.w, self.h)) #just to see the full rectangle in wich the widget is enclosed
            win.blit(self.building_name_txt_obj, self.building_name_rect)
            win.blit(self.caption_txt_obj, self.caption_rect)
            win.blit(self.line2_img, self.line2_rect)
            
            for i, stack_obj in enumerate(self.stack_objs):
                win.blit(stack_obj, self.stack_rects[i])

            space_occupied = [structure.space for structure in self.building.structures]
            space_remain_txt_obj = self.space_remain_txt_font.render("space remaining: "+str(self.building.max_space - sum(space_occupied)), True, general_txt_col)
            space_remain_txt_rect = space_remain_txt_obj.get_rect()
            space_remain_txt_rect.topleft = (self.x + 50, self.y + 450)
            win.blit(space_remain_txt_obj, space_remain_txt_rect)

            

class PlanetVariableTextDisplay(GameObject): #a specific display for stats in the planet data view section of the game
    def __init__(self, planets_dict, x, y, variableX, variable_name, font_size, font=general_txt_font):
        super().__init__()
        self.x = x
        self.y = y
        self.variableX = variableX
        self.font = pygame.font.Font(font, font_size)
        self.planets_dict = planets_dict
        self.variable_name = variable_name
        self.variable_value = planets_dict[current_planet.name][variable_name]

        text1 = self.font.render(variable_name, True, general_txt_col)
        text2 = self.font.render(str(self.variable_value), True, general_txt_col)
        self.var_name_rect = text1.get_rect()
        self.var_value_rect = text2.get_rect()
        self.var_name_rect.topleft = (self.x, self.y)
        self.var_value_rect.topleft = (self.variableX, self.y)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.variable_value = self.planets_dict[current_planet.name][self.variable_name]


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            var_name_text = self.font.render(self.variable_name, True, general_txt_col)
            var_value_text = self.font.render(str(self.variable_value)+" "+unit_measurements[self.variable_name], True, general_txt_col)
            win.blit(var_name_text, self.var_name_rect)
            win.blit(var_value_text, self.var_value_rect)



#NOTE: the structures are managed in the InfoDisplay classes
class Colony(PlanetBuilding):
    def __init__(self, view_structure_button, name, x, y, txt_x, txt_y, font_size=planet_buildings_menu_font_size, color=general_txt_col):
        super().__init__(view_structure_button, name, x, y, txt_x, txt_y, font_size, color)
        self.info_display = None

        self.basic_personnel = 0
        self.trained_personnel = 0
        self.specific_personnel = 0
        self.astronauts = 0

        self.launch_site_cost = 1500
        self.laboratory_cost = 3000
        self.temperature_net_cost = 8000000
        self.pressure_net_cost = 10500000

        self.initial_space = 3 #when the colony is created it has a default space
        self.max_space = self.initial_space #the actual space available
        self.base_space_cost = 1000 #cost to add building space
        self.space_cost_multiplier = 1.3 #the more space is purchased the more it costs

        self.building_display = PlanetBuildingDisplay(self, [{"basic personnel": self.basic_personnel}, #what is displayed in the scene planet view / main when a building is selected
                                                             {"trained personnel": self.trained_personnel},
                                                             {"specific personnel": self.specific_personnel},
                                                             {"astronauts": self.astronauts}])


    def deselect(self):
        super().deselect()

            
    def select(self):
        global menus
        if selected_build_menu == menus["add colony menu"]:
            super().select()


    def change_position(self, amount):
        super().change_position(amount)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.hitbox.collidepoint(event.pos):
                    if not self.is_selected:
                        self.select()
                    else:
                        self.deselect()

            self.building_display.event_update(event)
            self.view_structure_button.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.building_display.update([{"basic personnel": self.basic_personnel},
                                          {"trained personnel": self.trained_personnel},
                                          {"specific personnel": self.specific_personnel}])
            self.view_structure_button.update()


    def draw(self):
        if not self.draw_blocked:
            super().draw
            global selected_build_menu, menus
                
            if selected_build_menu == menus["add colony menu"]:
                if self.y >= planet_buildings_menus_default_y:               
                    cur_txt_col = self.color
                    if not self.is_selected:
                        if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                            cur_txt_col = (self.color[0]+hover_delta_col,self.color[1]+hover_delta_col,self.color[2]+hover_delta_col)
                            if self.name:
                                new_text_obj = self.txt_font.render(self.name, True, cur_txt_col)
                                win.blit(new_text_obj, self.txt_rect)
                        else:
                            if self.name:
                                win.blit(self.txt_object, self.txt_rect)
                    else:
                        if self.name:
                            win.blit(self.txt_object, self.txt_rect)
                            
                            self.building_display.draw()
                            self.view_structure_button.draw()
                            
                    pygame.draw.rect(win, cur_txt_col,
                                     (self.x, self.y, planet_buildings_menus_squares_width, planet_buildings_menus_squares_height),
                                     border_radius=20, width=5)



class City(PlanetBuilding):
    def __init__(self, view_structure_button, name, x, y, txt_x, txt_y, font_size=planet_buildings_menu_font_size, color=general_txt_col):
        super().__init__(view_structure_button, name, x, y, txt_x, txt_y, font_size, color)
        self.info_display = None

        self.population = 0
        self.habitations = 0
        self.economic_growth = 0

        self.residential_zone_cost = 2250
        self.space_port_cost = 1500000

        self.initial_space = 6
        self.max_space = self.initial_space
        self.base_space_cost = 1000
        self.space_cost_multiplier = 1.3

        self.building_display = PlanetBuildingDisplay(self, [{"population":self.population},
                                                             {"habitations":self.habitations},
                                                             {"economic growth":self.economic_growth}])


    def deselect(self):
        super().deselect()

            
    def select(self):
        global menus
        if selected_build_menu == menus["add city menu"]:
            super().select()


    def change_position(self, amount):
        super().change_position(amount)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.hitbox.collidepoint(event.pos):
                    if not self.is_selected:
                        self.select()
                    else:
                        self.deselect()

            self.building_display.event_update(event)
            self.view_structure_button.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.building_display.update([{"population":self.population},
                                          {"habitations":self.habitations},
                                          {"economic growth":self.economic_growth}])
            self.view_structure_button.update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            global selected_build_menu, menus
                
            if selected_build_menu == menus["add city menu"]:
                if self.y >= planet_buildings_menus_default_y:
                    cur_txt_col = self.color
                    if not self.is_selected:
                        if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                            cur_txt_col = (self.color[0]+hover_delta_col,self.color[1]+hover_delta_col,self.color[2]+hover_delta_col)
                            if self.name:
                                new_text_obj = self.txt_font.render(self.name, True, cur_txt_col)
                                win.blit(new_text_obj, self.txt_rect)
                        else:
                            if self.name:
                                win.blit(self.txt_object, self.txt_rect)
                    else:
                        if self.name:
                            win.blit(self.txt_object, self.txt_rect)
                            
                        self.building_display.draw()
                        self.view_structure_button.draw()
                        
                    pygame.draw.rect(win, cur_txt_col,
                                     (self.x, self.y, planet_buildings_menus_squares_width, planet_buildings_menus_squares_height),
                                     border_radius=20, width=5)



class IndustrialZone(PlanetBuilding):
    def __init__(self, view_structure_button, name, x, y, txt_x, txt_y, font_size=planet_buildings_menu_font_size, color=general_txt_col):
        super().__init__(view_structure_button, name, x, y, txt_x, txt_y, font_size, color)
        self.info_display = None

        self.basic_personnel = 0
        self.trained_personnel = 0
        self.specific_personnel = 0

        self.initial_space = 3
        self.max_space = self.initial_space
        self.base_space_cost = 1000
        self.space_cost_multiplier = 1.3

        self.building_display = PlanetBuildingDisplay(self, [{"basic personnel": self.basic_personnel},
                                                             {"trained personnel": self.trained_personnel},
                                                             {"specific personnel": self.specific_personnel}])


    def deselect(self):
        super().deselect()


    def select(self):
        global menus
        if selected_build_menu == menus["add industrial zone menu"]:
            super().select()


    def change_position(self, amount):
        super().change_position(amount)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.hitbox.collidepoint(event.pos):
                    if not self.is_selected:
                        self.select()
                    else:
                        self.deselect()

            self.building_display.event_update(event)
            self.view_structure_button.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.building_display.update([{"basic personnel": self.basic_personnel},
                                          {"trained personnel": self.trained_personnel},
                                          {"specific personnel": self.specific_personnel}])
            self.view_structure_button.update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            global selected_build_menu, menus
                
            if selected_build_menu == menus["add industrial zone menu"]:
                if self.y >= planet_buildings_menus_default_y:
                    cur_txt_col = self.color
                    if not self.is_selected:
                        if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                            cur_txt_col = (self.color[0]+hover_delta_col,self.color[1]+hover_delta_col,self.color[2]+hover_delta_col)
                            if self.name:
                                new_text_obj = self.txt_font.render(self.name, True, cur_txt_col)
                                win.blit(new_text_obj, self.txt_rect)
                        else:
                            if self.name:
                                win.blit(self.txt_object, self.txt_rect)
                    else:
                        if self.name:
                            win.blit(self.txt_object, self.txt_rect)

                            self.building_display.draw()
                            self.view_structure_button.draw()
                            
                    pygame.draw.rect(win, cur_txt_col,
                                     (self.x, self.y, planet_buildings_menus_squares_width, planet_buildings_menus_squares_height),
                                     border_radius=20, width=5)



class Base(PlanetBuilding):
    def __init__(self, view_structure_button, name, x, y, txt_x, txt_y, font_size=planet_buildings_menu_font_size, color=general_txt_col):
        super().__init__(view_structure_button, name, x, y, txt_x, txt_y, font_size, color)
        self.info_display = None

        self.basic_personnel = 0
        self.trained_personnel = 0
        self.specific_personnel = 0
        self.astronauts = 0

        self.earth_launch_site_cost = 800

        self.initial_space = 2
        self.max_space = self.initial_space
        self.base_space_cost = 10000
        self.space_cost_multiplier = 1.1

        self.building_display = PlanetBuildingDisplay(self, [{"basic personnel": self.basic_personnel}, #what is displayed in the scene planet view / main when a building is selected
                                                             {"trained personnel": self.trained_personnel},
                                                             {"specific personnel": self.specific_personnel},
                                                             {"astronauts": self.astronauts}])


    def deselect(self):
        super().deselect()

            
    def select(self):
        global menus
        if selected_build_menu == menus["add base menu"]:
            super().select()


    def change_position(self, amount):
        super().change_position(amount)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.hitbox.collidepoint(event.pos):
                    if not self.is_selected:
                        self.select()
                    else:
                        self.deselect()

            self.building_display.event_update(event)
            self.view_structure_button.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.building_display.update([{"basic personnel": self.basic_personnel},
                                          {"trained personnel": self.trained_personnel},
                                          {"specific personnel": self.specific_personnel},
                                          {"astronauts": self.astronauts}])
            self.view_structure_button.update()


    def draw(self):
        if not self.draw_blocked:
            super().draw
            global selected_build_menu, menus
                
            if selected_build_menu == menus["add base menu"]:
                if self.y >= planet_buildings_menus_default_y:               
                    cur_txt_col = self.color
                    if not self.is_selected:
                        if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                            cur_txt_col = (self.color[0]+hover_delta_col,self.color[1]+hover_delta_col,self.color[2]+hover_delta_col)
                            if self.name:
                                new_text_obj = self.txt_font.render(self.name, True, cur_txt_col)
                                win.blit(new_text_obj, self.txt_rect)
                        else:
                            if self.name:
                                win.blit(self.txt_object, self.txt_rect)
                    else:
                        if self.name:
                            win.blit(self.txt_object, self.txt_rect)
                            
                            self.building_display.draw()
                            self.view_structure_button.draw()
                            
                    pygame.draw.rect(win, cur_txt_col,
                                     (self.x, self.y, planet_buildings_menus_squares_width, planet_buildings_menus_squares_height),
                                     border_radius=20, width=5)



class InputBox(GameObject): #a pop up menu containing just 1 input entry
    def __init__(self, x, y, w, font, font_size, color=pop_up_menus_txt_col, max_txt_lenght=15, caption_text=""):
        super().__init__()
        global text_inputs
        
        self.x = x
        self.y = y
        self.w = w
        self.font = pygame.font.Font(font, font_size)
        self.caption_font = pygame.font.Font(font, font_size // 2)
        self.color = color
        rect = self.font.render("temp", True, self.color).get_rect() #temporary text to set the size of the box
        self.h = rect[-1]
        self.text = ""
        self.caption_text = caption_text #fixed caption on top of the input field
            
        manager = pygame_textinput.TextInputManager(validator = lambda inp: len(inp) <= max_txt_lenght)
        self.textinput = pygame_textinput.TextInputVisualizer(manager=manager, font_object=self.font)
        self.textinput.cursor_width = 4
        self.textinput.font_color = self.color
        self.textinput.cursor_color = self.color
        text_inputs.append(self.textinput)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.text = self.textinput.value
            self.textinput.font_color = self.color
            self.textinput.cursor_color = self.color


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            pygame.draw.rect(win, pop_up_menus_bg_col, (self.x, self.y, self.w + 80, self.h * 1.5 + 120), border_radius=10)
            pygame.draw.rect(win, self.color, (self.x, self.y, self.w + 80, self.h * 1.5 + 120), border_radius=10, width=5)
            win.blit(self.caption_font.render(self.caption_text, True, self.color), (self.x + 40, self.y + 20))
            win.blit(self.textinput.surface, (self.x + 40, self.y + 60 + self.h // 2))



#NOTE: The menus haven't got any system to handle the precedence between many of them nor to hide if more menus are shown except for the inputbox system. It all must be done manually.
class BasicPopUpMenu(GameObject):
    def __init__(self,
                 options,
                 x, y,
                 font_size = 20,
                 padX = 10, padY = 10, unit_pad = 5,
                 font = pop_up_menus_txt_font,
                 align = "left",
                 hover_opt_col_mode = "negative",
                 has_bg = True,
                 facing = "vertical",
                 select_opt_mode = "on hover",
                 input_box_font_size = 50
                 ):
        super().__init__()
        self.hidden = False #wether the menu is seen (useful to suppress the draw function and some parts of the others update functions)
        self.has_bg = has_bg
        self.facing = facing #wether options are displayed one under the other or one next to the other
        self.active_input_field = None #if the text input of the user is registered in this menu and where it registers (if there are more fields)
        #take in consideration that input fields won't work if the selected option mode of the menu is set to fixed
        self.input_box = InputBox(0, cur_win_size[1] // 2 - 200, 600, font, input_box_font_size)
        self.input_box.x = cur_win_size[0] // 2 - (self.input_box.w + 40) // 2 #centers the box
        self.draw_input_box = False
        self.input_box_font_size = input_box_font_size
        self.x = x
        self.y = y
        self.padX = padX #padding of all the options from the top left corner
        self.padY = padY
        self.unit_pad = unit_pad #padding between each option
        self.options = options #data structure containing infos for option text displays, option types
                               #(like button, slider...), additional padding, functions and colors
        self.txt_font = pygame.font.Font(font, font_size)
        self.hover_opt_col_mode = hover_opt_col_mode #if the color of the hovered option is brighter or darker
        self.select_opt_mode = select_opt_mode #if the menu is in fixed mode one option will always be selected
        self.align = align
        self.facing = facing

        #used just in copy()
        self.font_size = font_size
        self.font = font

        if select_opt_mode != "on hover" and select_opt_mode != "fixed":
            raise ValueError("selected option mode passed must be either 'on hover' or 'fixed'")
        self.selected_opt_i = 0 #only if the selected option mode is fixed

        if self.options:
            self.colors = [option["color"] for option in self.options]
            self.txts = [self.txt_font.render(option["text"], True, self.colors[i]) for i, option in enumerate(self.options)] #contains the text objects of every option
            self.txts_rect = [txt.get_rect() for txt in self.txts] #buffer for rect calculation
            self.txts_max_width = max([rect[-2] for rect in self.txts_rect]) #the width of the longest text rect
            self.additional_paddings = [option["additional padding"] for option in self.options]
        else:
            self.colors = []
            self.txts = []
            self.txts_rect = []
            self.txts_max_width = 0
            self.additional_paddings = 0

        if facing != "vertical" and facing != "horizontal":
            raise ValueError("facing passed must be either 'horizontal' or 'vertical'")
        
        if facing == "vertical":
            if align == "right":
                for i, txt in enumerate(self.txts): #adjusts the text positions so they are aligned left
                    additional_padding = self.additional_paddings[i]
                    for j in range(0, i):
                        additional_padding += self.additional_paddings[j]
                    x = self.x + self.padX + self.txts_max_width
                    y = self.y + self.padY + additional_padding + (self.unit_pad + self.txts_rect[i][-1]) * i
                    rect = self.txts_rect[i]
                    rect.topright = (x, y)
                    
            elif align == "center":
                for i, txt in enumerate(self.txts): #adjusts the text positions so they are centered
                    additional_padding = self.additional_paddings[i]
                    for j in range(0, i):
                        additional_padding += self.additional_paddings[j]
                    x = self.x + self.padX + self.txts_max_width // 2
                    y = self.y + self.padY + additional_padding + (self.unit_pad + self.txts_rect[i][-1]) * i + self.txts_rect[i][-1] // 2
                    rect = self.txts_rect[i]
                    rect.center = (x, y)
            
            elif align == "left":
                for i, txt in enumerate(self.txts): #adjusts the text positions so they are aligned right
                    additional_padding = self.additional_paddings[i]
                    for j in range(0, i):
                        additional_padding += self.additional_paddings[j]
                    x = self.x + self.padX
                    y = self.y + self.padY + additional_padding + (self.unit_pad + self.txts_rect[i][-1]) * i
                    rect = self.txts_rect[i]
                    rect.topleft = (x, y)

            else:
                raise ValueError("alignment passed is not defined")
        else:
            for i, txt in enumerate(self.txts): #adjusts the position of the rects if the menu is horizontal
                additional_padding = self.additional_paddings[i]
                for j in range(0, i):
                    additional_padding += self.additional_paddings[j]
                current_total_rects_w = sum([rect[-2] for rect in self.txts_rect[:i]])
                y = self.y + padY * 1.5 + self.txts_rect[i][-1] // 2
                x = self.x + self.padX * 1.5 + additional_padding + current_total_rects_w + self.unit_pad * i + self.txts_rect[i][-2] // 2
                self.txts_rect[i].center = (x, y)


    def copy(self):
        return BasicPopUpMenu(copy.deepcopy(self.options),
                              self.x, self.y,
                              self.font_size,
                              self.padX, self.padY, self.unit_pad,
                              self.font,
                              self.align,
                              self.hover_opt_col_mode,
                              self.has_bg,
                              self.facing,
                              self.select_opt_mode,
                              self.input_box_font_size)


    def change_options(self, new_options):
        if new_options:
            self.options = new_options
            self.colors = [option["color"] for option in self.options]
            self.txts = [self.txt_font.render(option["text"], True, self.colors[i]) for i, option in enumerate(self.options)]
            self.txts_rect = [txt.get_rect() for txt in self.txts]
            self.txts_max_width = max([rect[-2] for rect in self.txts_rect])
            self.additional_paddings = [option["additional padding"] for option in self.options]
        else:
            self.colors = []
            self.txts = []
            self.txts_rect = []
            self.txts_max_width = 0
            self.additional_paddings = 0
        
        if self.facing == "vertical":
            if self.align == "right":
                for i, txt in enumerate(self.txts):
                    additional_padding = self.additional_paddings[i]
                    for j in range(0, i):
                        additional_padding += self.additional_paddings[j]
                    x = self.x + self.padX + self.txts_max_width
                    y = self.y + self.padY + additional_padding + (self.unit_pad + self.txts_rect[i][-1]) * i
                    rect = self.txts_rect[i]
                    rect.topright = (x, y)
                    
            elif self.align == "center":
                for i, txt in enumerate(self.txts):
                    additional_padding = self.additional_paddings[i]
                    for j in range(0, i):
                        additional_padding += self.additional_paddings[j]
                    x = self.x + self.padX + self.txts_max_width // 2
                    y = self.y + self.padY + additional_padding + (self.unit_pad + self.txts_rect[i][-1]) * i + self.txts_rect[i][-1] // 2
                    rect = self.txts_rect[i]
                    rect.center = (x, y)
            
            elif self.align == "left":
                for i, txt in enumerate(self.txts):
                    additional_padding = self.additional_paddings[i]
                    for j in range(0, i):
                        additional_padding += self.additional_paddings[j]
                    x = self.x + self.padX
                    y = self.y + self.padY + additional_padding + (self.unit_pad + self.txts_rect[i][-1]) * i
                    rect = self.txts_rect[i]
                    rect.topleft = (x, y)
        else:
            for i, txt in enumerate(self.txts):
                additional_padding = self.additional_paddings[i]
                for j in range(0, i):
                    additional_padding += self.additional_paddings[j]
                current_total_rects_w = sum([rect[-2] for rect in self.txts_rect[:i]])
                y = self.y + padY * 1.5 + self.txts_rect[i][-1] // 2
                x = self.x + self.padX * 1.5 + additional_padding + current_total_rects_w + self.unit_pad * i + self.txts_rect[i][-2] // 2
                self.txts_rect[i].center = (x, y)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            global set_active_inp_field
            
            if not self.hidden:
                if self.select_opt_mode == "on hover":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        an_option_is_selected = False
                        
                        for i, rect in enumerate(self.txts_rect): #when an option is clicked
                            if rect.collidepoint(event.pos):
                                an_option_is_selected = True
                                if self.options[i]["option type"] != "text": #does different things depending of the type of option
                                    
                                    if self.options[i]["option type"] == "button":
                                        set_active_inp_field(self, None)
                                        self.draw_input_box = False
                                        self.options[i]["function"]()
                                        
                                    elif self.options[i]["option type"] == "input field":
                                        set_active_inp_field(self, i)
                                        self.draw_input_box = True
                                        self.input_box.color = self.colors[i]
                                        self.input_box.caption_text = self.options[i]["caption"]
                                        
                        if not an_option_is_selected: #doesn't display any input box
                            set_active_inp_field(self, None)
                            self.draw_input_box = False

                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: #the text in the input field is sent
                        if self.active_input_field != None:
                            self.options[self.active_input_field]["function"](self.input_box.text)
                            if self.options[self.active_input_field]["close after enter key"]:
                                set_active_inp_field(self, None)
                                self.draw_input_box = False


    def update(self, update_func=None):
        if not self.update_blocked:
            super().update()
            if self.hidden:
                self.draw_input_box = False
            if self.draw_input_box == True:
                self.input_box.update()
            
            if self.select_opt_mode == "fixed" and selected_menu == self:
                
                if keys[pygame.K_RIGHT]:
                    if "K_RIGHT" not in key_cooldown: #scrolls between options
                        if current_scene == "planet view / main" and not current_planet.name == "earth":
                            while True: #keeps going till it finds an option
                                self.selected_opt_i += 1
                                if self.selected_opt_i >= len(self.options):
                                    self.selected_opt_i = 0
                                key_cooldown["K_RIGHT"] = time.time()
                                if len([option["option type"] for i,option in enumerate(self.options) if option["option type"] != "text"]) != len(self.options):
                                    if self.options[self.selected_opt_i]["option type"] == "text": #only if it's not a menu composed by just text elements
                                        continue
                                self.options[self.selected_opt_i]["function"]()
                                break
                        
                if keys[pygame.K_LEFT]: #same but other way round
                    if "K_LEFT" not in key_cooldown:
                        if current_scene == "planet view / main" and not current_planet.name == "earth":
                            while True:
                                self.selected_opt_i -= 1
                                if self.selected_opt_i < 0:
                                    self.selected_opt_i = len(self.options) - 1
                                key_cooldown["K_LEFT"] = time.time()
                                if len([option["option type"] for i,option in enumerate(self.options) if option["option type"] != "text"]) != len(self.options):
                                    if self.options[self.selected_opt_i]["option type"] == "text":
                                        continue
                                self.options[self.selected_opt_i]["function"]()
                                break

            if update_func:
                update_func()

    
    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if not self.hidden:
                txts_hight = sum([rect[-1] for rect in self.txts_rect]) + self.unit_pad * len(self.txts) #for vertical menus
                txts_width = sum([rect[-2] for rect in self.txts_rect]) + self.unit_pad * len(self.txts) #for horizontal menus
                if self.has_bg: #draws the menu background
                    if self.facing == "vertical":
                        pygame.draw.rect(win,
                                         pop_up_menus_bg_col,
                                         (self.x,self.y,self.txts_max_width+self.padX*2,txts_hight+self.padY*2+sum(self.additional_paddings)),
                                         border_radius=10)
                    else:
                        pygame.draw.rect(win,
                                         pop_up_menus_bg_col,
                                         (self.x,self.y,txts_width+self.padX*2+sum(self.additional_paddings),self.txts_rect[0][-1]+self.padY*2),
                                         border_radius=10)
                
                for i, txt in enumerate(self.txts): #draws every text render
                    #if the option is hovered or is selected change color
                    if self.options[i]["option type"] != "text": #if the option is a text it must not change when hovered
                        if (self.txts_rect[i].collidepoint(pygame.mouse.get_pos()) and self.select_opt_mode == "on hover") or (self.selected_opt_i == i and self.select_opt_mode == "fixed"):                    
                            if self.hover_opt_col_mode == "negative":
                                new_txt = self.txt_font.render(self.options[i]["text"], True,
                                                               (self.colors[i][0]-hover_delta_col,self.colors[i][1]-hover_delta_col,self.colors[i][2]-hover_delta_col))
                            elif self.hover_opt_col_mode == "positive":
                                new_txt = self.txt_font.render(self.options[i]["text"], True,
                                                               (self.colors[i][0]+hover_delta_col,self.colors[i][1]+hover_delta_col,self.colors[i][2]+hover_delta_col))
                            else:
                                raise ValueError("hovered color mode passed is not defined")
                            win.blit(new_txt, self.txts_rect[i])

                            if self.hover_opt_col_mode == "negative": #draws the underline if the option is hovered
                                pygame.draw.rect(win,
                                                 (self.colors[i][0]-hover_delta_col,self.colors[i][1]-hover_delta_col,self.colors[i][2]-hover_delta_col),
                                                 (self.txts_rect[i][0]-5,self.txts_rect[i][1]+self.txts_rect[i][-1],self.txts_rect[i][-2]+10,5))
                            elif self.hover_opt_col_mode == "positive":
                                pygame.draw.rect(win,
                                                 (self.colors[i][0]+hover_delta_col,self.colors[i][1]+hover_delta_col,self.colors[i][2]+hover_delta_col),
                                                 (self.txts_rect[i][0]-5,self.txts_rect[i][1]+self.txts_rect[i][-1],self.txts_rect[i][-2]+10,5))
                            else:
                                raise ValueError("hovered color mode passed is not defined")
                        else:
                            win.blit(txt, self.txts_rect[i])
                    else:
                        win.blit(txt, self.txts_rect[i])
                if self.draw_input_box:
                    self.input_box.draw()



class ScrollDownMenuTextOption(GameObject):
    def __init__(self, menu, text, function, pyfont, color, hover_col, hitbox_size_shift=0):
        super().__init__()
        self.menu = menu
        self.text = text
        self.function = function
        self.pyfont = pyfont
        self.color = color
        self.hover_col = hover_col
        self.hitbox_size_shift = hitbox_size_shift

        self.is_hovered = False
        self.x, self.y = self.menu.x + self.menu.shift[0], self.menu.y
        self.txt_obj = self.pyfont.render(self.text, True, self.color)
        self.hovered_txt_obj = self.pyfont.render(self.text, True, self.hover_col)
        self.txt_rect = self.txt_obj.get_rect()
        self.hitbox_rect = Rect(0, 0, self.txt_rect.w + self.hitbox_size_shift * 2, self.txt_rect.h + self.hitbox_size_shift * 2)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if self.hitbox_rect.collidepoint(pygame.mouse.get_pos()):
                self.is_hovered = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.function()
            else:
                self.is_hovered = False


    def update(self):
        if not self.update_blocked:
            super().update()
            self.txt_rect.topleft = (self.x, self.y)
            self.hitbox_rect.topleft = (self.x - self.hitbox_size_shift, self.y - self.hitbox_size_shift)


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if self.is_hovered:
                win.blit(self.hovered_txt_obj, self.txt_rect)
            else:
                win.blit(self.txt_obj, self.txt_rect)



class ScrollDownMenu(GameObject):
    def __init__(self, options, x, y, padding, direction, shift : tuple, config_options : dict):
        super().__init__()
        self.is_expanded = False
        self.head_hovered = False
        
        self.options = options #options list must contain tuples of type (option text, option function) except option 0 which is just (option text,)
        if len(self.options) < 2:
            raise GameException("scrolldown menus cannot have 1 or less options")
        self.functions = [option[1] for option in self.options[1:]]
        self.x = x
        self.y = y
        self.padding = padding #between each option
        self.direction = direction #in which direction expand the options
        self.shift = shift #shift from option 0
        self.config_options = config_options
        '''
        config options must be like (# means they can be omitted):
        
        for type text
        
        {"type": text,
         "font": font,
         "font size": size,
         "color": color, #
         "hover opt col mode": positive/negative, #
         "options hitbox size shift": int #
        }
        '''
        
        if self.config_options["type"] == "text":
            self.font = pygame.font.Font(self.config_options["font"], self.config_options["font size"])
            if "color" in self.config_options:
                color = self.config_options["color"]
            else:
                color = general_txt_col
            if "hover opt col mode" in self.config_options:
                self.hover_opt_col_mode = self.config_options["hover opt col mode"]
            else:
                self.hover_opt_col_mode = "positive"
            if "options hitbox size shift" in self.config_options:
                self.options_hitbox_size_shift = self.config_options["options hitbox size shift"]
            else:
                self.options_hitbox_size_shift = 0

            self.texts = [option[0] for option in self.options[1:]]
            if self.hover_opt_col_mode == "positive":
                hover_col = iter_operation(color, r'+', hover_delta_col)
            elif self.hover_opt_col_mode == "negative":
                hover_col = iter_operation(color, r'-', hover_delta_col)

            self.head_txt_obj = self.font.render(self.options[0][0], True, color)
            self.hovered_head_txt_obj = self.font.render(self.options[0][0], True, hover_col)
            self.head_txt_rect = self.head_txt_obj.get_rect()
            self.head_txt_rect.topleft = (self.x, self.y)

            self.menu_opts = [ScrollDownMenuTextOption(self, text, function, self.font, color, hover_col, self.options_hitbox_size_shift) for text, function in zip(self.texts, self.functions)]

            self.extended_opt_pos = []
            for i, option in enumerate(self.menu_opts):
                if self.direction == "down":
                    self.extended_opt_pos.append([self.x + self.shift[0], self.y + self.shift[1] + (option.txt_rect.h + self.padding) * (i + 1)])
                elif self.direction == "up":
                    self.extended_opt_pos.append([self.x + self.shift[0], self.y + self.shift[1] - (option.txt_rect.h + self.padding) * (i + 1)])

            self.options_anim_group = MoveAnimationGroup(objectives=self.extended_opt_pos, speed=5, back_n_fourth=False)
            for option in self.menu_opts:
                self.options_anim_group.append(option)


    def copy(self):
        return ScrollDownMenu(self.options, self.x, self.y, self.padding, self.direction, self.shift, self.config_options)


    def expand(self):
        if self.is_expanded:
            self.is_expanded = False
            for option in self.menu_opts:
                option.x, option.y = self.x + self.shift[0], self.y #option return to the initial position before disappearing to restart the animation
        else:
            self.is_expanded = True
            self.options_anim_group.begin(True)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            mouse_pos = pygame.mouse.get_pos()

            if self.config_options["type"] == "text":
                if self.head_txt_rect.collidepoint(mouse_pos):
                    self.head_hovered = True
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.expand()
                else:
                    self.head_hovered = False

            if self.is_expanded:
                for option in self.menu_opts:
                    option.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            self.options_anim_group.animation_update()
            for option in self.menu_opts:
                option.update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if self.config_options["type"] == "text":
                if self.head_hovered:
                    win.blit(self.hovered_head_txt_obj, self.head_txt_rect)
                else:
                    win.blit(self.head_txt_obj, self.head_txt_rect)

            if self.is_expanded:
                for option in self.menu_opts:
                    option.draw()



class ImageMenu(GameObject):
    def __init__(self, options, x, y, w, padX, padY, has_borders=False, border_config=(general_txt_col, 8, True, "positive", hover_delta_col), image_scale=None, save_last_selection=False):
        super().__init__()
        self.hidden = False
        self.hovered_i = None
        self.last_selected_i = None
        self.options = options #must be of the type [(fuction, image_name), ...]
        self.x, self.y, self.w = x, y, w
        self.padX, self.padY = padX, padY
        self.has_borders = has_borders
        self.border_col = border_config[0]
        self.border_width = border_config[1]
        self.draw_all_borders = border_config[2]
        if len(border_config) > 4: #sets the color of the border of an hovered option
            if border_config[3] == "positive": #border_config[3] in this case is the usual hover_delta_col parameter
                self.hover_col = iter_operation(self.border_col, r'+', border_config[4])
            elif border_config[3] == "negative":
                self.hover_col = iter_operation(self.border_col, r'-', border_config[4])
        else: #instead of specifying the hover_delta_col and the delta parameter you can directly specify the hover color
            self.hover_col = border_config[3]
        self.image_scale = image_scale
        self.save_last_selection = save_last_selection #last option selected keeps the border until another is selected if the borders are active

        self.functions = [option[0] for option in self.options]
        if self.image_scale:
            self.images = [pygame.transform.scale(pygame.image.load(os.path.join("images", option[1])), self.image_scale) for option in self.options]
        else:
            self.images = [pygame.image.load(os.path.join("images", option[1])) for option in self.options]
        self.rects_matrix = [] #saves the rect in a matrix representing the columns and rows of the image menu itself
        row = []
        for i, img in enumerate(self.images):
            rect = img.get_rect()
            if sum([rect.w for rect in row]) + rect.w > self.w - 1:
                self.rects_matrix.append(row)
                row = []
            rectX = self.x + sum([rect.w + padX for rect in row])
            rectY = self.y + sum([self.rects_matrix[ind][len(row)].h + padY for ind, r in enumerate(self.rects_matrix) if len(row) < len(r)])
            rect.topleft = (rectX, rectY)
            row.append(rect)
        self.rects_matrix.append(row)
        self.rects = [] #all the rects in a list for easy access
        for rect in self.rects_matrix:
            self.rects += rect


    def copy(self):
        return ImageMenu(self.options,
                         self.x, self.y, self.w, self.padX, self.padY,
                         self.has_borders, self.border_config, self.image_scale, self.save_last_selection)


    def change_options(self, new_options):
        self.options = new_options
        self.functions = [option[0] for option in self.options]
        if self.image_scale:
            self.images = [pygame.transform.scale(pygame.image.load(os.path.join("images", option[1])), self.image_scale) for option in self.options]
        else:
            self.images = [pygame.image.load(os.path.join("images", option[1])) for option in self.options]
        self.rects_matrix = []
        row = []
        for i, img in enumerate(self.images):
            rect = img.get_rect()
            if sum([rect.w for rect in row]) + rect.w > self.w - 1:
                self.rects_matrix.append(row)
                row = []
            rectX = self.x + sum([rect.w + self.padX for rect in row])
            rectY = self.y + sum([self.rects_matrix[ind][len(row)].h + self.padY for ind, r in enumerate(self.rects_matrix) if len(row) < len(r)])
            rect.topleft = (rectX, rectY)
            row.append(rect)
        self.rects_matrix.append(row)
        self.rects = []
        for rect in self.rects_matrix:
            self.rects += rect


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            option_selected = False
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(pygame.mouse.get_pos()):
                    option_selected = True
                    self.hovered_i = i
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.functions[i]()
                        if self.save_last_selection:
                            self.last_selected_i = i #saves the position of the last object selected
                    break
            if not option_selected:
                self.hovered_i = None


    def update(self):
        if not self.update_blocked:
            super().update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            for img, rect in zip(self.images, self.rects):
                win.blit(img, rect)
                i = self.rects.index(rect)
                if self.has_borders:
                    if self.draw_all_borders:
                        if i == self.hovered_i or i == self.last_selected_i: #if the option is hovered draw the border of the hover color
                            pygame.draw.rect(win, self.hover_col,
                                             (rect.x - self.border_width, rect.y - self.border_width, rect.w + self.border_width * 2, rect.h + self.border_width * 2),
                                             width=self.border_width, border_radius=10)
                        else:
                            pygame.draw.rect(win, self.border_col,
                                             (rect.x - self.border_width, rect.y - self.border_width, rect.w + self.border_width * 2, rect.h + self.border_width * 2),
                                             width=self.border_width, border_radius=10)
                    else:
                        if i == self.hovered_i or i == self.last_selected_i: #if the option is hovered draw a border around it
                            pygame.draw.rect(win, self.border_col,
                                             (rect.x - self.border_width, rect.y - self.border_width, rect.w + self.border_width * 2, rect.h + self.border_width * 2),
                                             width=self.border_width, border_radius=10)
    



class TextButton(GameObject):
    def __init__(self,function,
                 x, y, w, h,
                 hitbox_x, hitbox_y, hitbox_w, hitbox_h,
                 text=None,
                 font=general_txt_font, font_size=30, txt_col=general_txt_col,
                 has_box=False,
                 fix="center",
                 hover_opt_col_mode="positive"):
        super().__init__()
        self.function = function #function called when the button is clicked
        self.hidden = False
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hitbox = Rect(hitbox_x, hitbox_y, hitbox_w, hitbox_h) #hitbox to register the clicks
        self.text = text
        self.has_box = has_box #wether to draw a box around the button the same color as the text
        self.fix = fix
        self.hover_opt_col_mode = hover_opt_col_mode #if the color of the hovered option is brighter or darker

        if text:
            self.txt_col = txt_col
            self.txt_font = pygame.font.Font(font, font_size)
            self.txt_object = self.txt_font.render(self.text, True, txt_col)
            self.txt_rect = self.txt_object.get_rect()
            if fix == "center":
                self.txt_rect.center = (self.x + self.w // 2, self.y + self.h // 2)
            elif fix == "topleft":
                self.txt_rect.topleft = (self.x, self.y)


    def change_pos(self, new_coords : tuple):
        self.x = new_coords[0]
        self.y = new_coords[1]
        self.w = new_coords[2]
        self.h = new_coords[3]

        if self.text:
            if self.fix == "center":
                self.txt_rect.center = (self.x + self.w // 2, self.y + self.h // 2)
            elif self.fix == "topleft": #if the button has a box the coordinates given must reference the box and not the text
                if not self.has_box:
                    self.txt_rect.topleft = (self.x, self.y)
                else:
                    self.txt_rect.center = (self.x + self.w // 2, self.y + self.h // 2)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if not self.hidden:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hitbox.collidepoint(event.pos): #the button is pressed
                        self.function()

                        
    def update(self, update_func=None):
        if not self.update_blocked:
            super().update()
            if update_func:
                update_func()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if not self.hidden:
                #pygame.draw.rect(win, (255,0,0), (self.x, self.y, self.w, self.h))
                cur_txt_col = self.txt_col
                if self.hitbox.collidepoint(pygame.mouse.get_pos()): #if the button is hovered change color
                    if self.hover_opt_col_mode == "negative":
                        cur_txt_col = (self.txt_col[0]-hover_delta_col,self.txt_col[1]-hover_delta_col,self.txt_col[2]-hover_delta_col)
                    elif self.hover_opt_col_mode == "positive":
                        cur_txt_col = (self.txt_col[0]+hover_delta_col,self.txt_col[1]+hover_delta_col,self.txt_col[2]+hover_delta_col)
                    else:
                        raise ValueError("hovered color mode passed is not defined")
                    if self.text:
                        new_text_obj = self.txt_font.render(self.text, True, cur_txt_col)
                        win.blit(new_text_obj, self.txt_rect)
                else:
                    if self.text:
                        win.blit(self.txt_object, self.txt_rect)
                if self.has_box:
                    pygame.draw.rect(win, cur_txt_col, (self.x, self.y, self.w, self.h), width=2, border_radius=5)



class FramedButton(GameObject): #a button with a pre-made ui
    def __init__(self,
                 function,
                 rect_x, rect_y, rect_w, rect_h,
                 added_width, frame_width,
                 align="topleft",
                 text=None,
                 font_size=30,
                 txt_col=general_txt_col,
                 hover_opt_col_mode="positive"):
        super().__init__()
        self.function = function
        self.hidden = False
        self.frame_rect = Rect(rect_x, rect_y, rect_w, rect_h)
        self.frame_width = frame_width
        self.align = align #where the trapeze is pointing
        self.text = text
        self.hover_opt_col_mode = hover_opt_col_mode
        self.frame_col = general_widget_col2
        self.bg_col = general_widget_col1

        if text:
            self.txt_col = txt_col
            self.txt_font = pygame.font.Font(pop_up_menus_txt_font, font_size)
            self.txt_object = self.txt_font.render(self.text, True, txt_col)
            self.txt_rect = self.txt_object.get_rect()
            self.txt_rect.center = (self.frame_rect[0] + self.frame_rect[2] // 2, self.frame_rect[1] + self.frame_rect[3] // 2)
            
        if align == "topleft": #setting the points of the polygon by the alignment
            self.points = ((self.frame_rect[0] - added_width, self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2], self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2], self.frame_rect[1] + self.frame_rect[3]),
                           (self.frame_rect[0], self.frame_rect[1] + self.frame_rect[3])
                           )
        elif align == "topright":
            self.points = ((self.frame_rect[0], self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2] + added_width, self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2], self.frame_rect[1] + self.frame_rect[3]),
                           (self.frame_rect[0], self.frame_rect[1] + self.frame_rect[3])
                           )
        elif align == "bottomleft":
            self.points = ((self.frame_rect[0], self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2], self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2], self.frame_rect[1] + self.frame_rect[3]),
                           (self.frame_rect[0] - added_width, self.frame_rect[1] + self.frame_rect[3])
                           )
        elif align == "bottomright":
            self.points = ((self.frame_rect[0], self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2], self.frame_rect[1]),
                           (self.frame_rect[0] + self.frame_rect[2] + added_width, self.frame_rect[1] + self.frame_rect[3]),
                           (self.frame_rect[0], self.frame_rect[1] + self.frame_rect[3])
                           )
        else:
            raise ValueError("Alignment passed is not defined. Alignment modes can be topright, topleft, bottomright and bottomleft.")


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if not self.hidden:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.frame_rect.collidepoint(event.pos):
                        self.function()

                        
    def update(self, update_func=None):
        if not self.update_blocked:
            super().update()
            if update_func:
                update_func()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if not self.hidden:
                pygame.draw.polygon(win, self.bg_col, self.points) #surface of the button
                if self.frame_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.polygon(win, self.txt_col, self.points, width=self.frame_width) #frame of the button                
                else:
                    pygame.draw.polygon(win, self.frame_col, self.points, width=self.frame_width)            
                if self.text:
                    win.blit(self.txt_object, self.txt_rect)



class ImageButton(GameObject): #a button displayed as an image
    def __init__(self, function, image_path, hovered_image_path, x, y, w, h, hitbox_x, hitbox_y, hitbox_w, hitbox_h, config_options={}):
        super().__init__()
        self.function = function
        if "scale" in config_options:
            self.image = pygame.transform.scale(pygame.image.load(image_path), config_options["scale"])
            self.hovered_image = pygame.transform.scale(pygame.image.load(hovered_image_path), config_options["scale"])
        else:
            self.image = pygame.image.load(image_path)
            self.hovered_image = pygame.image.load(hovered_image_path)
        self.hidden = False
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hitbox = Rect(hitbox_x, hitbox_y, hitbox_w, hitbox_h)
        self.config_options = config_options
        '''
        dict of type:

        {"scale": tuple,
         "image color": tuple,
         "hovered image color": tuple}

        in which every key is optional
        '''

        self.image_rect = self.image.get_rect()
        self.image_rect.center = (self.x + self.w // 2, self.y + self.h // 2)

        if "image color" in self.config_options:
            change_surface_col(self.image, self.config_options["image color"])
        if "hovered image color" in self.config_options:
            change_surface_col(self.hovered_image, self.config_options["hovered image color"])


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if not self.hidden:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hitbox.collidepoint(event.pos):
                        self.function()

    
    def update(self, update_func=None):
        if not self.update_blocked:
            super().update()
            if update_func:
                update_func()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if not self.hidden:
                if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                    win.blit(self.hovered_image, self.image_rect)
                else:
                    win.blit(self.image, self.image_rect)



class InfoButton(GameObject): #just some text that can be clicked to show a small info menu under it
    def __init__(self,
                 x, y,
                 hitbox_x, hitbox_y, hitbox_w, hitbox_h,
                 text=None, caption_txt=None, info_txt=None,
                 font_size=30, caption_font_size=24, info_font_size=16,
                 max_info_txt_len=30, info_txt_padding=3,
                 txt_col=general_txt_col,
                 info_txt_col=pop_up_menus_txt_col,
                 hover_opt_col_mode="positive"):
        super().__init__()
        self.hidden = False
        self.open = False
        self.x = x
        self.y = y
        self.hitbox = Rect(hitbox_x, hitbox_y, hitbox_w, hitbox_h) #hitbox to register the clicks
        self.text = text
        self.info_txt = info_txt
        self.caption_txt = caption_txt
        self.max_info_txt_len = max_info_txt_len
        self.txt_col = txt_col
        self.info_txt_col = info_txt_col
        self.hover_opt_col_mode = hover_opt_col_mode

        if text:
            self.txt_font = pygame.font.Font(general_menus_txt_font, font_size)
            self.txt_object = self.txt_font.render(self.text, True, txt_col)
            self.txt_rect = self.txt_object.get_rect()
            self.txt_rect.topleft = (self.x, self.y)

        if info_txt:
            self.info_font = pygame.font.Font(pop_up_menus_txt_font, info_font_size)
            self.info_objects = []
            
            words = self.info_txt.split()
            while True: #distributes the text amongst multiple text objects if there are multiple lines
                if len(words) == 0:
                    self.info_objects.append(self.info_font.render(new_line, True, info_txt_col)) #last line
                    break
                new_line = words[0]
                words.pop(0)
                while True:
                    if len(words) == 0:
                        break
                    if len(new_line + ' ' + words[0]) >= max_info_txt_len:
                        self.info_objects.append(self.info_font.render(new_line, True, info_txt_col)) #line is at maximum lenght so a new object is created
                        break
                    else:
                        new_line += ' ' + words[0]
                        words.pop(0)
                
            self.info_rects = [info_obj.get_rect() for info_obj in self.info_objects]
            self.info_surface_rect = Rect(0, 0, self.info_rects[0][2] + 20, sum([rect[3] for rect in self.info_rects]) + 60)
            self.info_surface_rect.center = (self.x + self.txt_rect[2] // 2 - 10, self.y + self.txt_rect[3] + self.info_surface_rect[3] // 2 + 30)
            self.info_surface = pygame.Surface((self.info_surface_rect[2], self.info_surface_rect[3]))
            for i, rect in enumerate(self.info_rects):
                rect.topleft = (10, 40 + rect[3] * i + info_txt_padding) #drawn on info_surface
            
        if caption_txt:
            self.caption_font = pygame.font.Font(pop_up_menus_txt_font, caption_font_size)
            self.caption_object = self.caption_font.render(self.caption_txt, True, info_txt_col)
            self.caption_rect = self.caption_object.get_rect()
            self.caption_rect.topleft = (0, 10) #drawn on info_surface


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if not self.hidden:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hitbox.collidepoint(event.pos): #the button is pressed
                        self.open = True
                    else:
                        self.open = False

                        
    def update(self, update_func=None):
        if not self.update_blocked:
            super().update()
            if update_func:
                update_func()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if not self.hidden:
                
                if self.open: #if the infos must be shown
                    info_border_rect = Rect(self.info_surface_rect[0]-5,self.info_surface_rect[1]-5,self.info_surface_rect[2]+10,self.info_surface_rect[3]+10)
                    pygame.draw.rect(win, pop_up_menus_bg_col, info_border_rect, width=10, border_radius=5)
                    self.info_surface.fill(pop_up_menus_bg_col)
                    if self.caption_txt:
                        self.info_surface.blit(self.caption_object, (self.caption_rect[0], self.caption_rect[1]))
                    if self.info_txt:
                        for i, obj in enumerate(self.info_objects): #draws every text object
                            self.info_surface.blit(obj, (self.info_rects[i][0], self.info_rects[i][1]))
                    win.blit(self.info_surface, self.info_surface_rect)
                    
                cur_txt_col = self.txt_col
                if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                    if self.hover_opt_col_mode == "negative":
                        cur_txt_col = (self.txt_col[0]-hover_delta_col,self.txt_col[1]-hover_delta_col,self.txt_col[2]-hover_delta_col)
                    elif self.hover_opt_col_mode == "positive":
                        cur_txt_col = (self.txt_col[0]+hover_delta_col,self.txt_col[1]+hover_delta_col,self.txt_col[2]+hover_delta_col)
                    else:
                        raise ValueError("hovered color mode passed is not defined")
                    if self.text:
                        new_text_obj = self.txt_font.render(self.text, True, cur_txt_col)
                        win.blit(new_text_obj, self.txt_rect)
                        
                else:
                    if self.text:
                        win.blit(self.txt_object, self.txt_rect)



class Notification(GameObject):
    def close(self, recalled=False):
        if not recalled: #if it hasn't been called from the notify system
            self.notify_sys.close_notification(obj=self)

        
    def __init__(self, notify_sys, title, text, caption, color=pop_up_menus_txt_col):
        super().__init__()

        self.notify_sys = notify_sys
        self.rect = NotifySystem.notification_rect
        self.bg_color = NotifySystem.notification_bg_color
        self.color = color
        self.title_font = NotifySystem.notification_title_font
        self.text_font = NotifySystem.notification_text_font
        self.caption_font = NotifySystem.notification_caption_font

        self.close_button = TextButton(self.close,
                                       self.rect[0] + self.rect[-2] - 140, self.rect[1] + 30, 100, 40,
                                       self.rect[0] + self.rect[-2] - 140, self.rect[1] + 25, 100, 45,
                                       text="close",
                                       font=pop_up_menus_txt_font,
                                       font_size=30,
                                       txt_col=self.color,
                                       has_box=True,
                                       hover_opt_col_mode="negative")

        self.title_txt_font = pygame.font.Font(self.title_font, 46)
        self.title_txt_obj = self.title_txt_font.render(title.upper(), True, self.color)
        self.title_txt_rect = self.title_txt_obj.get_rect()
        self.title_txt_rect.topleft = (self.rect[0] + 20, self.rect[1] + 40)

        self.caption_txt_font = pygame.font.Font(self.caption_font, 30)
        self.caption_txt_obj = self.caption_txt_font.render(caption, True, self.color)
        self.caption_txt_rect = self.caption_txt_obj.get_rect()
        self.caption_txt_rect.center = (self.rect[0] + self.rect[-2] // 2, self.rect[1] + self.rect[-1] - 30)

        self.text_txt_font = pygame.font.Font(self.text_font, 24)

        self.text_objects = []
        words = text.split()
        while True: #distributes the text amongst multiple text objects if there are multiple lines
            if len(words) == 0:
                self.text_objects.append(self.text_txt_font.render(new_line, True, self.color)) #last line
                break
            new_line = words[0]
            words.pop(0)
            while True:
                if len(words) == 0:
                    break
                if len(new_line + ' ' + words[0]) >= NotifySystem.max_text_line_len:
                    self.text_objects.append(self.text_txt_font.render(new_line, True, self.color)) #line is at maximum lenght so a new object is created
                    break
                else:
                    new_line += ' ' + words[0]
                    words.pop(0)
            
        self.text_rects = [text_obj.get_rect() for text_obj in self.text_objects]
        self.text_surface_rect = Rect(self.rect[0] + self.rect[2] - max([rect[2] for rect in self.text_rects]) - 80,
                                      self.rect[1] + self.title_txt_rect[-1] + 180,
                                      max([rect[2] for rect in self.text_rects]),
                                      NotifySystem.max_text_surface_height)
        self.text_surface = pygame.Surface((self.text_surface_rect[2], self.text_surface_rect[3]))
        for i, rect in enumerate(self.text_rects):
            rect.topleft = (0, (rect[3] + 20) * i) #drawn on info_surface

        self.scrollbar = None
        if sum([rect[-1] + 20 for rect in self.text_rects]) > NotifySystem.max_text_surface_height:
            self.scrollbar = VerticalScrollBar(0, (sum([rect[-1] + 20 for rect in self.text_rects]) - NotifySystem.max_text_surface_height) / 50,
                                               self.rect[0] + self.rect[2] - 20, self.text_surface_rect[1], self.text_surface_rect[-1], 8,
                                               NotifySystem.scrollbar_col, pop_up_menus_txt_col,
                                               rounded=None,
                                               bar_thickness=10,
                                               capsule_bar=True,
                                               selection_inflate=2)


    def draw_title_lines(self):
        ref_rect = self.title_txt_rect
        pygame.draw.lines(win, self.color, False,
                          (
                          (self.rect[0] + 20, ref_rect[1] + ref_rect[-1] + 20),
                          (self.rect[0] + 40 + ref_rect[-2], ref_rect[1] + ref_rect[-1] + 20),
                          (self.rect[0] + 160 + ref_rect[-2], ref_rect[1] - 20)
                          ),
                          width=5)
        pygame.draw.lines(win, self.color, False,
                          (
                          (self.rect[0] + 260, ref_rect[1] + ref_rect[-1] + 40),
                          (self.rect[0] + 60 + ref_rect[-2], ref_rect[1] + ref_rect[-1] + 40),
                          (self.rect[0] + 180 + ref_rect[-2], ref_rect[1]),
                          (self.rect[0] + self.rect[-2] - 240, ref_rect[1])
                          ),
                          width=5)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + self.rect[-2] - 230, ref_rect[1]),
                         (self.rect[0] + self.rect[-2] - 210, ref_rect[1]),
                         width=5)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + self.rect[-2] - 200, ref_rect[1]),
                         (self.rect[0] + self.rect[-2] - 190, ref_rect[1]),
                         width=5)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 40, ref_rect[1] + ref_rect[-1] + 40),
                         (self.rect[0] + 100, ref_rect[1] + ref_rect[-1] + 40),
                         width=5)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 110, ref_rect[1] + ref_rect[-1] + 40),
                         (self.rect[0] + 120, ref_rect[1] + ref_rect[-1] + 40),
                         width=5)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 130, ref_rect[1] + ref_rect[-1] + 40),
                         (self.rect[0] + 140, ref_rect[1] + ref_rect[-1] + 40),
                         width=5)


    def draw_caption_lines(self):
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 110, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + self.rect[-2] - 110, self.rect[1] + self.rect[-1] - 60),
                         width=2)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 100, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + 80, self.rect[1] + self.rect[-1] - 60),
                         width=2)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 70, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + 60, self.rect[1] + self.rect[-1] - 60),
                         width=2)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + 50, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + 40, self.rect[1] + self.rect[-1] - 60),
                         width=2)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + self.rect[-2] - 100, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + self.rect[-2] - 80, self.rect[1] + self.rect[-1] - 60),
                         width=2)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + self.rect[-2] - 70, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + self.rect[-2] - 60, self.rect[1] + self.rect[-1] - 60),
                         width=2)
        pygame.draw.line(win, self.color,
                         (self.rect[0] + self.rect[-2] - 50, self.rect[1] + self.rect[-1] - 60),
                         (self.rect[0] + self.rect[-2] - 40, self.rect[1] + self.rect[-1] - 60),
                         width=2)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)

            self.close_button.event_update(event)
            if self.scrollbar:
                self.scrollbar.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()

            self.close_button.update()
            if self.scrollbar:
                self.scrollbar.update()

            
    def draw(self):
        if not self.draw_blocked:
            super().draw()
            
            pygame.draw.rect(win, self.bg_color, self.rect, border_radius=10) #draws the background
            
            win.blit(self.title_txt_obj, self.title_txt_rect)
            self.draw_title_lines()
            
            self.text_surface.fill(self.bg_color)
            for i, obj in enumerate(self.text_objects): #draws every text object
                text_rect = copy.deepcopy(self.text_rects[i])
                if self.scrollbar:
                    text_rect.y -= self.scrollbar.get_value() * 50
                self.text_surface.blit(obj, (text_rect.x, text_rect.y))
            win.blit(self.text_surface, self.text_surface_rect)

            if self.scrollbar:
                self.scrollbar.draw()

            win.blit(self.caption_txt_obj, self.caption_txt_rect)
            self.draw_caption_lines()

            self.close_button.draw()



class NotifySystem(GameObject):
    notification_rect = (200, 100, 1200, 700)
    notification_bg_color = pop_up_menus_bg_col
    notification_title_font = pop_up_menus_txt_font
    notification_text_font = 'Aristotelica Display DemiBold Trial.ttf'
    notification_caption_font = pop_up_menus_txt_font
    max_text_line_len = 90
    max_text_surface_height = 340
    scrollbar_col = (50, 55, 70)
    
    def __init__(self):
        super().__init__()
        
        self.stack = []


    def stack_append(self, notification : Notification):
        self.stack.append(notification)


    def close_notification(self, index=-1, obj=None):
        if obj:
            obj.close(True)
            self.stack.remove(obj)
        else:
            self.stack[index].close(True)
            self.stack.pop(index)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if self.stack:
                self.stack[-1].event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            for notification in self.stack:
                notification.update()

            
    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if self.stack:
                self.stack[-1].draw()



#structures and building info displays are seen on the scene "planet view / building view"
class PlanetBuildingStructure(GameObject):
    #NOTE: do not use this class ingame
    def __init__(self, building, cost, name="unnamed building"):
        super().__init__()
        building.structures.append(self)

        self.hidden = True
        self.rect = Rect(620, 400, 650, 450)
        self.building = building
        self.cost = cost
        self.name = name
        self.space = 1

        def structure_func():
            global selected_structure
            self.hidden = False
            selected_structure = self

        self.button = TextButton(structure_func,
                                 45, 500 + structures_abs_padding_in_display * building.structures.index(self), 500, 70,
                                 45, 500 + structures_abs_padding_in_display * building.structures.index(self), 505, 70,
                                 text=self.name,font_size=40,txt_col=general_txt_col,
                                 has_box=True,
                                 fix="topleft",
                                 hover_opt_col_mode="positive")

        self.font = pygame.font.Font(general_txt_font, structure_names_display_font_size)

        def set_txt(font, name, rect):
            txt_obj = font.render(name, True, general_txt_col)
            txt_rect = txt_obj.get_rect()
            txt_rect.center = (rect.x + rect.w // 2, rect.y + 60)
            return txt_obj, txt_rect

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)

        return set_txt


    def get_space(): #to calculate space required before building the structure (the space cost is gotten from the class itself and not an object)
        return 1
    

    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            self.button.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            global selected_structure
            
            self.button.change_pos((45, 500 + structures_abs_padding_in_display * self.building.structures.index(self), 500, 70))
            self.button.update()

            if selected_structure != self:
                self.hidden = True


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if selected_build == self.building:
                self.button.draw()
            if not self.hidden:
                #pygame.draw.rect(win, (255,0,0), self.rect)
                win.blit(self.txt_obj, self.txt_rect)



class LaunchSite(PlanetBuildingStructure):
    __space = 1
    __binded_building = Colony
    is_researched = True
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="launch site")

        self.space = LaunchSite.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return LaunchSite.__space

    @staticmethod
    def get_building():
        return LaunchSite.__binded_building

    
    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



class Laboratory(PlanetBuildingStructure):
    __space = 2
    __binded_building = Colony
    is_researched = True
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="laboratory")

        self.space = Laboratory.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return Laboratory.__space

    @staticmethod
    def get_building():
        return Laboratory.__binded_building

    
    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



class TemperatureNet(PlanetBuildingStructure):
    __space = 4
    __binded_building = Colony
    is_researched = False
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="temperature net")

        self.space = TemperatureNet.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return TemperatureNet.__space

    @staticmethod
    def get_building():
        return TemperatureNet.__binded_building


    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



class PressureNet(PlanetBuildingStructure):
    __space = 4
    __binded_building = Colony
    is_researched = False
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="pressure net")

        self.space = PressureNet.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return PressureNet.__space

    @staticmethod
    def get_building():
        return PressureNet.__binded_building


    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



class ResidentialZone(PlanetBuildingStructure):
    __space = 8
    __binded_building = City
    is_researched = True
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="residential zone")

        self.space = ResidentialZone.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return ResidentialZone.__space

    @staticmethod
    def get_building():
        return ResidentialZone.__binded_building

    
    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



class SpacePort(PlanetBuildingStructure):
    __space = 2
    __binded_building = City
    is_researched = False
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="space port")

        self.space = SpacePort.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return SpacePort.__space

    @staticmethod
    def get_building():
        return SpacePort.__binded_building


    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



class EarthLaunchSite(PlanetBuildingStructure):
    __space = 1
    __binded_building = Base
    is_researched = True
    
    def __init__(self, building, cost):
        set_txt = super().__init__(building, cost, name="earth launch site")

        self.space = EarthLaunchSite.__space

        self.txt_obj, self.txt_rect = set_txt(self.font, self.name, self.rect)


    @staticmethod
    def get_space():
        return EarthLaunchSite.__space

    @staticmethod
    def get_building():
        return EarthLaunchSite.__binded_building

    
    def event_update(self, event):
        super().event_update(event)


    def update(self):
        super().update()


    def draw(self):
        super().draw()



def bind_info_display_menu_funcs(info_display):
    if type(info_display) == ColonyInfoDisplay:
        
        def add_launch_site():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.colony.structures]
            if LaunchSite.get_space() <= info_display.colony.max_space - sum(space_occupied):
                if globalcoins > info_display.colony.launch_site_cost:
                    LaunchSite(info_display.colony, info_display.colony.launch_site_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.colony.launch_site_cost

        def add_laboratory():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.colony.structures]
            if Laboratory.get_space() <= info_display.colony.max_space - sum(space_occupied):
                if globalcoins > info_display.colony.laboratory_cost:
                    Laboratory(info_display.colony, info_display.colony.laboratory_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.colony.laboratory_cost

        def add_temperature_net():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.colony.structures]
            if TemperatureNet.get_space() <= info_display.colony.max_space - sum(space_occupied):
                if globalcoins > info_display.colony.temperature_net_cost:
                    TemperatureNet(info_display.colony, info_display.colony.temperature_net_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.colony.temperature_net_cost

        def add_pressure_net():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.colony.structures]
            if PressureNet.get_space() <= info_display.colony.max_space - sum(space_occupied):
                if globalcoins > info_display.colony.pressure_net_cost:
                    PressureNet(info_display.colony, info_display.colony.pressure_net_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.colony.pressure_net_cost

        def cancel_structure_func():
            info_display.add_structure_menu.hidden = True

        return [eval(func, {'add_launch_site': add_launch_site,
                            'add_laboratory': add_laboratory,
                            'add_temperature_net': add_temperature_net,
                            'add_pressure_net': add_pressure_net,
                            'cancel_structure_func': cancel_structure_func}) for func in ColonyInfoDisplay.menu_funcs]

    elif type(info_display) == CityInfoDisplay:

        def add_residential_zone():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.city.structures]
            if ResidentialZone.get_space() <= info_display.city.max_space - sum(space_occupied):
                if globalcoins > info_display.city.residential_zone_cost:
                    ResidentialZone(info_display.city, info_display.city.residential_zone_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.city.residential_zone_cost

        def add_space_port():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.city.structures]
            if SpacePort.get_space() <= info_display.city.max_space - sum(space_occupied):
                if globalcoins > info_display.city.space_port_cost:
                    SpacePort(info_display.city, info_display.city.space_port_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.city.space_port_cost

        def cancel_structure_func():
            info_display.add_structure_menu.hidden = True

        return [eval(func, {'add_residential_zone': add_residential_zone,
                            'add_space_port': add_space_port,
                            'cancel_structure_func': cancel_structure_func}) for func in CityInfoDisplay.menu_funcs]

    elif type(info_display) == BaseInfoDisplay:

        def add_earth_launch_site():
            global globalcoins
            space_occupied = [structure.space for structure in info_display.base.structures]
            if EarthLaunchSite.get_space() <= info_display.base.max_space - sum(space_occupied):
                if globalcoins > info_display.base.earth_launch_site_cost:
                    EarthLaunchSite(info_display.base, info_display.base.earth_launch_site_cost)
                    info_display.add_structure_menu.hidden = True
                    globalcoins -= info_display.base.earth_launch_site_cost

        def cancel_structure_func():
            info_display.add_structure_menu.hidden = True

        return [eval(func, {'add_earth_launch_site': add_earth_launch_site,
                            'cancel_structure_func': cancel_structure_func}) for func in BaseInfoDisplay.menu_funcs]



class ColonyInfoDisplay(GameObject):
    menu_funcs = ['add_launch_site', 'add_laboratory', 'cancel_structure_func']
    menu_costs = ['launch_site_cost', 'laboratory_cost'] #the list that will be used is local_menu_costs because the cost will be drawn for every specific structure
    menu_spaces = [LaunchSite.get_space(), Laboratory.get_space()]
  
    add_structure_menu_init = BasicPopUpMenu([{"text": "SELECT THE BUILDING TYPE", #common templates for all the colonies
                                               "option type": "text",
                                               "additional padding": 0,
                                               "color": (255,255,255)
                                              },
                                              {"text": "launch site",
                                               "option type": "button",
                                               "function": None,
                                               "additional padding": 40,
                                               "color": pop_up_menus_txt_col
                                              },
                                              {"text": "laboratory",
                                               "option type": "button",
                                               "function": None,
                                               "additional padding": 0,
                                               "color": pop_up_menus_txt_col
                                              },
                                              {"text": "CANCEL",
                                               "option type": "button",
                                               "function":None,
                                               "additional padding": 40,
                                               "color": pop_up_menus_txt_col
                                              }],
                                             cur_win_size[0] // 3.2, 100, 44, 80, 80, 40,
                                             font=pop_up_menus_txt_font,
                                             align="center",
                                             facing="vertical",
                                             has_bg=True,
                                             hover_opt_col_mode="negative",
                                             input_box_font_size=50)


    add_structure_menu_costs_init = BasicPopUpMenu([{"text": None,
                                                     "option type": "text",
                                                     "additional padding": 40,
                                                     "color": pop_up_menus_txt_col
                                                    },
                                                    {"text": None,
                                                     "option type": "text",
                                                     "additional padding": 0,
                                                     "color": pop_up_menus_txt_col
                                                    }],
                                                   cur_win_size[0] // 3.2 + 450, 170, 20, 80, 80, 56,
                                                   font=general_menus_txt_font,
                                                   align="center",
                                                   facing="vertical",
                                                   has_bg=False,
                                                   hover_opt_col_mode="negative",
                                                   input_box_font_size=50)


    add_structure_menu_spaces_init = BasicPopUpMenu([{"text": None,
                                                      "option type": "text",
                                                      "additional padding": 40,
                                                      "color": pop_up_menus_txt_col
                                                     },
                                                     {"text": None,
                                                      "option type": "text",
                                                      "additional padding": 0,
                                                      "color": pop_up_menus_txt_col
                                                     }],
                                                    cur_win_size[0] // 3.2 + 450, 200, 20, 80, 80, 56,
                                                    font=general_menus_txt_font,
                                                    align="center",
                                                    facing="vertical",
                                                    has_bg=False,
                                                    hover_opt_col_mode="negative",
                                                    input_box_font_size=50)

    
    def __init__(self, colony, add_structure_button, add_space_button):
        super().__init__()
        self.colony = colony
        self.colony.info_display = self
        space_occupied_in_colony = [structure.space for structure in colony.structures]
        self.add_structure_button = add_structure_button #the buttons are created in the update() function
        self.add_space_button = add_space_button
        
        self.space_display_font = pygame.font.Font(general_txt_font, 36) #objects for the building space indicators
        self.max_space_txt_obj = self.space_display_font.render("max: " + str(colony.max_space), True, general_txt_col)
        self.max_space_txt_rect = self.max_space_txt_obj.get_rect()
        self.left_space_txt_obj = self.space_display_font.render("left: " + str(colony.max_space - sum(space_occupied_in_colony)), True, general_txt_col)
        self.left_space_txt_rect = self.left_space_txt_obj.get_rect()
        self.max_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y)
        self.left_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y + 50)

        def add_structure_func():
            self.add_structure_menu.hidden = False


        def add_space_func():
            '''
            Adds building space to a building
            '''
            global globalcoins
            
            space_cost = colony.base_space_cost
            for i in range(0, colony.max_space - colony.initial_space):
                space_cost *= colony.space_cost_multiplier

            if globalcoins >= space_cost:
                colony.max_space += 1
                print("space is added in " + colony.name + ", now the maximum space is", colony.max_space)
                globalcoins -= space_cost

        self.add_structure_button.function = add_structure_func
        self.add_space_button.function = add_space_func

        self.add_structure_menu = ColonyInfoDisplay.add_structure_menu_init.copy()
        self.add_structure_menu.hidden = True
        
        for i, option in enumerate(self.add_structure_menu.options):
            if i > 0:
                option["function"] = bind_info_display_menu_funcs(self)[i-1]

        #displays the costs of the structures | the cost is managed in the PlanetBuilding classes so they can change accordingly to the context
        self.local_menu_costs = [eval('self.colony.' + cost, {'self':self}) for cost in ColonyInfoDisplay.menu_costs]
        
        self.add_structure_menu_costs = ColonyInfoDisplay.add_structure_menu_costs_init.copy()
        self.add_structure_menu_costs.hidden = True

        options_copy = self.add_structure_menu_costs.options.copy() #uses a flexible template to initialise because the menu can change overtime in all colonies together
        for i, option in enumerate(options_copy):
            option["text"] = compress_number_value_in_str(self.local_menu_costs[i])+"  G"
        self.add_structure_menu_costs.change_options(options_copy)

        #displays the space occupied by the structures | the space is managed in the PlanetBuildingStructure classes
        self.add_structure_menu_spaces = ColonyInfoDisplay.add_structure_menu_spaces_init.copy()
        self.add_structure_menu_spaces.hidden = True

        options_copy = self.add_structure_menu_spaces.options.copy() #same template deal as above
        for i, option in enumerate(options_copy):
            option["text"] = str(ColonyInfoDisplay.menu_spaces[i])
        self.add_structure_menu_spaces.change_options(options_copy)


    @staticmethod
    def register_menu_update(new_menu_option : dict, new_menu_func : str, new_menu_cost_option : dict, new_menu_cost : str, new_menu_space_option : dict, new_menu_space : int):
        global current_planet
        
        ColonyInfoDisplay.menu_funcs.insert(-1, new_menu_func)
        new_options = ColonyInfoDisplay.add_structure_menu_init.options.copy()
        new_options.insert(-1, new_menu_option)
        ColonyInfoDisplay.add_structure_menu_init.change_options(new_options)

        new_options = ColonyInfoDisplay.add_structure_menu_costs_init.options.copy()
        new_options.append(new_menu_cost_option)
        ColonyInfoDisplay.add_structure_menu_costs_init.change_options(new_options)
        ColonyInfoDisplay.menu_costs.append(new_menu_cost)

        new_options = ColonyInfoDisplay.add_structure_menu_spaces_init.options.copy()
        new_options.append(new_menu_space_option)
        ColonyInfoDisplay.add_structure_menu_spaces_init.change_options(new_options)
        ColonyInfoDisplay.menu_spaces.append(str(new_menu_space))

        for colony in current_planet.colonies:

            #adds the option to build the structure on a colony
            funcs = [option["function"] for option in colony.info_display.add_structure_menu.options[1:]]
            for option in colony.info_display.add_structure_menu.options[1:]: #removes the functions in the menu options to make a deep copy
                option["function"] = None
                
            new_options = copy.deepcopy(colony.info_display.add_structure_menu.options)
            
            for i, option in enumerate(colony.info_display.add_structure_menu.options[1:]): #re-adds the functions to both the original menu options and the copied one
                option["function"] = funcs[i]
            for i, option in enumerate(new_options[1:]):
                option["function"] = funcs[i]
                
            new_options.insert(-1, new_menu_option.copy())
            new_options[-2]["function"] = bind_info_display_menu_funcs(colony.info_display)[-2] #a function specific for the colony is created
            colony.info_display.add_structure_menu.change_options(new_options)

            new_options = copy.deepcopy(colony.info_display.add_structure_menu_costs.options) #adds the cost indicator
            new_options.append(new_menu_cost_option)
            new_options[-1]["text"] = compress_number_value_in_str(eval('''colony.'''+new_menu_cost))+"  G"
            colony.info_display.add_structure_menu_costs.change_options(new_options)
            
            colony.info_display.local_menu_costs.append(eval('''colony.'''+new_menu_cost))

            new_options = copy.deepcopy(colony.info_display.add_structure_menu_spaces.options) #adds the space required indicator
            new_options.append(new_menu_space_option)
            new_options[-1]["text"] = str(new_menu_space)
            colony.info_display.add_structure_menu_spaces.change_options(new_options)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            self.add_structure_button.event_update(event)
            self.add_space_button.event_update(event)
            self.add_structure_menu.event_update(event)
            self.add_structure_menu_costs.event_update(event)
            self.add_structure_menu_spaces.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()

            #updates building space indicators
            space_occupied_in_colony = [structure.space for structure in self.colony.structures]

            self.max_space_txt_obj = self.space_display_font.render("max: " + str(self.colony.max_space), True, general_txt_col)
            self.left_space_txt_obj = self.space_display_font.render("left: " + str(self.colony.max_space - sum(space_occupied_in_colony)), True, general_txt_col)
            
            if self.add_structure_menu.hidden: #syncs the visibility of the secondary menus (costs, spaces) with the main one (structures)
                self.add_structure_menu_costs.hidden = True
                self.add_structure_menu_spaces.hidden = True
            else:
                self.add_structure_menu_costs.hidden = False
                self.add_structure_menu_spaces.hidden = False
                
            self.add_structure_button.update()
            self.add_space_button.update()
            self.add_structure_menu.update()
            self.add_structure_menu_costs.update()
            self.add_structure_menu_spaces.update()

            if not menus["pause menu"].hidden:
                self.add_structure_menu.hidden = True


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            win.blit(self.max_space_txt_obj, self.max_space_txt_rect)
            win.blit(self.left_space_txt_obj, self.left_space_txt_rect)
            self.add_structure_button.draw()
            self.add_space_button.draw()
            self.add_structure_menu.draw()
            self.add_structure_menu_costs.draw()
            self.add_structure_menu_spaces.draw()



class CityInfoDisplay(GameObject):
    menu_funcs = ['add_residential_zone', 'cancel_structure_func']
    menu_costs = ['residential_zone_cost'] 
    menu_spaces = [ResidentialZone.get_space()]
  
    add_structure_menu_init = BasicPopUpMenu([{"text": "SELECT THE BUILDING TYPE", #common templates for all the colonies
                                               "option type": "text",
                                               "additional padding": 0,
                                               "color": (255,255,255)
                                              },
                                              {"text": "residential zone",
                                               "option type": "button",
                                               "function": None,
                                               "additional padding": 40,
                                               "color": pop_up_menus_txt_col
                                              },
                                              {"text": "CANCEL",
                                               "option type": "button",
                                               "function":None,
                                               "additional padding": 40,
                                               "color": pop_up_menus_txt_col
                                              }],
                                             cur_win_size[0] // 3.2, 100, 44, 80, 80, 40,
                                             font=pop_up_menus_txt_font,
                                             align="center",
                                             facing="vertical",
                                             has_bg=True,
                                             hover_opt_col_mode="negative",
                                             input_box_font_size=50)


    add_structure_menu_costs_init = BasicPopUpMenu([{"text": None,
                                                     "option type": "text",
                                                     "additional padding": 40,
                                                     "color": pop_up_menus_txt_col
                                                    }],
                                                   cur_win_size[0] // 3.2 + 450, 170, 20, 80, 80, 56,
                                                   font=general_menus_txt_font,
                                                   align="center",
                                                   facing="vertical",
                                                   has_bg=False,
                                                   hover_opt_col_mode="negative",
                                                   input_box_font_size=50)


    add_structure_menu_spaces_init = BasicPopUpMenu([{"text": None,
                                                      "option type": "text",
                                                      "additional padding": 40,
                                                      "color": pop_up_menus_txt_col
                                                     }],
                                                    cur_win_size[0] // 3.2 + 450, 200, 20, 80, 80, 56,
                                                    font=general_menus_txt_font,
                                                    align="center",
                                                    facing="vertical",
                                                    has_bg=False,
                                                    hover_opt_col_mode="negative",
                                                    input_box_font_size=50)

    
    def __init__(self, city, add_structure_button, add_space_button):
        super().__init__()
        self.city = city
        self.city.info_display = self
        space_occupied_in_city = [structure.space for structure in city.structures]
        self.add_structure_button = add_structure_button
        self.add_space_button = add_space_button
        
        self.space_display_font = pygame.font.Font(general_txt_font, 36)
        self.max_space_txt_obj = self.space_display_font.render("max: " + str(city.max_space), True, general_txt_col)
        self.max_space_txt_rect = self.max_space_txt_obj.get_rect()
        self.left_space_txt_obj = self.space_display_font.render("left: " + str(city.max_space - sum(space_occupied_in_city)), True, general_txt_col)
        self.left_space_txt_rect = self.left_space_txt_obj.get_rect()
        self.max_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y)
        self.left_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y + 50)

        def add_structure_func():
            self.add_structure_menu.hidden = False


        def add_space_func():
            '''
            Adds building space to a building
            '''
            global globalcoins
            
            space_cost = city.base_space_cost
            for i in range(0, city.max_space - city.initial_space):
                space_cost *= city.space_cost_multiplier

            if globalcoins >= space_cost:
                city.max_space += 1
                print("space is added in " + city.name + ", now the maximum space is", city.max_space)
                globalcoins -= space_cost

        self.add_structure_button.function = add_structure_func
        self.add_space_button.function = add_space_func

        self.add_structure_menu = CityInfoDisplay.add_structure_menu_init.copy()
        self.add_structure_menu.hidden = True
        
        for i, option in enumerate(self.add_structure_menu.options):
            if i > 0:
                option["function"] = bind_info_display_menu_funcs(self)[i-1]

        #displays the costs of the structures | the cost is managed in the PlanetBuilding classes so they can change accordingly to the context
        self.local_menu_costs = [eval('self.city.' + cost, {'self':self}) for cost in CityInfoDisplay.menu_costs]
        
        self.add_structure_menu_costs = CityInfoDisplay.add_structure_menu_costs_init.copy()
        self.add_structure_menu_costs.hidden = True

        options_copy = self.add_structure_menu_costs.options.copy()
        for i, option in enumerate(options_copy):
            option["text"] = compress_number_value_in_str(self.local_menu_costs[i])+"  G"
        self.add_structure_menu_costs.change_options(options_copy)

        #displays the space occupied by the structures | the space is managed in the PlanetBuildingStructure classes
        self.add_structure_menu_spaces = CityInfoDisplay.add_structure_menu_spaces_init.copy()
        self.add_structure_menu_spaces.hidden = True

        options_copy = self.add_structure_menu_spaces.options.copy()
        for i, option in enumerate(options_copy):
            option["text"] = str(CityInfoDisplay.menu_spaces[i])
        self.add_structure_menu_spaces.change_options(options_copy)


    @staticmethod
    def register_menu_update(new_menu_option : dict, new_menu_func : str, new_menu_cost_option : dict, new_menu_cost : str, new_menu_space_option : dict, new_menu_space : int):
        global current_planet

        CityInfoDisplay.menu_funcs.insert(-1, new_menu_func)
        new_options = CityInfoDisplay.add_structure_menu_init.options.copy()
        new_options.insert(-1, new_menu_option)
        CityInfoDisplay.add_structure_menu_init.change_options(new_options)

        new_options = CityInfoDisplay.add_structure_menu_costs_init.options.copy()
        new_options.append(new_menu_cost_option)
        CityInfoDisplay.add_structure_menu_costs_init.change_options(new_options)
        CityInfoDisplay.menu_costs.append(new_menu_cost)

        new_options = CityInfoDisplay.add_structure_menu_spaces_init.options.copy()
        new_options.append(new_menu_space_option)
        CityInfoDisplay.add_structure_menu_spaces_init.change_options(new_options)
        CityInfoDisplay.menu_spaces.append(str(new_menu_space))

        for city in current_planet.cities:

            #adds the option to build the structure on a colony
            funcs = [option["function"] for option in city.info_display.add_structure_menu.options[1:]]
            for option in city.info_display.add_structure_menu.options[1:]: #removes the functions in the menu options to make a deep copy
                option["function"] = None
                
            new_options = copy.deepcopy(city.info_display.add_structure_menu.options)
            
            for i, option in enumerate(city.info_display.add_structure_menu.options[1:]): #re-adds the functions to both the original menu options and the copied one
                option["function"] = funcs[i]
            for i, option in enumerate(new_options[1:]):
                option["function"] = funcs[i]
                
            new_options.insert(-1, new_menu_option.copy())
            new_options[-2]["function"] = bind_info_display_menu_funcs(city.info_display)[-2] #a function specific for the colony is created
            city.info_display.add_structure_menu.change_options(new_options)

            new_options = copy.deepcopy(city.info_display.add_structure_menu_costs.options) #adds the cost indicator
            new_options.append(new_menu_cost_option)
            new_options[-1]["text"] = compress_number_value_in_str(eval('''city.'''+new_menu_cost))+"  G"
            city.info_display.add_structure_menu_costs.change_options(new_options)
            
            city.info_display.local_menu_costs.append(eval('''city.'''+new_menu_cost))

            new_options = copy.deepcopy(city.info_display.add_structure_menu_spaces.options) #adds the space required indicator
            new_options.append(new_menu_space_option)
            new_options[-1]["text"] = str(new_menu_space)
            city.info_display.add_structure_menu_spaces.change_options(new_options)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            self.add_structure_button.event_update(event)
            self.add_space_button.event_update(event)
            self.add_structure_menu.event_update(event)
            self.add_structure_menu_costs.event_update(event)
            self.add_structure_menu_spaces.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()

            #updates building space indicators
            space_occupied_in_city = [structure.space for structure in self.city.structures]

            self.max_space_txt_obj = self.space_display_font.render("max: " + str(self.city.max_space), True, general_txt_col)
            self.left_space_txt_obj = self.space_display_font.render("left: " + str(self.city.max_space - sum(space_occupied_in_city)), True, general_txt_col)
            
            if self.add_structure_menu.hidden: #syncs the visibility of the secondary menus (costs, spaces) with the main one (structures)
                self.add_structure_menu_costs.hidden = True
                self.add_structure_menu_spaces.hidden = True
            else:
                self.add_structure_menu_costs.hidden = False
                self.add_structure_menu_spaces.hidden = False
                
            self.add_structure_button.update()
            self.add_space_button.update()
            self.add_structure_menu.update()
            self.add_structure_menu_costs.update()
            self.add_structure_menu_spaces.update()

            if not menus["pause menu"].hidden:
                self.add_structure_menu.hidden = True


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            win.blit(self.max_space_txt_obj, self.max_space_txt_rect)
            win.blit(self.left_space_txt_obj, self.left_space_txt_rect)
            self.add_structure_button.draw()
            self.add_space_button.draw()
            self.add_structure_menu.draw()
            self.add_structure_menu_costs.draw()
            self.add_structure_menu_spaces.draw()



class IndustrialZoneInfoDisplay(GameObject):
    def __init__(self, industrial_zone, add_structure_button, add_space_button):
        super().__init__()
        self.industrial_zone = industrial_zone
        self.industrial_zone.info_display = self
        space_occupied_by_industrial_zone = [structure.space for structure in industrial_zone.structures]
        self.add_structure_button = add_structure_button
        self.add_space_button = add_space_button
        
        self.space_display_font = pygame.font.Font(general_txt_font, 36)
        self.max_space_txt_obj = self.space_display_font.render("max: " + str(industrial_zone.max_space), True, general_txt_col)
        self.max_space_txt_rect = self.max_space_txt_obj.get_rect()
        self.left_space_txt_obj = self.space_display_font.render("left: " + str(industrial_zone.max_space - sum(space_occupied_by_industrial_zone)), True, general_txt_col)
        self.left_space_txt_rect = self.left_space_txt_obj.get_rect()
        self.max_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y)
        self.left_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y + 50)


        def add_structure_func():
            pass


        def add_space_func():
            global globalcoins
            
            space_cost = industrial_zone.base_space_cost
            for i in range(0, industrial_zone.max_space - industrial_zone.initial_space):
                space_cost *= industrial_zone.space_cost_multiplier

            if globalcoins >= space_cost:
                industrial_zone.max_space += 1
                print("space is added in " + industrial_zone.name + ", now the maximum space is", industrial_zone.max_space)
                globalcoins -= space_cost

        self.add_structure_button.function = add_structure_func
        self.add_space_button.function = add_space_func


        def cancel_structure_func():
            self.add_structure_menu.hidden = True
            
        self.add_structure_menu = BasicPopUpMenu([{"text": "SELECT THE BUILDING TYPE",
                                                   "option type": "text",
                                                   "additional padding": 20,
                                                   "color": pop_up_menus_txt_col
                                                  },
                                                  {"text": "CANCEL",
                                                   "option type": "button",
                                                   "function":cancel_structure_func,
                                                   "additional padding": 40,
                                                   "color": pop_up_menus_txt_col
                                                  }],
                                                 cur_win_size[0] // 3.2, 200, 44, 80, 80, 40,
                                                 font=pop_up_menus_txt_font,
                                                 align="center",
                                                 facing="vertical",
                                                 has_bg=True,
                                                 hover_opt_col_mode="negative",
                                                 input_box_font_size=50)
        self.add_structure_menu.hidden = True


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            self.add_structure_button.event_update(event)
            self.add_space_button.event_update(event)
            self.add_structure_menu.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            space_occupied_by_industrial_zone = [structure.space for structure in self.industrial_zone.structures]
            
            self.max_space_txt_obj = self.space_display_font.render("max: " + str(self.industrial_zone.max_space), True, general_txt_col)
            self.left_space_txt_obj = self.space_display_font.render("left: " + str(self.industrial_zone.max_space - sum(space_occupied_by_industrial_zone)), True, general_txt_col)
            
            self.add_structure_button.update()
            self.add_space_button.update()
            self.add_structure_menu.update()

            if not menus["pause menu"].hidden:
                self.add_structure_menu.hidden = True


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            win.blit(self.max_space_txt_obj, self.max_space_txt_rect)
            win.blit(self.left_space_txt_obj, self.left_space_txt_rect)
            self.add_structure_button.draw()
            self.add_space_button.draw()
            self.add_structure_menu.draw()



class BaseInfoDisplay(GameObject):
    menu_funcs = ['add_earth_launch_site', 'cancel_structure_func']
    menu_costs = ['earth_launch_site_cost'] 
    menu_spaces = [EarthLaunchSite.get_space()]
  
    add_structure_menu_init = BasicPopUpMenu([{"text": "SELECT THE BUILDING TYPE", #common templates for all the colonies
                                               "option type": "text",
                                               "additional padding": 0,
                                               "color": (255,255,255)
                                              },
                                              {"text": "earth launch site",
                                               "option type": "button",
                                               "function": None,
                                               "additional padding": 40,
                                               "color": pop_up_menus_txt_col
                                              },
                                              {"text": "CANCEL",
                                               "option type": "button",
                                               "function":None,
                                               "additional padding": 40,
                                               "color": pop_up_menus_txt_col
                                              }],
                                             cur_win_size[0] // 3.2, 100, 44, 80, 80, 40,
                                             font=pop_up_menus_txt_font,
                                             align="center",
                                             facing="vertical",
                                             has_bg=True,
                                             hover_opt_col_mode="negative",
                                             input_box_font_size=50)


    add_structure_menu_costs_init = BasicPopUpMenu([{"text": None,
                                                     "option type": "text",
                                                     "additional padding": 40,
                                                     "color": pop_up_menus_txt_col
                                                    }],
                                                   cur_win_size[0] // 3.2 + 450, 170, 20, 80, 80, 56,
                                                   font=general_menus_txt_font,
                                                   align="center",
                                                   facing="vertical",
                                                   has_bg=False,
                                                   hover_opt_col_mode="negative",
                                                   input_box_font_size=50)


    add_structure_menu_spaces_init = BasicPopUpMenu([{"text": None,
                                                      "option type": "text",
                                                      "additional padding": 40,
                                                      "color": pop_up_menus_txt_col
                                                     }],
                                                    cur_win_size[0] // 3.2 + 450, 200, 20, 80, 80, 56,
                                                    font=general_menus_txt_font,
                                                    align="center",
                                                    facing="vertical",
                                                    has_bg=False,
                                                    hover_opt_col_mode="negative",
                                                    input_box_font_size=50)

    
    def __init__(self, base, add_structure_button, add_space_button):
        super().__init__()
        self.base = base
        self.base.info_display = self
        space_occupied_in_base = [structure.space for structure in base.structures]
        self.add_structure_button = add_structure_button
        self.add_space_button = add_space_button
        
        self.space_display_font = pygame.font.Font(general_txt_font, 36)
        self.max_space_txt_obj = self.space_display_font.render("max: " + str(base.max_space), True, general_txt_col)
        self.max_space_txt_rect = self.max_space_txt_obj.get_rect()
        self.left_space_txt_obj = self.space_display_font.render("left: " + str(base.max_space - sum(space_occupied_in_base)), True, general_txt_col)
        self.left_space_txt_rect = self.left_space_txt_obj.get_rect()
        self.max_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y)
        self.left_space_txt_rect.topleft = (self.add_structure_button.x + 310, self.add_structure_button.y + 50)

        def add_structure_func():
            self.add_structure_menu.hidden = False


        def add_space_func():
            '''
            Adds building space to a building
            '''
            global globalcoins
            
            space_cost = base.base_space_cost
            for i in range(0, base.max_space - base.initial_space):
                space_cost *= base.space_cost_multiplier

            if globalcoins >= space_cost:
                base.max_space += 1
                print("space is added in " + base.name + ", now the maximum space is", base.max_space)
                globalcoins -= space_cost

        self.add_structure_button.function = add_structure_func
        self.add_space_button.function = add_space_func

        self.add_structure_menu = BaseInfoDisplay.add_structure_menu_init.copy()
        self.add_structure_menu.hidden = True
        
        for i, option in enumerate(self.add_structure_menu.options):
            if i > 0:
                option["function"] = bind_info_display_menu_funcs(self)[i-1]

        #displays the costs of the structures | the cost is managed in the PlanetBuilding classes so they can change accordingly to the context
        self.local_menu_costs = [eval('self.base.' + cost, {'self':self}) for cost in BaseInfoDisplay.menu_costs]
        
        self.add_structure_menu_costs = BaseInfoDisplay.add_structure_menu_costs_init.copy()
        self.add_structure_menu_costs.hidden = True

        options_copy = self.add_structure_menu_costs.options.copy()
        for i, option in enumerate(options_copy):
            option["text"] = compress_number_value_in_str(self.local_menu_costs[i])+"  G"
        self.add_structure_menu_costs.change_options(options_copy)

        #displays the space occupied by the structures | the space is managed in the PlanetBuildingStructure classes
        self.add_structure_menu_spaces = BaseInfoDisplay.add_structure_menu_spaces_init.copy()
        self.add_structure_menu_spaces.hidden = True

        options_copy = self.add_structure_menu_spaces.options.copy()
        for i, option in enumerate(options_copy):
            option["text"] = str(BaseInfoDisplay.menu_spaces[i])
        self.add_structure_menu_spaces.change_options(options_copy)


    @staticmethod
    def register_menu_update(new_menu_option : dict, new_menu_func : str, new_menu_cost_option : dict, new_menu_cost : str, new_menu_space_option : dict, new_menu_space : int):
        global current_planet

        print('\n'*3, new_menu_option, '\n', new_menu_func, '\n'*3)

        BaseInfoDisplay.menu_funcs.insert(-1, new_menu_func)
        new_options = BaseInfoDisplay.add_structure_menu_init.options.copy()
        new_options.insert(-1, new_menu_option)
        BaseInfoDisplay.add_structure_menu_init.change_options(new_options)

        new_options = BaseInfoDisplay.add_structure_menu_costs_init.options.copy()
        new_options.append(new_menu_cost_option)
        BaseInfoDisplay.add_structure_menu_costs_init.change_options(new_options)
        BaseInfoDisplay.menu_costs.append(new_menu_cost)

        new_options = BaseInfoDisplay.add_structure_menu_spaces_init.options.copy()
        new_options.append(new_menu_space_option)
        BaseInfoDisplay.add_structure_menu_spaces_init.change_options(new_options)
        BaseInfoDisplay.menu_spaces.append(str(new_menu_space))

        for base in current_planet.bases:

            #adds the option to build the structure on a colony
            funcs = [option["function"] for option in base.info_display.add_structure_menu.options[1:]]
            for option in base.info_display.add_structure_menu.options[1:]: #removes the functions in the menu options to make a deep copy
                option["function"] = None
                
            new_options = copy.deepcopy(base.info_display.add_structure_menu.options)
            
            for i, option in enumerate(base.info_display.add_structure_menu.options[1:]): #re-adds the functions to both the original menu options and the copied one
                option["function"] = funcs[i]
            for i, option in enumerate(new_options[1:]):
                option["function"] = funcs[i]
                
            new_options.insert(-1, new_menu_option.copy())
            new_options[-2]["function"] = bind_info_display_menu_funcs(base.info_display)[-2] #a function specific for the colony is created
            base.info_display.add_structure_menu.change_options(new_options)

            new_options = copy.deepcopy(base.info_display.add_structure_menu_costs.options) #adds the cost indicator
            new_options.append(new_menu_cost_option)
            new_options[-1]["text"] = compress_number_value_in_str(eval('''base.'''+new_menu_cost))+"  G"
            base.info_display.add_structure_menu_costs.change_options(new_options)
            
            base.info_display.local_menu_costs.append(eval('''base.'''+new_menu_cost))

            new_options = copy.deepcopy(base.info_display.add_structure_menu_spaces.options) #adds the space required indicator
            new_options.append(new_menu_space_option)
            new_options[-1]["text"] = str(new_menu_space)
            base.info_display.add_structure_menu_spaces.change_options(new_options)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            self.add_structure_button.event_update(event)
            self.add_space_button.event_update(event)
            self.add_structure_menu.event_update(event)
            self.add_structure_menu_costs.event_update(event)
            self.add_structure_menu_spaces.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()

            #updates building space indicators
            space_occupied_in_base = [structure.space for structure in self.base.structures]

            self.max_space_txt_obj = self.space_display_font.render("max: " + str(self.base.max_space), True, general_txt_col)
            self.left_space_txt_obj = self.space_display_font.render("left: " + str(self.base.max_space - sum(space_occupied_in_base)), True, general_txt_col)
            
            if self.add_structure_menu.hidden: #syncs the visibility of the secondary menus (costs, spaces) with the main one (structures)
                self.add_structure_menu_costs.hidden = True
                self.add_structure_menu_spaces.hidden = True
            else:
                self.add_structure_menu_costs.hidden = False
                self.add_structure_menu_spaces.hidden = False
                
            self.add_structure_button.update()
            self.add_space_button.update()
            self.add_structure_menu.update()
            self.add_structure_menu_costs.update()
            self.add_structure_menu_spaces.update()

            if not menus["pause menu"].hidden:
                self.add_structure_menu.hidden = True


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            win.blit(self.max_space_txt_obj, self.max_space_txt_rect)
            win.blit(self.left_space_txt_obj, self.left_space_txt_rect)
            self.add_structure_button.draw()
            self.add_space_button.draw()
            self.add_structure_menu.draw()
            self.add_structure_menu_costs.draw()
            self.add_structure_menu_spaces.draw()



class ResearchGrade:
    def __init__(self, requisite_exp):
        self.is_researched = False
        self.requisite_exp = requisite_exp
        self.next_researches = {}


    def can_research(self):
        if eval(self.requisite_exp, globals()):
            return True
        else:
            return False



class Research:
    def __init__(self, research_func, probability, category):
        self.is_researched = False
        self.research_func = research_func
        self.probability = probability
        self.category = category
        self.next_researches = {}


    def can_research(self):
        if random.randint(0, int('9'*research_slowness)) < self.probability:
            return True
        else:
            return False



class ResearchTree:
    root = ResearchGrade(r"True")
    researchables = [root]


    def space_port_research_func():
        print("\nRESEARCH - space port is researched for cities\n")
        notify_system.stack_append(Notification(notify_system,
                                        "new technology researched",
                                        "Your research effort has brought to the interplanetary colonisation market a new structure:"\
                                        " the space port. At this point in the development cycle the structure has no use but wait till"\
                                        " the next update!",
                                        "researched in year: "+str(date["Y"])))
        CityInfoDisplay.register_menu_update({"text": "space port",
                                              "option type": "button",
                                              "function": None,
                                              "additional padding": 0,
                                              "color": pop_up_menus_txt_col
                                             }, 'add_space_port',
                                             {"text": None,
                                              "option type": "text",
                                              "additional padding": 0,
                                              "color": pop_up_menus_txt_col
                                             }, 'space_port_cost',
                                             {"text": None,
                                              "option type": "text",
                                              "additional padding": 0,
                                              "color": pop_up_menus_txt_col
                                             }, SpacePort.get_space())
    space_port = Research(space_port_research_func, 5, "space travel")
    root.next_researches["space port"] = space_port                                                              #space port


    terraforming = ResearchGrade(r"globalcoins > 10000000")
    root.next_researches["terraforming"] = terraforming                                                          #TERRAFORMING GRADE


    def temperature_net_research_func():
        print("\nRESEARCH - temperature net is researched for colonies\n")
        notify_system.stack_append(Notification(notify_system,
                                        "new technology researched",
                                        "Your research effort has brought to the interplanetary colonisation market a new structure:"\
                                        " the temperature net. At this point in the development cycle the structure has no use but wait"\
                                        " till the next update!",
                                        "researched in year: "+str(date["Y"])))
        ColonyInfoDisplay.register_menu_update({"text": "temperature net",
                                                "option type": "button",
                                                "function": None,
                                                "additional padding": 0,
                                                "color": pop_up_menus_txt_col
                                               }, 'add_temperature_net',
                                               {"text": None,
                                                "option type": "text",
                                                "additional padding": 0,
                                                "color": pop_up_menus_txt_col
                                               }, 'temperature_net_cost',
                                               {"text": None,
                                                "option type": "text",
                                                "additional padding": 0,
                                                "color": pop_up_menus_txt_col
                                               }, TemperatureNet.get_space())
    temperature_net = Research(temperature_net_research_func, 5, "global temperature alteration")
    terraforming.next_researches["temperature net"] = temperature_net                                            #temperature net


    def pressure_net_research_func():
        print("\nRESEARCH - pressure net is researched for colonies\n")
        notify_system.stack_append(Notification(notify_system,
                                        "new technology researched",
                                        "Your research effort has brought to the interplanetary colonisation market a new structure:"\
                                        " the pressure net. At this point in the development cycle the structure has no use but wait"\
                                        " till the next update!",
                                        "researched in year: "+str(date["Y"])))
        ColonyInfoDisplay.register_menu_update({"text": "pressure net",
                                                "option type": "button",
                                                "function": None,
                                                "additional padding": 0,
                                                "color": pop_up_menus_txt_col
                                               }, 'add_pressure_net',
                                               {"text": None,
                                                "option type": "text",
                                                "additional padding": 0,
                                                "color": pop_up_menus_txt_col
                                               }, 'pressure_net_cost',
                                               {"text": None,
                                                "option type": "text",
                                                "additional padding": 0,
                                                "color": pop_up_menus_txt_col
                                               }, PressureNet.get_space())
    pressure_net = Research(pressure_net_research_func, 5, "global pressure alteration")
    terraforming.next_researches["pressure net"] = pressure_net                                                  #pressure net


    @classmethod
    def random_research(cls):
        grades = [grade for grade in cls.researchables if type(grade) == ResearchGrade]
        researchs = [res for res in cls.researchables if type(res) == Research]
        random.shuffle(researchs)

        if researchs != []:
            if researchs[0].can_research():
                researchs[0].is_researched = True
                researchs[0].research_func()
                
                cls.researchables.remove(researchs[0])
                for nxt in researchs[0].next_researches.values(): #adds the next branches of the tree
                    cls.researchables.append(nxt)
                return researchs[0]
            
        else: #next grade is unlockable only if all researches of the previous grades are already unlocked
            for grade in grades:
                if grade.can_research():
                    grade.is_researched = True

                    cls.researchables.remove(grade)
                    for nxt in grade.next_researches.values():
                        cls.researchables.append(nxt)
                    return grade



class FirstStage:
    def __init__(self, name):
        self.name = name
        self.image_path = os.path.join("images", "vehicle design", self.name + " - first stage.png")


    def select(self):
        if VehicleDesignSystem.design_mode:
            VehicleDesignSystem.selected_rocket.first_stage = self
            if VehicleDesignSystem.selected_rocket.first_stage and VehicleDesignSystem.selected_rocket.second_stage and VehicleDesignSystem.selected_rocket.payload:
                VehicleDesignSystem.selected_rocket.update_parts()



class SecondStage:
    def __init__(self, name):
        self.name = name
        self.image_path = os.path.join("images", "vehicle design", self.name + " - second stage.png")


    def select(self):
        if VehicleDesignSystem.design_mode:
            VehicleDesignSystem.selected_rocket.second_stage = self
            if VehicleDesignSystem.selected_rocket.first_stage and VehicleDesignSystem.selected_rocket.second_stage and VehicleDesignSystem.selected_rocket.payload:
                VehicleDesignSystem.selected_rocket.update_parts()



class Payload:
    def __init__(self, name):
        self.name = name
        self.image_path = os.path.join("images", "vehicle design", self.name + " - payload.png")


    def select(self):
        if VehicleDesignSystem.design_mode:
            VehicleDesignSystem.selected_rocket.payload = self
            if VehicleDesignSystem.selected_rocket.first_stage and VehicleDesignSystem.selected_rocket.second_stage and VehicleDesignSystem.selected_rocket.payload:
                VehicleDesignSystem.selected_rocket.update_parts()



class AuxiliarySystem:
    image = pygame.image.load(os.path.join("images", "vehicle design", "auxiliary systems icon.png"))
    
    def __init__(self, name):
        self.name = name


    def select(self):
        if VehicleDesignSystem.design_mode:
            VehicleDesignSystem.selected_rocket.auxiliary_system = self



class Rocket(GameObject):
    x = 60
    y = 310
    
    def __init__(self, name, first_stage=None, second_stage=None, payload=None, auxiliary_systems=None):
        super().__init__()
        VehicleDesignSystem.all_rockets.append(self)
        self.name = name
        self.first_stage = first_stage
        self.second_stage = second_stage
        self.payload = payload
        self.auxiliary_systems = auxiliary_systems

        self.no_sufficient_parts_txt_obj = pygame.font.Font(general_txt_font, 30).render("choose rocket parts", True, dim_txt_col)
        self.no_sufficient_parts_txt_rect = self.no_sufficient_parts_txt_obj.get_rect()
        self.no_sufficient_parts_txt_rect.topleft = (70, 500)

        self.first_stage_img = self.second_stage_img = self.payload_img = None
        self.first_stage_offsetY = self.second_stage_offsetY = self.payload_offsetY = None
        self.first_stage_img_rect = self.second_stage_img_rect = self.payload_img_rect = None
        self.first_stage_img_surf = self.second_stage_img_surf = self.payload_img_surf = None
        self.first_stage_img_surf_rect = self.second_stage_img_surf_rect = self.payload_img_surf_rect = None
        self.rocket_img_surf = None

        if self.first_stage and self.second_stage and self.payload:
            self.update_parts()


    def update_parts(self):
        self.first_stage_img = pygame.image.load(self.first_stage.image_path)
        self.second_stage_img = pygame.image.load(self.second_stage.image_path)
        self.payload_img = pygame.image.load(self.payload.image_path)
        self.first_stage_offsetY = pygame.Surface.get_bounding_rect(self.first_stage_img).y + 5
        self.second_stage_offsetY = pygame.Surface.get_bounding_rect(self.second_stage_img).y + 5
        self.payload_offsetY = pygame.Surface.get_bounding_rect(self.payload_img).y
        self.first_stage_img_rect = self.first_stage_img.get_rect()
        self.second_stage_img_rect = self.second_stage_img.get_rect()
        self.payload_img_rect = self.payload_img.get_rect()
        self.first_stage_img_surf = pygame.Surface((self.first_stage_img_rect.w, self.first_stage_img_rect.h - self.first_stage_offsetY))
        self.second_stage_img_surf = pygame.Surface((self.second_stage_img_rect.w, self.second_stage_img_rect.h - self.second_stage_offsetY))
        self.payload_img_surf = pygame.Surface((self.payload_img_rect.w, self.payload_img_rect.h - self.payload_offsetY))
        self.first_stage_img_surf.fill((51, 0, 51))
        self.second_stage_img_surf.fill((51, 0, 51))
        self.payload_img_surf.fill((51, 0, 51))
        self.first_stage_img_surf.set_colorkey((51, 0, 51))
        self.second_stage_img_surf.set_colorkey((51, 0, 51))
        self.payload_img_surf.set_colorkey((51, 0, 51))
        self.first_stage_img_surf.blit(self.first_stage_img, (0, -self.first_stage_offsetY))
        self.second_stage_img_surf.blit(self.second_stage_img, (0, -self.second_stage_offsetY))
        self.payload_img_surf.blit(self.payload_img, (0, -self.payload_offsetY))
        self.first_stage_img_surf_rect = self.first_stage_img_surf.get_rect()
        self.second_stage_img_surf_rect = self.second_stage_img_surf.get_rect()
        self.payload_img_surf_rect = self.payload_img_surf.get_rect()

        self.rocket_img_surf = pygame.Surface((self.first_stage_img_rect.w, self.first_stage_img_surf_rect.h + self.second_stage_img_surf_rect.h + self.payload_img_surf_rect.h))
        self.rocket_img_surf.fill((51, 0, 51))
        self.rocket_img_surf.set_colorkey((51, 0, 51))
        self.rocket_img_surf_rect = self.rocket_img_surf.get_rect()
        self.first_stage_img_surf_rect.center = (self.rocket_img_surf_rect.w // 2, 0)
        self.second_stage_img_surf_rect.center = (self.rocket_img_surf_rect.w // 2, 0)
        self.payload_img_surf_rect.center = (self.rocket_img_surf_rect.w // 2, 0)
        self.rocket_img_surf.blit(self.payload_img_surf, (self.payload_img_surf_rect.x, 0))
        self.rocket_img_surf.blit(self.second_stage_img_surf, (self.second_stage_img_surf_rect.x, self.payload_img_surf_rect.h))
        self.rocket_img_surf.blit(self.first_stage_img_surf, (self.first_stage_img_surf_rect.x, self.payload_img_surf_rect.h + self.second_stage_img_surf_rect.h))


    def select(self):
        global current_scene
        VehicleDesignSystem.selected_rocket = self
        VehicleDesignSystem.all_rockets_menu.is_hidden = True
        current_scene = "vehicle design view"
        VehicleDesignSystem.all_rockets_menu.hidden = True


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if self.first_stage and self.second_stage and self.payload:
                scale = (int(self.rocket_img_surf_rect.w * VehicleDesignSystem.rocket_draw_height_lock / self.rocket_img_surf_rect.h), VehicleDesignSystem.rocket_draw_height_lock)
                scaled_rocket_surf = pygame.transform.scale(self.rocket_img_surf, scale)
                win.blit(scaled_rocket_surf, (Rocket.x, Rocket.y))
            else:
                win.blit(self.no_sufficient_parts_txt_obj, self.no_sufficient_parts_txt_rect)



class VehicleDesignSection:
    all_sections = [] #to easily communicate between sections
    
    rect = Rect(500, 300, 1000, 550)
    is_selected = False

    def return_function():
        global current_scene
        current_scene = "vehicle design view"
        for section in VehicleDesignSection.all_sections:
            section.is_selected = False

    return_func = return_function
    return_img_path = os.path.join("images", "return icon.png")

    @classmethod
    def select(cls):
        if cls is VehicleDesignSection:
            raise GameException("class VehicleDesignSection's functions can't be accessed in game")
        for section in cls.all_sections:
            section.is_selected = False
        cls.is_selected = True


    @classmethod
    def event_update(cls, event):
        if cls is VehicleDesignSection:
            raise GameException("class VehicleDesignSection's functions can't be accessed in game")


    @classmethod
    def update(cls):
        if cls is VehicleDesignSection:
            raise GameException("class VehicleDesignSection's functions can't be accessed in game")


    @classmethod
    def draw(cls):
        if cls is VehicleDesignSection:
            raise GameException("class VehicleDesignSection's functions can't be accessed in game")
        #pygame.draw.rect(win, (255,0,0), cls.rect)



class FirstStageDesignSection(VehicleDesignSection):
    rect = VehicleDesignSection.rect
    
    title_txt_obj = pygame.font.Font(general_txt_font, 56).render("first stage", True, general_txt_col)
    title_txt_rect = title_txt_obj.get_rect()
    title_txt_rect.centerx = VehicleDesignSection.rect.x + VehicleDesignSection.rect.w // 2
    title_txt_rect.y = VehicleDesignSection.rect.y

    return_button = ImageButton(VehicleDesignSection.return_func,
                                VehicleDesignSection.return_img_path, VehicleDesignSection.return_img_path,
                                rect.x + rect.w - 50, rect.y + 50, 50, 50, rect.x + rect.w - 50, rect.y + 50, 50, 50,
                                {"scale": (50, 50),
                                 "image color": general_txt_col,
                                 "hovered image color": iter_operation(general_txt_col, r'+', 'hover_delta_col')})

    def specs_option_func():
        global current_scene
        if current_scene[:19] == "vehicle design view":
            current_scene = "vehicle design view / specs"

    def change_part_option_func():
        global current_scene
        if current_scene[:19] == "vehicle design view" and VehicleDesignSystem.design_mode:
            current_scene = "vehicle design view / change part"

    rocket_edit_menu = BasicPopUpMenu([{"text": "specifics",
                                        "option type": "button",
                                        "function": specs_option_func,
                                        "additional padding": 0,
                                        "color": general_txt_col
                                       },
                                       {"text": "change part",
                                        "option type": "button",
                                        "function": change_part_option_func,
                                        "additional padding": 0,
                                        "color": general_txt_col
                                       }],
                                      rect.x, rect.y + 120,
                                      font_size = 30,
                                      padX = 0, padY = 0, unit_pad = 50,
                                      font = general_txt_font,
                                      align = "left",
                                      hover_opt_col_mode = "positive",
                                      has_bg = False,
                                      facing = "horizontal",
                                      select_opt_mode = "on hover",
                                      input_box_font_size = 50)

    first_stages_menu_options = []
    first_stages_menu = ImageMenu(first_stages_menu_options,
                                  rect.x, rect.y + 190, rect.w, 40, 40,
                                  has_borders=True, border_config=(general_txt_col, 8, True, "positive", hover_delta_col), image_scale=(120, 160), save_last_selection=True)


    @classmethod
    def add_part(cls, part):
        cls.first_stages_menu_options.append((part.select, os.path.join("vehicle design", part.name + " - first stage.png")))
        cls.first_stages_menu.change_options(cls.first_stages_menu_options)


    @classmethod
    def event_update(cls, event):
        global current_scene
        super().event_update(event)
        cls.return_button.event_update(event)
        cls.rocket_edit_menu.event_update(event)
        if current_scene == "vehicle design view / change part":
            cls.first_stages_menu.event_update(event)


    @classmethod
    def update(cls):
        global current_scene
        super().update()
        cls.return_button.update()
        cls.rocket_edit_menu.update()
        if current_scene == "vehicle design view / change part":
            cls.first_stages_menu.update()

    
    @classmethod
    def draw(cls):
        global current_scene
        super().draw()
        win.blit(cls.title_txt_obj, cls.title_txt_rect)
        cls.return_button.draw()
        cls.rocket_edit_menu.draw()
        if current_scene == "vehicle design view / change part":
            cls.first_stages_menu.draw()



class SecondStageDesignSection(VehicleDesignSection):
    rect = VehicleDesignSection.rect
    
    title_txt_obj = pygame.font.Font(general_txt_font, 56).render("second stage", True, general_txt_col)
    title_txt_rect = title_txt_obj.get_rect()
    title_txt_rect.centerx = VehicleDesignSection.rect.x + VehicleDesignSection.rect.w // 2
    title_txt_rect.y = VehicleDesignSection.rect.y

    return_button = ImageButton(VehicleDesignSection.return_func,
                                VehicleDesignSection.return_img_path, VehicleDesignSection.return_img_path,
                                rect.x + rect.w - 50, rect.y + 50, 50, 50, rect.x + rect.w - 50, rect.y + 50, 50, 50,
                                {"scale": (50, 50),
                                 "image color": general_txt_col,
                                 "hovered image color": iter_operation(general_txt_col, r'+', 'hover_delta_col')})

    def specs_option_func():
        global current_scene
        if current_scene[:19] == "vehicle design view":
            current_scene = "vehicle design view / specs"

    def change_part_option_func():
        global current_scene
        if current_scene[:19] == "vehicle design view" and VehicleDesignSystem.design_mode:
            current_scene = "vehicle design view / change part"

    rocket_edit_menu = BasicPopUpMenu([{"text": "specifics",
                                        "option type": "button",
                                        "function": specs_option_func,
                                        "additional padding": 0,
                                        "color": general_txt_col
                                       },
                                       {"text": "change part",
                                        "option type": "button",
                                        "function": change_part_option_func,
                                        "additional padding": 0,
                                        "color": general_txt_col
                                       }],
                                      rect.x, rect.y + 120,
                                      font_size = 30,
                                      padX = 0, padY = 0, unit_pad = 50,
                                      font = general_txt_font,
                                      align = "left",
                                      hover_opt_col_mode = "positive",
                                      has_bg = False,
                                      facing = "horizontal",
                                      select_opt_mode = "on hover",
                                      input_box_font_size = 50)

    second_stages_menu_options = []
    second_stages_menu = ImageMenu(second_stages_menu_options,
                                   rect.x, rect.y + 190, rect.w, 40, 40,
                                   has_borders=True, border_config=(general_txt_col, 8, True, "positive", hover_delta_col), image_scale=(90, 180), save_last_selection=True)


    @classmethod
    def add_part(cls, part):
        cls.second_stages_menu_options.append((part.select, os.path.join("vehicle design", part.name + " - second stage.png")))
        cls.second_stages_menu.change_options(cls.second_stages_menu_options)


    @classmethod
    def event_update(cls, event):
        global current_scene
        super().event_update(event)
        cls.return_button.event_update(event)
        cls.rocket_edit_menu.event_update(event)
        if current_scene == "vehicle design view / change part":
            cls.second_stages_menu.event_update(event)


    @classmethod
    def update(cls):
        global current_scene
        super().update()
        cls.return_button.update()
        cls.rocket_edit_menu.update()
        if current_scene == "vehicle design view / change part":
            cls.second_stages_menu.update()

    
    @classmethod
    def draw(cls):
        global current_scene
        super().draw()
        win.blit(cls.title_txt_obj, cls.title_txt_rect)
        cls.return_button.draw()
        cls.rocket_edit_menu.draw()
        if current_scene == "vehicle design view / change part":
            cls.second_stages_menu.draw()



class PayloadDesignSection(VehicleDesignSection):
    rect = VehicleDesignSection.rect
    
    title_txt_obj = pygame.font.Font(general_txt_font, 58).render("payload", True, general_txt_col)
    title_txt_rect = title_txt_obj.get_rect()
    title_txt_rect.centerx = VehicleDesignSection.rect.x + VehicleDesignSection.rect.w // 2
    title_txt_rect.y = VehicleDesignSection.rect.y

    return_button = ImageButton(VehicleDesignSection.return_func,
                                VehicleDesignSection.return_img_path, VehicleDesignSection.return_img_path,
                                rect.x + rect.w - 50, rect.y + 50, 50, 50, rect.x + rect.w - 50, rect.y + 50, 50, 50,
                                {"scale": (50, 50),
                                 "image color": general_txt_col,
                                 "hovered image color": iter_operation(general_txt_col, r'+', 'hover_delta_col')})

    def specs_option_func():
        global current_scene
        if current_scene[:19] == "vehicle design view":
            current_scene = "vehicle design view / specs"

    def change_part_option_func():
        global current_scene
        if current_scene[:19] == "vehicle design view" and VehicleDesignSystem.design_mode:
            current_scene = "vehicle design view / change part"

    rocket_edit_menu = BasicPopUpMenu([{"text": "specifics",
                                        "option type": "button",
                                        "function": specs_option_func,
                                        "additional padding": 0,
                                        "color": general_txt_col
                                       },
                                       {"text": "change part",
                                        "option type": "button",
                                        "function": change_part_option_func,
                                        "additional padding": 0,
                                        "color": general_txt_col
                                       }],
                                      rect.x, rect.y + 120,
                                      font_size = 30,
                                      padX = 0, padY = 0, unit_pad = 50,
                                      font = general_txt_font,
                                      align = "left",
                                      hover_opt_col_mode = "positive",
                                      has_bg = False,
                                      facing = "horizontal",
                                      select_opt_mode = "on hover",
                                      input_box_font_size = 50)

    payloads_menu_options = []
    payloads_menu = ImageMenu(payloads_menu_options,
                              rect.x, rect.y + 190, rect.w, 40, 40,
                              has_borders=True, border_config=(general_txt_col, 8, True, "positive", hover_delta_col), image_scale=(150, 150), save_last_selection=True)


    @classmethod
    def add_part(cls, part):
        cls.payloads_menu_options.append((part.select, os.path.join("vehicle design", part.name + " - payload.png")))
        cls.payloads_menu.change_options(cls.payloads_menu_options)


    @classmethod
    def event_update(cls, event):
        global current_scene
        super().event_update(event)
        cls.return_button.event_update(event)
        cls.rocket_edit_menu.event_update(event)
        if current_scene == "vehicle design view / change part":
            cls.payloads_menu.event_update(event)


    @classmethod
    def update(cls):
        global current_scene
        super().update()
        cls.return_button.update()
        cls.rocket_edit_menu.update()
        if current_scene == "vehicle design view / change part":
            cls.payloads_menu.update()

    
    @classmethod
    def draw(cls):
        global current_scene
        super().draw()
        win.blit(cls.title_txt_obj, cls.title_txt_rect)
        cls.return_button.draw()
        cls.rocket_edit_menu.draw()
        if current_scene == "vehicle design view / change part":
            cls.payloads_menu.draw()



class AuxiliarySystemDesignSection(VehicleDesignSection):
    rect = VehicleDesignSection.rect
    
    title_txt_obj = pygame.font.Font(general_txt_font, 56).render("auxiliary system", True, general_txt_col)
    title_txt_rect = title_txt_obj.get_rect()
    title_txt_rect.centerx = VehicleDesignSection.rect.x + VehicleDesignSection.rect.w // 2
    title_txt_rect.y = VehicleDesignSection.rect.y

    return_button = ImageButton(VehicleDesignSection.return_func,
                                VehicleDesignSection.return_img_path, VehicleDesignSection.return_img_path,
                                rect.x + rect.w - 50, rect.y + 50, 50, 50, rect.x + rect.w - 50, rect.y + 50, 50, 50,
                                {"scale": (50, 50),
                                 "image color": general_txt_col,
                                 "hovered image color": iter_operation(general_txt_col, r'+', 'hover_delta_col')})

    @classmethod
    def event_update(cls, event):
        super().event_update(event)
        cls.return_button.event_update(event)


    @classmethod
    def update(cls):
        super().update()
        cls.return_button.update()

    
    @classmethod
    def draw(cls):
        super().draw()
        win.blit(cls.title_txt_obj, cls.title_txt_rect)
        cls.return_button.draw()



VehicleDesignSection.all_sections = [FirstStageDesignSection, SecondStageDesignSection, PayloadDesignSection, AuxiliarySystemDesignSection]



class VehicleMenuOption(GameObject):
    def __init__(self, menu, vehicle, y, rocket_img, name_txt1, name_txt2):
        super().__init__()
        self.is_hovered = False
        
        self.vehicle = vehicle
        self.menu = menu
        self.x = menu.x
        self.y = y
        self.rocket_img_obj = rocket_img
        self.name_txt_obj1 = name_txt1
        self.name_txt_obj2 = name_txt2

        self.rocket_img_rect = self.rocket_img_obj.get_rect()
        self.rocket_img_rect.center = (self.menu.box_side // 2, self.menu.box_side // 2)
        self.rocket_img_rect.x += self.x
        self.rocket_img_rect.y += self.y
        self.name_txt_rect1 = self.name_txt_obj1.get_rect()
        self.name_txt_rect1.topleft = (self.rocket_img_rect.x + self.menu.box_side, self.rocket_img_rect.y)
        self.name_txt_rect2 = self.name_txt_obj2.get_rect()
        self.name_txt_rect2.topleft = (self.rocket_img_rect.x + self.menu.box_side, self.name_txt_rect1.y + self.name_txt_rect1.h)


    def event_update(self, event):
        if not self.event_update_blocked:
            super().event_update(event)
            if Rect(self.menu.x, self.y, self.menu.box_side, self.menu.box_side).collidepoint(pygame.mouse.get_pos()) or Rect(self.menu.x + self.menu.box_side - 80, self.y, max([self.name_txt_rect1.w, self.name_txt_rect2.w]) + 200, self.menu.box_side - 40).collidepoint(pygame.mouse.get_pos()):
                self.is_hovered = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.vehicle.select()
            else:
                self.is_hovered = False


    def update(self):
        if not self.update_blocked:
            super().update()


    def draw(self):
        if not self.draw_blocked:
            super().draw()
            if self.is_hovered:
                color = self.menu.hovered_col
            else:
                color = self.menu.color
                
            pygame.draw.rect(win, color,
                             (self.menu.x + self.menu.box_side - 80, self.y, max([self.name_txt_rect1.w, self.name_txt_rect2.w]) + 200, self.menu.box_side - 40),
                             width=3, border_radius=10)
            pygame.draw.rect(win, bg_col, (self.menu.x, self.y, self.menu.box_side, self.menu.box_side), border_radius=20)
            win.blit(self.rocket_img_obj, self.rocket_img_rect)
            win.blit(self.name_txt_obj1, self.name_txt_rect1)
            win.blit(self.name_txt_obj2, self.name_txt_rect2)
            pygame.draw.rect(win, color, (self.menu.x, self.y, self.menu.box_side, self.menu.box_side), width=10, border_radius=20)



class VehicleMenu(GameObject):
    def __init__(self, x, y, padding, vehicle_name_pyfont, box_side, color=general_txt_col, max_name_len_inline=18, hover_col_mode="positive"):
        super().__init__()
        self.options = []
        self.hidden = False
        self.x, self.y = x, y
        self.padding = padding
        self.color = color
        if hover_col_mode == "positive":
            self.hovered_col = iter_operation(self.color, r'+', hover_delta_col)
        elif hover_col_mode == "negative":
            self.hovered_col = iter_operation(self.color, r'-', hover_delta_col)
        self.vehicle_name_pyfont = vehicle_name_pyfont
        self.box_side = box_side #the box around a rocket image
        self.max_name_len_inline = max_name_len_inline


    def append(self, vehicle):
        if type(vehicle) == Rocket:
            image_rect = vehicle.rocket_img_surf.get_rect()
            image = pygame.transform.scale(vehicle.rocket_img_surf, (int(image_rect.w * (self.box_side - 30) / image_rect.h), self.box_side - 30))
        else:
            raise GameException("the type of the vehicle appended to "+str(self)+" VehicleMenu is not accepted\nvehicle object must be of type Rocket")

        #devides the name into multiple lines so it doesn't go overscreen
        if len(vehicle.name) <= self.max_name_len_inline:
            name_txt_obj1 = self.vehicle_name_pyfont.render(vehicle.name, True, self.color)
            name_txt_obj2 = self.vehicle_name_pyfont.render("", True, self.color)
        else:
            words = vehicle.name.split() #all the words in the vehicle name
            if len(words) == 1: #if the name can't be divided in lines it's then just arbitrarly divided
                line1 = vehicle.name[:self.max_name_len_inline]
                line2 = vehicle.name[self.max_name_len_inline:]
            else: #if the name instead has multiple words line1 consists of all the words that can fit in the specific lenght limit and the rest goes to line2
                line = ""
                print(words, '\n')
                for i, word in enumerate(words):
                    if len(line + " " * i + word) <= self.max_name_len_inline:
                        line += word + " "
                    else:
                        line1 = line
                        line2 = " ".join(words[i:])
                        break
            name_txt_obj1 = self.vehicle_name_pyfont.render(line1, True, self.color)
            name_txt_obj2 = self.vehicle_name_pyfont.render(line2, True, self.color)
            
        if self.options: #if there are other options already appended the y coord of the option must consider them
            self.options.append(VehicleMenuOption(self, vehicle, self.options[-1].y + self.box_side + self.padding, image, name_txt_obj1, name_txt_obj2))
        else:
            self.options.append(VehicleMenuOption(self, vehicle, self.y, image, name_txt_obj1, name_txt_obj2))


    def event_update(self, event):
        if not self.event_update_blocked and not self.hidden:
            super().event_update(event)
            for option in self.options:
                option.event_update(event)


    def update(self):
        if not self.update_blocked:
            super().update()
            for option in self.options:
                option.update()


    def draw(self):
        if not self.draw_blocked and not self.hidden:
            super().draw()
            for option in self.options:
                option.draw()



class VehicleDesignSystem:
    rocket_draw_height_lock = 560
    
    title_txt_obj = pygame.font.Font(general_txt_font, 50).render("vehicle design", True, general_txt_col)
    title_txt_rect = title_txt_obj.get_rect()
    title_txt_rect.topleft = (80, 160)

    def select_rocket():
        pass

    def select_spacecraft():
        pass

    def select_spaceplane():
        pass

    vehicle_select_menu = ScrollDownMenu([("select vehicle type",),
                                          ("rocket", select_rocket),
                                          ("spacecraft", select_spacecraft),
                                          ("spaceplane", select_spaceplane)],
                                         x=1100, y=100, padding=30, direction="down", shift=(30, 10),
                                         config_options={"type": "text",
                                                         "font": general_txt_font,
                                                         "font size": 40,
                                                         "options hitbox size shift": 10})

    no_rocket_displayed_txt_obj = pygame.font.Font(general_txt_font, 32).render("no rocket displayed", True, dim_txt_col)
    no_rocket_displayed_txt_rect = no_rocket_displayed_txt_obj.get_rect()
    no_rocket_displayed_txt_rect.topleft = (70, 500)

    rocket_name_inp_box = InputBox(cur_win_size[0] // 10, cur_win_size[1] // 3, 1200, general_txt_font, 50, color=general_txt_col, max_txt_lenght=32, caption_text="choose rocket name")
    wait_for_rocket_name = False

    all_rockets = []
    selected_rocket = None
    design_mode = False
    designed_rocket = None
    
    def design_new_rocket_func():
        global current_scene
        current_scene = "vehicle design view"
        VehicleDesignSystem.design_mode = True
        VehicleDesignSystem.selected_rocket = Rocket('rocket_design_in_progress')

    design_new_rocket_button = TextButton(design_new_rocket_func,
                                          450, 300, 280, 50,
                                          450, 300, 280, 50,
                                          text="design new +",
                                          font=general_txt_font, font_size=26, txt_col=general_txt_col,
                                          has_box=True,
                                          fix="center",
                                          hover_opt_col_mode="positive")

    @classmethod
    def save_design_func(cls):
        if cls.design_mode:
            cls.selected_rocket.name = cls.rocket_name_inp_box.text
            cls.finalize_rocket(cls.selected_rocket)
            cls.design_mode = False
            cls.selected_rocket = None
            cls.wait_for_rocket_name = False
            FirstStageDesignSection.first_stages_menu.last_selected_i = None
            SecondStageDesignSection.second_stages_menu.last_selected_i = None
            PayloadDesignSection.payloads_menu.last_selected_i = None

    def wait_for_rocket_name_func():
        if VehicleDesignSystem.design_mode:
            VehicleDesignSystem.wait_for_rocket_name = True

    save_design_button = TextButton(wait_for_rocket_name_func,
                                    490, 380, 240, 40,
                                    490, 380, 240, 40,
                                    text="save design",
                                    font=general_txt_font, font_size=22, txt_col=general_txt_col,
                                    has_box=True,
                                    fix="center",
                                    hover_opt_col_mode="positive")

    def discard_design_func():
        if VehicleDesignSystem.design_mode:
            VehicleDesignSystem.design_mode = False
            VehicleDesignSystem.all_rockets.remove(VehicleDesignSystem.selected_rocket)
            VehicleDesignSystem.selected_rocket = None

    discard_design_button = TextButton(discard_design_func,
                                       490, 450, 240, 40,
                                       490, 450, 240, 40,
                                       text="discard",
                                       font=general_txt_font, font_size=22, txt_col=general_txt_col,
                                       has_box=True,
                                       fix="center",
                                       hover_opt_col_mode="positive")

    def view_rockets_func():
        global current_scene
        current_scene = "vehicle design view / all rockets"

    view_rockets_button = TextButton(view_rockets_func,
                                     450, 800, 280, 50,
                                     450, 800, 280, 50,
                                     text="all rockets",
                                     font=general_txt_font, font_size=26, txt_col=general_txt_col,
                                     has_box=True,
                                     fix="center",
                                     hover_opt_col_mode="positive")

    rocket_menu = BasicPopUpMenu([{"text": "first stage",
                                   "option type": "button",
                                   "function": FirstStageDesignSection.select,
                                   "additional padding": 0,
                                   "color": general_txt_col
                                  },
                                  {"text": "second stage",
                                   "option type": "button",
                                   "function": SecondStageDesignSection.select,
                                   "additional padding": 0,
                                   "color": general_txt_col
                                  },
                                  {"text": "payload",
                                   "option type": "button",
                                   "function": PayloadDesignSection.select,
                                   "additional padding": 0,
                                   "color": general_txt_col
                                  },
                                  {"text": "auxiliary system",
                                   "option type": "button",
                                   "function": AuxiliarySystemDesignSection.select,
                                   "additional padding": 0,
                                   "color": general_txt_col
                                  }],
                                 x = 800, y = 320,
                                 font_size = 58,
                                 padX = 0, padY = 0, unit_pad = 80,
                                 font = general_txt_font,
                                 align = "left",
                                 hover_opt_col_mode = "positive",
                                 has_bg = False,
                                 facing = "vertical",
                                 select_opt_mode = "on hover"
                                 )
    menus["rocket menu"] = rocket_menu

    all_rockets_menu = VehicleMenu(800, 300, 40, pygame.font.Font(general_txt_font, 40), 200)
    all_rockets_menu.hidden = True


    @classmethod
    def finalize_rocket(cls, rocket):
        cls.all_rockets_menu.append(rocket)
        cls.design_mode = False
    

    @classmethod
    def event_update(cls, event):
        global current_scene
        if cls.wait_for_rocket_name:
            cls.rocket_name_inp_box.event_update(event)
            if keys[pygame.K_RETURN]:
                cls.save_design_func()
        else:
            cls.vehicle_select_menu.event_update(event)

            section_selected = False
            if cls.selected_rocket:
                cls.selected_rocket.event_update(event)
                if not cls.vehicle_select_menu.is_expanded:
                    for section in VehicleDesignSection.all_sections:
                        if section.is_selected:
                            section.event_update(event)
                            section_selected = True
                            break
                        
                    if not section_selected and cls.all_rockets_menu.hidden:
                        cls.rocket_menu.event_update(event)

            if current_scene == "vehicle design view / all rockets" and not cls.vehicle_select_menu.is_expanded:
                cls.all_rockets_menu.event_update(event)

            if not section_selected:
                cls.design_new_rocket_button.event_update(event)
                cls.view_rockets_button.event_update(event)
                if cls.design_mode:
                    cls.save_design_button.event_update(event)
                    cls.discard_design_button.event_update(event)


    @classmethod
    def update(cls):
        global current_scene
        cls.vehicle_select_menu.update()
        cls.design_new_rocket_button.update()
        cls.view_rockets_button.update()
        cls.save_design_button.update()
        cls.discard_design_button.update()
        cls.rocket_name_inp_box.update()
        cls.all_rockets_menu.update()

        if current_scene[:19] != "vehicle design view":
            cls.wait_for_rocket_name = False
        elif current_scene == "vehicle design view / all rockets":
            cls.all_rockets_menu.hidden = False
        
        if cls.selected_rocket:
            cls.selected_rocket.update()
            if cls.design_mode:
                cls.rocket_menu.update()
                for section in VehicleDesignSection.all_sections:
                    section.update()


    @classmethod
    def draw(cls):
        cls.vehicle_select_menu.draw()

        section_selected = False
        if not cls.vehicle_select_menu.is_expanded:
            for section in VehicleDesignSection.all_sections:
                if section.is_selected:
                    section.draw()
                    section_selected = True
                    break

            if not section_selected and cls.selected_rocket and cls.all_rockets_menu.hidden:
                cls.rocket_menu.draw()
            
        if cls.selected_rocket:
            cls.selected_rocket.draw()
        else:
            win.blit(cls.no_rocket_displayed_txt_obj, cls.no_rocket_displayed_txt_rect)
        win.blit(cls.title_txt_obj, cls.title_txt_rect)

        if not section_selected:
            cls.design_new_rocket_button.draw()
            cls.view_rockets_button.draw()
            if cls.design_mode:
                cls.save_design_button.draw()
                cls.discard_design_button.draw()

            if current_scene == "vehicle design view / all rockets" and not cls.vehicle_select_menu.is_expanded:
                cls.all_rockets_menu.draw()

        if cls.wait_for_rocket_name:
            cls.rocket_name_inp_box.draw()



#==========================================================FUNCTIONS NEEDED FOR GAME OBJECTS===========================================================

def open_planet_data(mode : str, Data=None):
    '''
    Manages the files where the planets are stored.
    Data is the planet dictionary where the planets are taken from with writing operations (contains all the planet information in an ordered manner and the planet objects).
    The possible modes are:

    r - read, returns a dict containing all the data from planets saved including the planet objects
    w - write, saves in memory the data from a planet dictionary
    pk - print keys, prints the names of the planets stored in memory

    While in memory pygame.Surface objects are stored in their bytes form and when loaded they are converted back into surfaces,
    This is entering and exiting "save mode". If there are problems with save modes warnings will be printed.
    '''
    global data_path

    if mode != 'w' and Data: #makes sure the given function parameters are correct
        raise GameError("Can't override planet data if not in write mode ('w')")
    elif not(mode == 'r' or mode == 'w' or mode == 'pk'):
        raise GameError("Cannot accept "+str(mode)+" as mode to open planet data, possible modes are: r  w  pk")

    current_cwd = os.getcwd() #moves to the planet data directory
    os.chdir(data_path)
    try:
        planet_data = shelve.open('planets')
        
        if mode == 'r' or mode == 'pk':
            planets = {name: data for name, data in planet_data.items()}
            for name, data in planets.items():
                try: #restores the planet object to its non save mode form
                    data["object"].exit_save_mode(planets)
                except Exception as e:
                    print("WARNING: planet", name, "has not exited save mode.", "\nException raised was: ", e)
                for map_name, planet_map in data["maps"].items(): #does so with the information in the planet dictionary
                    try:
                        planet_map.exit_save_mode()
                    except Exception as e:
                        print("WARNING: map", map_name, "(located in a planet dictionary) of planet", name, "has not exited save mode.", "\nException raised was: ", e)
            
        elif mode == 'w':
            for name, data in Data.items():
                try: #puts the planet object in save mode
                    data["object"].enter_save_mode()
                except:
                    print("WARNING: planet", name, "has not entered save mode.")
                for map_name, planet_map in data["maps"].items(): #puts the information in the dictionary in save mode
                    try:
                        planet_map.enter_save_mode()
                    except:
                        print("WARNING: map", map_name, "(located in a planet dictionary) of planet", name, "has not entered save mode.")
                planet_data[name] = data
                
    finally:
        planet_data.close()
        os.chdir(current_cwd)

    if mode == 'r':
        return planets
    elif mode == 'pk':
        print("PLANETS STORED IN MEMORY:\n", '\n '.join([key for key in planets.keys()]),'\n')



def pause_button_func():
    global pause_menu_open
    pause_menu_open = True
    
def return_game_button_func():
    global pause_menu_open
    pause_menu_open = False
    
def quit_button_func():
    global run
    run = False

def placeholder_func():
    print("placeholder function called")

def placeholder_text_input_func(text):
    print(text)



globalcoins_counter = None
def globalcoins_counter_update_func(): #to rewrite the value in case of a change in the amount of globalcoins
    global globalcoins_counter, globalcoins
    globalcoins_counter.text = compress_number_value_in_str(globalcoins)
    globalcoins_counter.txt_object = globalcoins_counter.txt_font.render(globalcoins_counter.text, True, globalcoins_counter.txt_col)
    globalcoins_counter.txt_rect = globalcoins_counter.txt_object.get_rect()
    globalcoins_counter.txt_rect.topleft = (globalcoins_counter.x, globalcoins_counter.y)



atmosphere_display = None
def atmosphere_display_update_func():
    global atmosphere_display
    atmosphere_display.change_options([{"text":(element + ":").ljust(10) + (str(amount) + " ppm").rjust(20),
                                      "option type":"text",
                                      "additional padding":0,
                                      "color":general_txt_col} for element, amount in planets[current_planet.name]["atmosphere"].items()])



def view_building_func():
    global current_scene
    current_scene = "planet view / building view"
    current_planet.structure_view_animation.begin(True)

def return_to_main_view_func():
    global current_scene, selected_structure
    current_scene = "planet view / main"
    current_planet.structure_view_animation.stasis_permission = True
    selected_structure = None
    


def add_colony_func(text):
    global current_planet
    new_colony = Colony(TextButton(view_building_func,
                                   640,520,200,40,
                                   635,515,210,30,
                                   text="VIEW COLONY",font_size=24,txt_col=general_txt_col,
                                   fix="topleft",
                                   hover_opt_col_mode="positive"),
                        text, 40, planet_buildings_menus_default_y + 120 * len(current_planet.colonies), 60, planet_buildings_menus_default_y + 120 * len(current_planet.colonies) + 30)
    current_planet.colonies.append(new_colony)


def add_city_func(text):
    global current_planet
    new_city = City(TextButton(view_building_func,
                                640,520,200,40,
                                635,515,155,30,
                                text="VIEW CITY",font_size=24,txt_col=general_txt_col,
                                fix="topleft",
                                hover_opt_col_mode="positive"),
                    text, 40, planet_buildings_menus_default_y + 120 * len(current_planet.cities), 60, planet_buildings_menus_default_y + 120 * len(current_planet.cities) + 30)
    current_planet.cities.append(new_city)


def add_industrial_zone_func(text):
    global current_planet
    new_industrial_zone = IndustrialZone(TextButton(view_building_func,
                                       640,515,380,40,
                                       630,510,380,30,
                                       text="VIEW INDUSTRIAL ZONE",font_size=24,txt_col=general_txt_col,
                                       fix="topleft",
                                       hover_opt_col_mode="positive"),
                                text, 40, planet_buildings_menus_default_y + 120 * len(current_planet.industrial_zones), 60, planet_buildings_menus_default_y + 120 * len(current_planet.industrial_zones) + 30)
    current_planet.industrial_zones.append(new_industrial_zone)


def add_base_func(text):
    global current_planet
    new_base = Base(TextButton(view_building_func,
                                640,520,200,40,
                                635,515,155,30,
                                text="VIEW BASE",font_size=24,txt_col=general_txt_col,
                                fix="topleft",
                                hover_opt_col_mode="positive"),
                    text, 40, planet_buildings_menus_default_y + 120 * len(current_planet.bases), 60, planet_buildings_menus_default_y + 120 * len(current_planet.bases) + 30)
    current_planet.bases.append(new_base)



def colonies_section_func(): #selects the colonies menu so colonies are displayed
    global selected_build_menu, menus
    selected_build_menu = menus["add colony menu"]
    menus["add colony menu"].hidden = False
    menus["add city menu"].hidden = True
    menus["add industrial zone menu"].hidden = True
    menus["add base menu"].hidden = True


def cities_section_func(): #selects the cities menu so cities are displayed
    global selected_build_menu, menus
    selected_build_menu = menus["add city menu"]
    menus["add colony menu"].hidden = True
    menus["add city menu"].hidden = False
    menus["add industrial zone menu"].hidden = True
    menus["add base menu"].hidden = True


def industrial_zones_section_func(): #selects the industrial zones menu so industrial zones are displayed
    global selected_build_menu, menus
    selected_build_menu = menus["add industrial zone menu"]
    menus["add colony menu"].hidden = True
    menus["add city menu"].hidden = True
    menus["add industrial zone menu"].hidden = False
    menus["add base menu"].hidden = True


def bases_section_func(): #selects the bases menu so bases are displayed
    global selected_build_menu, menus
    selected_build_menu = menus["add base menu"]
    menus["add colony menu"].hidden = True
    menus["add city menu"].hidden = True
    menus["add industrial zone menu"].hidden = True
    menus["add base menu"].hidden = False



def stats_button_func(): #changes the scene to view planet stats
    global selected_menu, current_scene, selected_structure
    selected_structure = None
    if current_scene[:16] != "planet data view":
        current_scene = "planet data view / main"
        selected_menu = None
    else:
        current_scene = "planet view / main"
        selected_menu = menus["planet buildings menu"]



def main_stats_button_func():
    global current_scene
    if current_scene != "planet data view / main":
        current_scene = "planet data view / main"


def atmosphere_stats_button_func():
    global current_scene
    if current_scene != "planet data view / atmosphere":
        current_scene = "planet data view / atmosphere"


def constant_stats_button_func():
    global current_scene
    if current_scene != "planet data view / constant":
        current_scene = "planet data view / constant"


def oceans_stats_button_func():
    global current_scene
    if current_scene != "planet data view / oceans":
        current_scene = "planet data view / oceans"



def vehicle_design_button_func(): #changes the scene to view the interface for building the space vehicles
    global selected_menu, current_scene, selected_structure
    selected_structure = None
    if current_scene[:19] != "vehicle design view":
        current_scene = "vehicle design view / main"
        selected_menu = menus["rocket menu"]
    else:
        current_scene = "planet view / main"
        selected_menu = menus["planet buildings menu"]
        for section in VehicleDesignSection.all_sections:
            if section.is_selected:
                section.is_selected = False
                break

#=====================================================================GAME OBJECTS=====================================================================

dummy = TestDummy(500, 500)

dummies = [TestDummy(500, 400), TestDummy(600, 500), TestDummy(700, 600)]
dummies_anim_group = MoveAnimationGroup([200, 100], speed=5, back_n_fourth=True, stasis_time=1, reverse=True, reverse_speed=10)
for dummy_obj in dummies:
    dummies_anim_group.append(dummy_obj)


test_inventory = Inventory("test inventory", 60, 480, 8, 6, 40, 15)
names = ["test" + str(i) for i in range(1, 4)]
for i in range(3):
    obj = InventoryObject(names[i], test_inventory)
    if not test_inventory.append(obj):
        InventoryObject.all_objects.remove(obj)
        del obj


FirstStageDesignSection.add_part(FirstStage("first stage test"))
FirstStageDesignSection.add_part(FirstStage("first stage test2"))
FirstStageDesignSection.add_part(FirstStage("first stage test3"))

SecondStageDesignSection.add_part(SecondStage("second stage test"))

PayloadDesignSection.add_part(Payload("payload test"))
PayloadDesignSection.add_part(Payload("payload test2"))


notify_system = NotifySystem()
'''
notify_system.stack_append(Notification(notify_system,
                                        "this is a title",
                                        "Here is some text getting displayed in the notification."\
                                        " This is useful for testing and demostrating the functionalities"\
                                        " of the notification system which is really important in the"\
                                        " development of the game so it must be finished really quickly."\
                                        " Besides, it's important to communicate to the player the things"\
                                        " happening inside the game without obligating them to navigate"\
                                        " through some complicate menus just to gain the information they"\
                                        " need. This will be mostly used paired with management related "\
                                        "mechanics such as trends, problematics raised, etc, and also with"\
                                        " randomly occourring events such as new discoveries or natural"\
                                        " disasters. This here text is useful for testing the reading"\
                                        "functionalities of the notify system like the space occupied by"\
                                        "each text part in a notification and the way to scroll through"\
                                        " long text.",
                                        "this one instead is a caption"))
'''   

menus["pause menu"] = BasicPopUpMenu([{
                                       "text": "return to game",
                                       "option type": "button",
                                       "additional padding": 0,
                                       "function": return_game_button_func,
                                       "color": pop_up_menus_txt_col
                                      },
                                      {
                                       "text": "useless option 1",
                                       "option type": "button",
                                       "additional padding": 30,
                                       "function": placeholder_func,
                                       "color": pop_up_menus_txt_col
                                      },
                                      {
                                       "text": "useless option 2",
                                       "option type": "button",
                                       "additional padding": 0,
                                       "function": placeholder_func,
                                       "color": pop_up_menus_txt_col
                                      },
                                      {
                                       "text": "useless option 3",
                                       "option type": "button",
                                       "additional padding": 0,
                                       "function": placeholder_func,
                                       "color": pop_up_menus_txt_col
                                      },
                                      {
                                       "text": "exit game",
                                       "option type": "button",
                                       "additional padding": 50,
                                       "function": quit_button_func,
                                       "color": pop_up_menus_txt_col
                                       }],
                                     cur_win_size[0] // 3, 150, 48, 100, 80, 23, align="center")

pause_button = ImageButton(pause_button_func,
                           os.path.join('images','pause button img.png'), os.path.join('images','pause button img clicked.png'),
                           15, 15, 40, 40, 15, 15, 40, 40)

globalcoins_counter = InfoButton(cur_win_size[0] - 220, 15,
                                 cur_win_size[0] - 220, 15, 200, 40,
                                 compress_number_value_in_str(globalcoins), "GLOBALCOINS", "The universal currency for every transaction you make.",
                                 hover_opt_col_mode="positive")



#stuff for map generation
feature_set_1 = [{'percentage': 0.03, 'value': 1, 'color': (0, 77, 26)},
                 {'percentage': 0.06, 'value': 2, 'color': (0, 128, 43)},
                 {'percentage': 0.06, 'value': 3, 'color': (0, 179, 60)},
                 {'percentage': 0.06, 'value': 4, 'color': (0, 230, 77)},
                 {'percentage': 0.06, 'value': 5, 'color': (26, 255, 102)},
                 {'percentage': 0.06, 'value': 6, 'color': (77, 255, 136)},
                 {'percentage': 0.06, 'value': 7, 'color': (128, 255, 170)}]

feature_params_1 = {'circle radius':40, 'expand phases':350, 'expand prob':2, 'radius reduction speed':10}

#test_map = PIG.PlanetMap(PIG.ProgressiveFeatures(feature_set_1, feature_params_1), iter_operation(cur_win_size, '//', 2))



planets = open_planet_data('r')

current_planet = planets["test planet"]["object"]

months_days_dict = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
month_names_dict = { #months are stored in number form for easier calculations but must be written in text form
                    1:"january",
                    2:"february",
                    3:"march",
                    4:"april",
                    5:"may",
                    6:"june",
                    7:"july",
                    8:"august",
                    9:"september",
                    10:"october",
                    11:"november",
                    12:"december"
                    }
date = {"Y":2040, "M":1, "D":1, "H":0, "min":0, "sec":0} #the global imaginary date
dates = [] #stores the dates passed in the game (for testing purposes for now)

planet_displays_padding = 150

temperature_display = PlanetVariableTextDisplay(planets, 100, 300 + planet_displays_padding * 0, 1000, "temperature", 74)
pressure_display = PlanetVariableTextDisplay(planets, 100, 300 + planet_displays_padding * 1, 1000, "pressure", 74)

mass_display = PlanetVariableTextDisplay(planets, 100, 300 + planet_displays_padding * 0, 1000, "mass", 74)
radius_display = PlanetVariableTextDisplay(planets, 100, 300 + planet_displays_padding * 1, 1000, "radius", 74)
surface_gravity_display = PlanetVariableTextDisplay(planets, 100, 300 + planet_displays_padding * 2, 1000, "surface gravity", 74)


atmosphere_display = BasicPopUpMenu([{"text":(element + ":").ljust(10) + (str(amount) + " ppm").rjust(20),
                                      "option type":"text",
                                      "additional padding":0,
                                      "color":general_txt_col} for element, amount in planets[current_planet.name]["atmosphere"].items()],
                                    300, 280, 52, 0, 0, 25,
                                    font=general_txt_font,
                                    facing="vertical",
                                    has_bg=False,
                                    hover_opt_col_mode="positive")



menus["add colony menu"] =  BasicPopUpMenu([{ #note: these menus are just buttons but since they have an input field it was easier to set them up like so
                                             "text": "build a new colony +",
                                             "option type": "input field",
                                             "additional padding": 0,
                                             "function": add_colony_func,
                                             "close after enter key": True,
                                             "color": general_txt_col,
                                             "caption": "type the name of the colony."
                                            }],
                                           120, 370, 24, 0, 0, 0,
                                           font=general_txt_font,
                                           facing="horizontal",
                                           has_bg=False,
                                           hover_opt_col_mode="positive",
                                           input_box_font_size=50)

menus["add city menu"] =  BasicPopUpMenu([{
                                           "text": "build a new city +",
                                           "option type": "input field",
                                           "additional padding": 0,
                                           "function": add_city_func,
                                           "close after enter key": True,
                                           "color": general_txt_col,
                                           "caption": "type the name of the city."
                                          }],
                                         120, 370, 24, 0, 0, 0,
                                         font=general_txt_font,
                                         facing="horizontal",
                                         has_bg=False,
                                         hover_opt_col_mode="positive",
                                         input_box_font_size=50)

menus["add industrial zone menu"] =  BasicPopUpMenu([{
                                                      "text": "build a new industrial zone +",
                                                      "option type": "input field",
                                                      "additional padding": 0,
                                                      "function": add_industrial_zone_func,
                                                      "close after enter key": True,
                                                      "color": general_txt_col,
                                                      "caption": "type the name of the industrial zone."
                                                     }],
                                                    120, 370, 24, 0, 0, 0,
                                                    font=general_txt_font,
                                                    facing="horizontal",
                                                    has_bg=False,
                                                    hover_opt_col_mode="positive",
                                                    input_box_font_size=50)

menus["add base menu"] =  BasicPopUpMenu([{
                                           "text": "build a new base +",
                                           "option type": "input field",
                                           "additional padding": 0,
                                           "function": add_base_func,
                                           "close after enter key": True,
                                           "color": general_txt_col,
                                           "caption": "type the name of the base."
                                          }],
                                         120, 370, 24, 0, 0, 0,
                                         font=general_txt_font,
                                         facing="horizontal",
                                         has_bg=False,
                                         hover_opt_col_mode="positive",
                                         input_box_font_size=50)

    
return_to_main_view_button = FramedButton(return_to_main_view_func,
                                          cur_win_size[0] - 430,300,400,50,
                                          30, 4,
                                          align="topleft",
                                          text="return to main view",font_size=34,txt_col=general_txt_col)



selected_build_menu  = menus["add colony menu"] #by default the colonies will be visualized
menus["add city menu"].hidden = True
menus["add industrial zone menu"].hidden = True
menus["add base menu"].hidden = True

menus["planet buildings menu"] = BasicPopUpMenu([{ #the menu under the upper permanent one with the 3 options: colonies, cities and industrial zones
                                                  "text": "colonies",
                                                  "option type": "button",
                                                  "additional padding": 0,
                                                  "function": colonies_section_func,
                                                  "color": general_txt_col
                                                  },
                                                 {
                                                  "text": "cities",
                                                  "option type": "button",
                                                  "additional padding": 0,
                                                  "function": cities_section_func,
                                                  "color": general_txt_col
                                                  },
                                                  {
                                                  "text": "industrial sites",
                                                  "option type": "button",
                                                  "additional padding": 0,
                                                  "function": industrial_zones_section_func,
                                                  "color": general_txt_col
                                                  }],
                                                20, 200, 52, 0, 0, 85,
                                                font=general_txt_font,
                                                facing="horizontal",
                                                has_bg=False,
                                                hover_opt_col_mode="positive",
                                                select_opt_mode="fixed")

selected_menu = menus["planet buildings menu"]


stats_button = ImageButton(stats_button_func,
                           os.path.join('images','stats button img.png'), os.path.join('images','stats button img clicked.png'),
                           70, 15, 40, 40, 70, 15, 40, 40)


L_main_stats_button = FramedButton(main_stats_button_func,20,150,300,70,50,5,"topright","main stats",38,hover_opt_col_mode="positive")
R_atmosphere_stats_button = FramedButton(atmosphere_stats_button_func,cur_win_size[0]-320,150,300,70,50,5,"topleft","atmosphere",38,hover_opt_col_mode="positive")
L_atmosphere_stats_button = FramedButton(atmosphere_stats_button_func,20,150,300,70,50,5,"topright","atmosphere",38,hover_opt_col_mode="positive")
R_constant_stats_button = FramedButton(constant_stats_button_func,cur_win_size[0]-320,150,300,70,50,5,"topleft","constants",38,hover_opt_col_mode="positive")
L_constant_stats_button = FramedButton(constant_stats_button_func,20,150,300,70,50,5,"topright","constants",38,hover_opt_col_mode="positive")
R_oceans_stats_button = FramedButton(oceans_stats_button_func,cur_win_size[0]-320,150,300,70,50,5,"topleft","oceans",38,hover_opt_col_mode="positive")


vehicle_design_button = ImageButton(vehicle_design_button_func,
                           os.path.join('images','vehicle design button img.png'), os.path.join('images','vehicle design button img clicked.png'),
                           125, 15, 40, 40, 125, 15, 40, 40)

#==================================================================GENERAL FUNCTIONS===================================================================

def set_active_inp_field(selected_menu, index): #function to manage input fields
    global menus
    for menu in menus.values():
        if menu is not selected_menu:
            menu.active_input_field = None
        else:
            menu.active_input_field = index


def add_secs_to_date(seconds):
    '''
    Adds a certain number of seconds to the global date.
    '''
    global date
    global dates
    
    if seconds > 59:
        assert ValueError("seconds added every loop must not be more than 59")

    for i in range(0, seconds):
        if date["sec"] >= 59:
            date["sec"] = 0
            if date["min"] >= 59:
                date["min"] = 0
                if date["H"] >= 23:
                    date["H"] = 0
                    if date["M"] == 2:
                        if date["Y"] % 4 == 0 and date["Y"] % 100 != 0:
                            temp = 29
                        else:
                            temp = 28
                        if date["D"] >= temp:
                            date["D"] = 1
                            if date["M"] >= 11:
                                date["M"] = 0
                                date["Y"] += 1
                            else:
                                date["M"] += 1
                        else:
                            date["D"] += 1
                    else:
                        if date["D"] >= months_days_dict[date["M"]] - 1:
                            date["D"] = 1
                            if date["M"] >= 11:
                                date["M"] = 0
                                date["Y"] += 1
                            else:
                                date["M"] += 1
                        else:
                            date["D"] += 1
                else:
                    date["H"] +=1
            else:
                date["min"] += 1
        else:
            date["sec"] += 1

    dates.append((date["Y"], date["M"], date["D"]))


#===================================================================UPDATE FUNCTIONS===================================================================

def event_update():
    '''
    Updates according to the pygame events happening.
    '''
    global run
    global text_inputs

    events = pygame.event.get()
    
    for textinput in text_inputs:
        textinput.update(events)
        
    for event in events:
        if event.type == QUIT:
            run = False

        notify_system.event_update(event)
        menus["pause menu"].event_update(event)
        pause_button.event_update(event)
        stats_button.event_update(event)
        vehicle_design_button.event_update(event)
        globalcoins_counter.event_update(event)
        
        if current_scene[:11] == "planet view":
            current_planet.event_update(event)
            if not current_planet.name == "earth":
                menus["planet buildings menu"].event_update(event)
            
            if current_scene == "planet view / main":
                menus["add colony menu"].event_update(event)
                menus["add city menu"].event_update(event)
                menus["add industrial zone menu"].event_update(event)
                menus["add base menu"].event_update(event)
                for colony in current_planet.colonies:
                    colony.event_update(event)
                for city in current_planet.cities:
                    city.event_update(event)
                for industrial_zone in current_planet.industrial_zones:
                    industrial_zone.event_update(event)
                for base in current_planet.bases:
                    base.event_update(event)

            elif current_scene == "planet view / building view":
                if planet_building_current_info_display:
                    if planet_building_current_info_display.add_structure_menu.hidden:
                        return_to_main_view_button.event_update(event)

                    planet_building_current_info_display.event_update(event)

                    
                    if type(planet_building_current_info_display) == ColonyInfoDisplay:
                        structure_type = 'colony'
                    if type(planet_building_current_info_display) == CityInfoDisplay:
                        structure_type = 'city'
                    if type(planet_building_current_info_display) == IndustrialZoneInfoDisplay:
                        structure_type = 'industrial_zone'
                    if type(planet_building_current_info_display) == BaseInfoDisplay:
                        structure_type = 'base'

                    for structure in eval('planet_building_current_info_display.'+structure_type+'.structures'):
                        structure.event_update(event)
                        
        elif "planet data view" in current_scene[:16]:
            if current_scene == "planet data view / main":
                R_atmosphere_stats_button.event_update(event)
                temperature_display.event_update(event)
                pressure_display.event_update(event)

            elif current_scene == "planet data view / atmosphere":
                L_main_stats_button.event_update(event)
                R_constant_stats_button.event_update(event)
                atmosphere_display.event_update(event)

            elif current_scene == "planet data view / constant":
                L_atmosphere_stats_button.event_update(event)
                R_oceans_stats_button.event_update(event)
                radius_display.event_update(event)
                mass_display.event_update(event)
                surface_gravity_display.event_update(event)

            elif current_scene == "planet data view / oceans":
                L_constant_stats_button.event_update(event)

        elif current_scene[:19] == "vehicle design view":
            VehicleDesignSystem.event_update(event)


def update():
    '''
    Update cycle for general purpose calculations.
    '''
    #NOTE: scene-binded update functions must be disabled inside the functions themselves when the wrong scene is visualized
    
    #NOTE: menus updates aren't done in a loop cycling through the menus list so that if a menu has a specific update
    #      function to be executed it can be set manually
    
    global menus, planet_building_current_info_display, planet_building_current_info_display_menu, prev_selected_build
    cur_win_size = win.get_size()

    add_secs_to_date(50)

    a_new_building_is_selected = False
    if prev_selected_build != selected_build:
        a_new_building_is_selected = True
    prev_selected_build = selected_build

    notify_system.update()
    
    if pause_menu_open:
        menus["pause menu"].hidden = False
    else:
        menus["pause menu"].hidden = True

    for obj in InventoryObject.all_objects:
        obj.update()

    if a_new_building_is_selected:
        if "building current info display menu" in menus:
            menus.pop("building current info display menu")
            
        add_structure_button = TextButton(view_building_func,
                                          90,390,330,50,
                                          55,375,330,55,
                                          text="add structure +",font_size=26,txt_col=general_txt_col,
                                          has_box=False,
                                          fix="topleft",
                                          hover_opt_col_mode="positive")

        add_space_button = TextButton(view_building_func,
                                      90,450,330,50,
                                      55,435,330,55,
                                      text="add space +",font_size=26,txt_col=general_txt_col,
                                      has_box=False,
                                      fix="topleft",
                                      hover_opt_col_mode="positive")

        if 'planet_building_current_info_display' in globals():
            del planet_building_current_info_display
        if 'planet_building_current_info_display_menu' in globals():
            del planet_building_current_info_display_menu
            
        if type(selected_build) == Colony:
            planet_building_current_info_display = ColonyInfoDisplay(selected_build, add_structure_button, add_space_button)
            planet_building_current_info_display_menu = planet_building_current_info_display.add_structure_menu
            
        elif type(selected_build) == City:
            planet_building_current_info_display = CityInfoDisplay(selected_build, add_structure_button, add_space_button)
            planet_building_current_info_display_menu = planet_building_current_info_display.add_structure_menu
            
        elif type(selected_build) == IndustrialZone:
            planet_building_current_info_display = IndustrialZoneInfoDisplay(selected_build, add_structure_button, add_space_button)
            planet_building_current_info_display_menu = planet_building_current_info_display.add_structure_menu

        elif type(selected_build) == Base:
            planet_building_current_info_display = BaseInfoDisplay(selected_build, add_structure_button, add_space_button)
            planet_building_current_info_display_menu = planet_building_current_info_display.add_structure_menu
            
        else:
            current_scene = "planet view / main"

        if 'planet_building_current_info_display_menu' in globals():
            menus["building current info display menu"] = planet_building_current_info_display_menu
        elif "building current info display menu" in menus:
            menus.pop("building current info display menu")
        
    menus["pause menu"].update()
    pause_button.update()
    stats_button.update()
    vehicle_design_button.update()
    
    globalcoins_counter.update(globalcoins_counter_update_func)

    return_to_main_view_button.update()

    current_planet.update()
    menus["planet buildings menu"].update()
    menus["add colony menu"].update()
    menus["add city menu"].update()
    menus["add industrial zone menu"].update()
    menus["add base menu"].update()

    for planet in planets.values():
        for colony in planet["object"].colonies:
            colony.update()
            for structure in colony.structures:
                structure.update()
                
        for city in planet["object"].cities:
            city.update()
            for structure in city.structures:
                structure.update()
                
        for industrial_zone in planet["object"].industrial_zones:
            industrial_zone.update()
            for structure in industrial_zone.structures:
                structure.update()

        for base in planet["object"].bases:
            base.update()
            for structure in base.structures:
                structure.update()

    if 'planet_building_current_info_display' in globals():
        if planet_building_current_info_display:
            planet_building_current_info_display.update()

    L_main_stats_button.update()
    R_atmosphere_stats_button.update()
    L_atmosphere_stats_button.update()
    R_constant_stats_button.update()
    L_constant_stats_button.update()
    R_oceans_stats_button.update()
    atmosphere_display.update(atmosphere_display_update_func)
    temperature_display.update()
    pressure_display.update()
    radius_display.update()
    mass_display.update()
    surface_gravity_display.update()

    VehicleDesignSystem.update()

    ResearchTree.random_research()


def updateGFX():
    '''
    Graphic update.
    '''
    global current_scene, selected_build_menu
    win.fill(bg_col)

    if current_scene[:11] == "planet view":
        current_planet.draw()

    if "planet data view" in current_scene[:16]: #draws the displays of the various planet variables in the planet data view scene
        if current_scene == "planet data view / main":
            R_atmosphere_stats_button.draw()
            temperature_display.draw()
            pressure_display.draw()
            
        elif current_scene == "planet data view / atmosphere":
            L_main_stats_button.draw()
            R_constant_stats_button.draw()
            atmosphere_display.draw()

        elif current_scene == "planet data view / constant":
            L_atmosphere_stats_button.draw()
            R_oceans_stats_button.draw()
            radius_display.draw()
            mass_display.draw()
            surface_gravity_display.draw()

        elif current_scene == "planet data view / oceans":
            L_constant_stats_button.draw()
            for i, ocean_element in enumerate(planets[current_planet.name]["oceans"].keys()):
                ocean_element_txt_font = pygame.font.Font(general_txt_font, 55) #name of the element/compound that composes the ocean
                temp_txt_var = current_planet.oceans[ocean_element]["display name"] + " [" + ocean_element + "]"
                ocean_element_txt_obj = ocean_element_txt_font.render(temp_txt_var, True, general_txt_col)
                ocean_element_txt_rect = ocean_element_txt_obj.get_rect()
                ocean_element_txt_rect.topleft = (100, 280 + 320 * i)
                win.blit(ocean_element_txt_obj, ocean_element_txt_rect)
                
                sea_level_txt_font = pygame.font.Font(general_txt_font, 35) #sea level of the planet regarding that element/compound
                temp_txt_var = "sea level:" + " " * 8 + str(current_planet.oceans[ocean_element]["sea level"]) + " cm"
                sea_level_txt_obj = sea_level_txt_font.render(temp_txt_var, True, general_txt_col)
                sea_level_txt_rect = sea_level_txt_obj.get_rect()
                sea_level_txt_rect.topleft = (250, 370 + 320 * i)
                win.blit(sea_level_txt_obj, sea_level_txt_rect)

                percentage_txt_font = pygame.font.Font(general_txt_font, 35) #percentages of states of matter of the element
                temp_dict = current_planet.oceans[ocean_element]["percentage"]
                temp_txt_var = "percentage:   "+"sol.("+str(temp_dict["solid"])+"%) liq.("+str(temp_dict["liquid"])+"%) aer.("+str(temp_dict["aeriform"])+"%)"
                percentage_txt_obj = percentage_txt_font.render(temp_txt_var, True, general_txt_col)
                percentage_txt_rect = percentage_txt_obj.get_rect()
                percentage_txt_rect.topleft = (250, 430 + 320 * i)
                win.blit(percentage_txt_obj, percentage_txt_rect)

                acquifers_txt_font = pygame.font.Font(general_txt_font, 35)
                temp_txt_var = "acquifers amount:" + " " * 3 + str(current_planet.oceans[ocean_element]["acquifers"])
                acquifers_txt_obj = acquifers_txt_font.render(temp_txt_var, True, general_txt_col)
                acquifers_txt_rect = acquifers_txt_obj.get_rect()
                acquifers_txt_rect.topleft = (250, 490 + 320 * i)
                win.blit(acquifers_txt_obj, acquifers_txt_rect)

    elif current_scene[:11] == "planet view":
        if current_planet.name == "earth":
            if current_scene == "planet view / main":
                for base in current_planet.bases:
                    base.draw()
            if current_planet.name == "earth":
                win.blit(earth_bases_txt_obj, earth_bases_txt_rect)
                
        else:
            menus["planet buildings menu"].draw()

            if current_scene == "planet view / main":
                for colony in current_planet.colonies:
                    colony.draw()
                for city in current_planet.cities:
                    city.draw()
                for industrial_zone in current_planet.industrial_zones:
                    industrial_zone.draw()

        if current_scene == "planet view / main":
            win.blit(building_menu_line1_img, building_menu_line1_rect) #the section where the colonies infos are displayed
            win.blit(building_menu_line3_img, building_menu_line3_rect)

        if current_scene == "planet view / building view":
            return_to_main_view_button.draw()

        planet_buildings_menu_underline_rect = planet_buildings_menu_underline.get_rect()
        planet_buildings_menu_underline_rect.topleft = (10, 300)
        win.blit(planet_buildings_menu_underline, planet_buildings_menu_underline_rect)
        
        if current_scene == "planet view / main":
            selected_build_menu.draw()

    if current_scene[:19] == "vehicle design view":
        planet_buildings_menu_underline_rect = planet_buildings_menu_underline.get_rect()
        planet_buildings_menu_underline_rect.topleft = (10, 250)
        win.blit(pygame.transform.scale(planet_buildings_menu_underline, (int(planet_buildings_menu_underline_rect.w * 0.7), int(planet_buildings_menu_underline_rect.h * 0.8))),
                 planet_buildings_menu_underline_rect)

        VehicleDesignSystem.draw()


    #draws upper permanent menu
    pygame.draw.polygon(win, general_widget_col2,
                        ((cur_win_size[0] // 2 - upper_permanent_menu_polygon_width // 2 - 5,  135),
                         (cur_win_size[0] // 2 + upper_permanent_menu_polygon_width // 2 + 5,  135),
                         (cur_win_size[0] // 2 + upper_permanent_menu_polygon_width // 2 + 55,  15),
                         (cur_win_size[0] // 2 - upper_permanent_menu_polygon_width // 2 - 55,  15)),
                        )
    pygame.draw.rect(win, general_widget_col1, (0,0,cur_win_size[0],70))
    pygame.draw.rect(win, general_widget_col2, (0,0,cur_win_size[0],70), width=5)
    pygame.draw.polygon(win, general_widget_col1,
                        ((cur_win_size[0] // 2 - upper_permanent_menu_polygon_width // 2,  130),
                         (cur_win_size[0] // 2 + upper_permanent_menu_polygon_width // 2,  130),
                         (cur_win_size[0] // 2 + upper_permanent_menu_polygon_width // 2 + 50,  10),
                         (cur_win_size[0] // 2 - upper_permanent_menu_polygon_width // 2 - 50,  10))
                        )

    #draws the current planet name in the middle of the permanent upper menu
    planet_upper_menu_txt_obj = planet_upper_menu_txt_font.render(current_planet.name, True, general_txt_col)
    planet_upper_menu_txt_rect = planet_upper_menu_txt_obj.get_rect()
    planet_upper_menu_txt_rect.center = (cur_win_size[0] // 2, 50)
    win.blit(planet_upper_menu_txt_obj, planet_upper_menu_txt_rect)

    #draws the date under the planet name
    date_txt = "year: {0}  month: {1}  day: {2}".format(date["Y"], month_names_dict[date["M"]][:3], date["D"])
    date_upper_menu_txt_obj = date_upper_menu_txt_font.render(date_txt, True, general_txt_col)
    date_upper_menu_txt_rect = date_upper_menu_txt_obj.get_rect()
    date_upper_menu_txt_rect.center = (cur_win_size[0] // 2, 105)
    win.blit(date_upper_menu_txt_obj, date_upper_menu_txt_rect)

    if current_scene == "planet view / building view":
        if current_planet.name == "earth":
            for base in current_planet.bases:
                for structure in base.structures:
                    structure.draw()
        else:
            for colony in current_planet.colonies:
                for structure in colony.structures:
                    structure.draw()
            for city in current_planet.cities:
                for structure in city.structures:
                    structure.draw()
            for industrial_zone in current_planet.industrial_zones:
                for structure in industrial_zone.structures:
                    structure.draw()

        if planet_building_current_info_display:
            planet_building_current_info_display.draw()

    win.blit(globalcoins_upper_menu_icon_img, (cur_win_size[0] - 100, 10))
        
    pause_button.draw()
    stats_button.draw()
    vehicle_design_button.draw()
    notify_system.draw()
    menus["pause menu"].draw()
    globalcoins_counter.draw()
    
    pygame.display.update()

#======================================================================PREP CODE=======================================================================

#Planet.activate_all_map_features()
        
#=======================================================================MAINLOOP=======================================================================

while run:
    ref_loop_time = time.time()
    
    event_update()

    keys = pygame.key.get_pressed()

    if keys[pygame.K_ESCAPE]:
        if "K_ESCAPE" not in key_cooldown:
            if pause_menu_open:
                pause_menu_open = False
            else:
                pause_menu_open = True
                
            key_cooldown["K_ESCAPE"] = time.time()

    if keys[pygame.K_UP]: #scrolls up in the planet buildings menu
        if "K_UP" not in key_cooldown:
            if current_scene == "planet view / main":
                if selected_build_menu == menus["add colony menu"]:
                    if current_planet.colonies[0].y <= planet_buildings_menus_default_y - 120:
                        for colony in current_planet.colonies:
                            colony.change_position((0, 120))
                elif selected_build_menu == menus["add city menu"]:
                    if current_planet.cities[0].y <= planet_buildings_menus_default_y - 120:
                        for city in current_planet.cities:
                            city.change_position((0, 120))
                elif selected_build_menu == menus["add industrial zone menu"]:
                    if current_planet.industrial_zones[0].y <= planet_buildings_menus_default_y - 120:
                        for industrial_zone in current_planet.industrial_zones:
                            industrial_zone.change_position((0, 120))
                elif selected_build_menu == menus["add base menu"]:
                    if current_planet.bases[0].y <= planet_buildings_menus_default_y - 120:
                        for base in current_planet.bases:
                            base.change_position((0, 120))
                    
            key_cooldown["K_UP"] = time.time()

    if keys[pygame.K_DOWN]: #scrolls down in the planet buildings menu
        if "K_DOWN" not in key_cooldown:
            if current_scene == "planet view / main":
                if selected_build_menu == menus["add colony menu"]:
                    if current_planet.colonies[-1].y >= planet_buildings_menus_default_y + 120:
                        for colony in current_planet.colonies:
                            colony.change_position((0, -120))
                if selected_build_menu == menus["add city menu"]:
                    if current_planet.cities[-1].y >= planet_buildings_menus_default_y + 120:
                        for city in current_planet.cities:
                            city.change_position((0, -120))
                if selected_build_menu == menus["add industrial zone menu"]:
                    if current_planet.industrial_zones[-1].y >= planet_buildings_menus_default_y + 120:
                        for industrial_zone in current_planet.industrial_zones:
                            industrial_zone.change_position((0, -120))
                if selected_build_menu == menus["add base menu"]:
                    if current_planet.bases[-1].y >= planet_buildings_menus_default_y + 120:
                        for base in current_planet.bases:
                            base.change_position((0, -120))
                    
            key_cooldown["K_DOWN"] = time.time()


    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_1]: #debug command slot 1
        current_planet = planets["mars"]["object"]
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_2]: #debug command slot 2
        current_planet = planets["test planet"]["object"]
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_3]: #debug command slot 3
        current_planet = planets["big test planet"]["object"]
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_4]: #debug command slot 4
        current_planet = planets["earth"]["object"]
        bases_section_func()
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_5]: #debug command slot 5
        pass
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_6]: #debug command slot 6
        globalcoins = globalcoins * 1.004 + 1
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_7]: #debug command slot 7
        globalcoins //= 1.004
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_8]: #debug command slot 8
        exec(input())
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_d] and keys[pygame.K_9]: #debug command slot 9
        print(pygame.mouse.get_pos())
    
    update()
    updateGFX()

    #removes the cooldowns of keys
    if "K_ESCAPE" in key_cooldown:
        if 0.3 - (time.time() - key_cooldown["K_ESCAPE"]) <= 0:
            key_cooldown.pop("K_ESCAPE")

    if "K_RIGHT" in key_cooldown:
        if 0.2 - (time.time() - key_cooldown["K_RIGHT"]) <= 0:
            key_cooldown.pop("K_RIGHT")

    if "K_LEFT" in key_cooldown:
        if 0.2 - (time.time() - key_cooldown["K_LEFT"]) <= 0:
            key_cooldown.pop("K_LEFT")

    if "K_UP" in key_cooldown:
        if 0.15 - (time.time() - key_cooldown["K_UP"]) <= 0:
            key_cooldown.pop("K_UP")

    if "K_DOWN" in key_cooldown:
        if 0.15 - (time.time() - key_cooldown["K_DOWN"]) <= 0:
            key_cooldown.pop("K_DOWN")


    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and keys[pygame.K_t]: #to see how long frames lasts
        print(time.time() - ref_loop_time)

pygame.quit()
