import pygame
from pygame.locals import *
import random, time, copy, math

win_size = (1600, 800)
if __name__ == '__main__':
    win = pygame.display.set_mode(win_size)
    win.fill((255,0,0))



class Features:
    '''
Parameters necessaries to build a map.

NOTE: performance greatly decreases the higher expand probability and expand phases are set.
    '''
    def __init__(self, values, parameters):
        self.all_circles = {}
        self.filters = {"in init":[]}
        
        self.percentages = [value["percentage"] for value in values]
        self.values = [value["value"] for value in values]
        self.colors = [value["color"] for value in values]
        self.circle_radius = parameters["circle radius"]
        self.expand_phases = parameters["expand phases"]
        self.expand_prob = parameters["expand prob"]
        self.radius_reduction_speed = parameters["radius reduction speed"]

        self.activation_state = None #stores information about the advancement of the state of activation


    def initialize(self, circles, i):
        '''
Not to use outside class definition.
        '''
        
        print("initializing feature "+str(i)+"...") #initializing a feature means drawing the first zones where the feature will expand
        for y in range(self.surf_size[1]):
            for x in range(self.surf_size[0]):
                if random.uniform(0,100) <= self.percentages[i]:
                    circles[i][0].append(pygame.draw.circle(self.planet_map.surface, self.colors[i], (x, y), self.circle_radius))
                    for fil in self.filters["in init"]:
                        fil(self.surf_size, circles, i)
        print("feature "+str(i)+" initialized")


    def expand(self, circles, i):
        '''
Not to use outside class definition.
        '''
        
        print("\nexpanding feature "+str(i)) #an expanding phase draws circle adiacent to existing ones with a fixed probability ( self.expand_prob )
        local_radius = self.circle_radius
        
        for phase in range(self.expand_phases): 
            if phase % 10 == 0:
                print("phase "+str(phase+1))
            
            if phase % (100 // self.radius_reduction_speed) == 0:
                if not local_radius <= 2:
                    local_radius -= 1
            
            new_circles = []
            for circle_phase in circles[i]:
                for circle in circle_phase:
                    x, y = circle.center
                    x += random.randint(-local_radius, local_radius)
                    y += random.randint(-local_radius, local_radius)
                    if random.uniform(0,100) <= self.expand_prob:
                        new_circles.append(pygame.draw.circle(self.planet_map.surface, self.colors[i], (x, y), local_radius))
            circles[i].append(new_circles)
            self.all_circles[i].append(new_circles)


    def activate(self):
        print("\nactivating features...\n")
        circles = {i:[[]] for i in range(len(self.values))} #copy of self.all_circles, it's a redundant feature
        self.all_circles = copy.deepcopy(circles)
        
        for i in circles.keys(): 
            self.initialize(circles, i)
                    
        pygame.display.update()
        self.planet_map.surface.fill((0,0,0))
        print()

        for i in circles.keys():
            self.expand(circles, i)

        print("\nfeatures activated\n")
        self.activation_state = True


    def step_activate(self):
        print("\nactivating features...\n")
        circles = {i:[[]] for i in range(len(self.values))}
        if not self.activation_state:
            self.all_circles = copy.deepcopy(circles)
            self.activation_state = {k: False for k in circles.keys()}
        
        for i in circles.keys():
            self.initialize(circles, i)
                    
        self.planet_map.surface.fill((0,0,0))
        print()

        for i, state in self.activation_state.items():
            if state:
                continue
            self.expand(circles, i)
            self.activation_state[i] = True
            break

        if sum(self.activation_state.values()) == len(self.activation_state):
            self.activation_state = True

        print("\nfeatures activated\n")



class ProgressiveFeatures(Features):
    '''
Features that separatedly initialize and expand each level so that the superior
level is filtered by the inferior ones. This is to make each layer go on top of
the previous one and not the more inferior ones / background and smoothly transition
from a more probable layer to a less probable one.

NOTE: this will alter the probability a bit so make sure to increase the probability
      of the higher levels.
    '''
    def activate(self):
        print("\nactivating features...\n")
        circles = {i:[[]] for i in range(len(self.values))}
        self.all_circles = {i:[[]] for i in range(len(self.values))}

        def initialize(i):
            print("\ninitializing feature "+str(i)+"...")
            ghost_surf = pygame.Surface((self.surf_size[0], self.surf_size[1]))
            if i == 0:
                for y in range(self.surf_size[1]):
                    for x in range(self.surf_size[0]):
                        if random.uniform(0,100) <= self.percentages[i]:
                            circles[i][0].append(pygame.draw.circle(self.planet_map.surface, self.colors[i], (x, y), self.circle_radius))
                            for fil in self.filters["in init"]:
                                fil(self.surf_size, circles, i)
            else:
                for exp_phase in self.all_circles[i-1]:
                    for circle in exp_phase:
                        x, y = circle.center
                        x += random.randint(-self.circle_radius, self.circle_radius)
                        y += random.randint(-self.circle_radius, self.circle_radius)
                        if random.uniform(0,100) <= self.percentages[i]:
                            circles[i][0].append(pygame.draw.circle(ghost_surf, self.colors[i], (x, y), self.circle_radius))
            print("feature "+str(i)+" initialized")

        for i in circles.keys():
            initialize(i)  
            self.expand(circles, i)
            pygame.display.update()

        print("\nfeatures activated\n")


    def step_activate(self):
        print("\nactivating features...\n")
        circles = {i:[[]] for i in range(len(self.values))}
        if not self.activation_state:
            self.all_circles = {i:[[]] for i in range(len(self.values))}
            self.activation_state = {k: False for k in circles.keys()}

        def initialize(i):
            print("\ninitializing feature "+str(i)+"...")
            ghost_surf = pygame.Surface((self.surf_size[0], self.surf_size[1]))
            if i == 0:
                for y in range(self.surf_size[1]):
                    for x in range(self.surf_size[0]):
                        if random.uniform(0,100) <= self.percentages[i]:
                            circles[i][0].append(pygame.draw.circle(self.planet_map.surface, self.colors[i], (x, y), self.circle_radius))
                            for fil in self.filters["in init"]:
                                fil(self.surf_size, circles, i)
            else:
                for exp_phase in self.all_circles[i-1]:
                    for circle in exp_phase:
                        x, y = circle.center
                        x += random.randint(-self.circle_radius, self.circle_radius)
                        y += random.randint(-self.circle_radius, self.circle_radius)
                        if random.uniform(0,100) <= self.percentages[i]:
                            circles[i][0].append(pygame.draw.circle(ghost_surf, self.colors[i], (x, y), self.circle_radius))
            print("feature "+str(i)+" initialized")

        for i, state in self.activation_state.items():
            if state:
                continue
            initialize(i)  
            self.expand(circles, i)
            self.activation_state[i] = True
            pygame.display.update()
            break

        if sum(self.activation_state.values()) == len(self.activation_state):
            self.activation_state = True

        print("\nfeatures activated\n")



class PlanetMap:
    def __init__(self, features, surf_size):
        self.surf_size = surf_size
        self.surface = pygame.Surface(self.surf_size)
        self.features = features
        setattr(self.features, 'planet_map', self)
        setattr(self.features, 'surf_size', self.surf_size)


    def enter_save_mode(self):
        self.surface = pygame.image.tostring(self.surface, 'RGB')


    def exit_save_mode(self):
        self.surface = pygame.image.fromstring(self.surface, self.surf_size, 'RGB')


    def event_update(self, event):
        pass


    def update(self):
        pass


    def draw(self):
        win.blit(self.surface, (0,0))


if __name__ == '__main__':
    #time.sleep(8)
            
    feature_set_1 = [{'percentage': 0.012, 'value': 1, 'color': (0,31,51)},
                     {'percentage': 0.006, 'value': 2, 'color': (0,92,153)},
                     {'percentage': 0.002, 'value': 3, 'color': (0,153,255)},
                     {'percentage': 0.0008, 'value': 4, 'color': (102,194,255)},
                     {'percentage': 0.0002, 'value': 5, 'color': (204,235,255)}]

    feature_set_2 = [{'percentage': 0.03, 'value': 1, 'color': (0, 77, 26)},
                     {'percentage': 0.012, 'value': 2, 'color': (0, 128, 43)},
                     {'percentage': 0.006, 'value': 3, 'color': (0, 179, 60)},
                     {'percentage': 0.003, 'value': 4, 'color': (0, 230, 77)},
                     {'percentage': 0.001, 'value': 5, 'color': (26, 255, 102)},
                     {'percentage': 0.0006, 'value': 6, 'color': (77, 255, 136)},
                     {'percentage': 0.0002, 'value': 7, 'color': (128, 255, 170)}]

    feature_set_3 = [{'percentage': 0.03, 'value': 1, 'color': (0, 77, 26)},
                     {'percentage': 0.06, 'value': 2, 'color': (0, 128, 43)},
                     {'percentage': 0.06, 'value': 3, 'color': (0, 179, 60)},
                     {'percentage': 0.06, 'value': 4, 'color': (0, 230, 77)},
                     {'percentage': 0.06, 'value': 5, 'color': (26, 255, 102)},
                     {'percentage': 0.06, 'value': 6, 'color': (77, 255, 136)},
                     {'percentage': 0.06, 'value': 7, 'color': (128, 255, 170)}]


    feature_params_1 = {'circle radius':18, 'expand phases':350, 'expand prob':2, 'radius reduction speed':4}
    feature_params_2 = {'circle radius':20, 'expand phases':280, 'expand prob':2, 'radius reduction speed':4}
    feature_params_3 = {'circle radius':40, 'expand phases':350, 'expand prob':2, 'radius reduction speed':10}


    symfilter_funcs = ['0.5*x**2+0.3', '0.5*x**2+0.3', '0.9*x**2+0.1']
    def filter1(screen_size, circles, i, func_i, inverse):
        x, y = circles[i][0][-1].center
        shift_x, shift_y = 0, 0
        function = symfilter_funcs[func_i]

        func_x = random.uniform(0, 1)
        func_y = eval(function.replace('x', str(func_x)))
        
        if y > screen_size[1] / 2:
            if inverse:
                shift_y += screen_size[1] - y
            else:
                shift_y -= y - screen_size[1] // 2
        else:
            if inverse:
                shift_y -= y
            else:
                shift_y += screen_size[1] // 2 - y

        shift_y *= func_y
        
        circles[i][0][-1].center = (x + shift_x, y + shift_y)


    def filter2(screen_size, circles, i, func_i, inverse):
        x, y = circles[i][0][-1].center
        shift_x, shift_y = 0, 0
        function = symfilter_funcs[func_i]

        func_x = random.uniform(0, 1)
        func_y = eval(function.replace('x', str(func_x)))
        
        if x > screen_size[0] / 2:
            if inverse:
                shift_x += screen_size[0] - x
            else:
                shift_x -= x - screen_size[0] // 2
        else:
            if inverse:
                shift_x -= x
            else:
                shift_x += screen_size[0] // 2 - x

        shift_x *= func_y
        
        circles[i][0][-1].center = (x + shift_x, y + shift_y)


    def symfilterconfig(filt, func_i, inverse=False):
        def new_filter(screen_size, circles, i):
            filt(screen_size, circles, i, func_i, inverse)
        return new_filter



    test_map = PlanetMap(ProgressiveFeatures(feature_set_3, feature_params_3), win_size)
    test_map.features.filters["in init"].append(symfilterconfig(filter1, 2))
    test_map.features.filters["in init"].append(symfilterconfig(filter2, 2))
    t1 = time.time()
    test_map.features.activate()
    t2 = time.time()



    run = True

    def event_update():
        global run
        
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT:
                run = False

            test_map.event_update(event)


    def update():
        test_map.update()


    def updateGFX():
        test_map.draw()

        pygame.display.update()



    while run:
        event_update()
        update()
        updateGFX()



    pygame.quit()
