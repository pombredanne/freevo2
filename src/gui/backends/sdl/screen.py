from layer import Layer


class Screen:
    """
    The screen implementation for pygame
    """
    def __init__(self, renderer):
        self.renderer = renderer
        self.width    = self.renderer.width
        self.height   = self.renderer.height
        self.layer    = {}

        self.layer['content'] = Layer('content', self)
        self.layer['alpha']   = Layer('alpha', self, True)
        self.layer['bg']      = Layer('bg', self)
        self.layer['widget']  = Layer('widget', self, True)
        self.complete_bg      = self.renderer.screen.convert()
        self.old_surface      = None
        

    def clear(self):
        """
        Clear the complete screen
        """
        _debug_('someone called clear')
        self.layer['bg'].add_to_update_rect(0, 0, 800, 600)


    def add(self, object):
        """
        Add object to the screen
        """
        if object.layer < -4:
            return self.layer['bg'].add(object)
        if object.layer < 0:
            return self.layer['alpha'].add(object)
        return self.layer['content'].add(object)
    
            
    def remove(self, object):
        """
        Remove an object from the screen
        """
        if object.layer < -4:
            return self.layer['bg'].remove(object)
        if object.layer < 0:
            return self.layer['alpha'].remove(object)
        return self.layer['content'].remove(object)


    def get_objects(self):
        return self.layer['bg'].objects + self.layer['alpha'].objects + \
               self.layer['content'].objects


    def update(self):
        """
        Show the screen using pygame
        """
        if self.renderer.must_lock:
            # only lock s_alpha layer, because only there
            # are pixel operations (round rectangle)
            self.layer['alpha'].lock()

        bg    = self.layer['bg']
        alpha = self.layer['alpha']

        update_area = bg.draw()[0]

        update_area = alpha.expand_update_rect(update_area)

        if update_area:
            alpha.screen.fill((0,0,0,0))
            alpha.draw()

        # and than blit only the changed parts of the screen
        for x0, y0, x1, y1 in update_area:
            self.complete_bg.blit(bg.screen, (x0, y0), (x0, y0, x1-x0, y1-y0))
            self.complete_bg.blit(alpha.screen, (x0, y0), (x0, y0, x1-x0, y1-y0))

        content = self.layer['content']

        update_area = content.expand_update_rect(update_area)

        for x0, y0, x1, y1 in update_area:
            content.blit(self.complete_bg, (x0, y0), (x0, y0, x1-x0, y1-y0))

        rect = content.draw()[1]


        widget = self.layer['widget']
        update_area = widget.expand_update_rect(update_area)

        for x0, y0, x1, y1 in update_area:
            widget.blit(self.complete_bg, (x0, y0), (x0, y0, x1-x0, y1-y0))

        rect = widget.draw()[1]

        for x0, y0, x1, y1 in update_area:
            self.renderer.screenblit(content.screen, (x0, y0), (x0, y0, x1-x0, y1-y0))

        if self.renderer.must_lock:
            self.s_alpha.unlock()

        if self.old_surface:
            # move test
            self.new_surface = self.renderer.screen.convert()
            step = 20
            if self.direction == 1:
                for i in range(self.width / step):
                    self.renderer.screen.blit(self.old_surface, (-i * step, 0))
                    self.renderer.screen.blit(self.new_surface, (self.width-i*step, 0))
                    self.renderer.update()
            else:
                for i in range(self.width / step):
                    self.renderer.screen.blit(self.new_surface, (-self.width + i * step, 0))
                    self.renderer.screen.blit(self.old_surface, ( i * step, 0))
                    self.renderer.update()
            self.renderer.screen.blit(self.new_surface, (0, 0))
            self.renderer.update()
            self.old_surface = None
            self.new_surface = None
        elif update_area:
            self.renderer.update([rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]])


    def prepare_for_move(self, direction):
        return
        self.old_surface = self.renderer.screen.convert()
        self.direction   = direction