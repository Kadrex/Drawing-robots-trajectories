"""Program to draw robot's trajectories and objects (polygons) on an image."""

from scipy.optimize import fsolve
import numpy as np
from PIL import Image, ImageDraw
import math


class Good:

    def __init__(self):
        """Constructor."""
        self.image_size = 3000
        self.drawing_line_width = 6
        self.scale = 1000
        self.size_multiplier = 1
        self.image = Image.new("RGBA", (self.image_size * self.size_multiplier, self.image_size * self.size_multiplier),
                               (255, 255, 255))
        self.circle_center = [self.image.size[0] // 2, self.image.size[1] // 2]
        self.starting_point = []
        self.l = None
        self.radius = None
        self.ending_point = []
        self.line_color = (0, 0, 153)
        self.colors = [(0, 0, 153), (153, 0, 0), (0, 153, 0)]  # blue, red, green

        self.prev_circle_center = []
        self.prev_radius = None
        self.prev_was_negative_radius = False
        self.same_direction_as_previous = True
        self.negative_radius = False

    def find_new_circle_center(self, xy):
        """
        Find new circle center coordinates, solves a equation system.

        :param xy: x and y as a list, "presumable" values for x and y
        :return: values of x and y, as a list
        """
        Ox = self.prev_circle_center[0]
        Oy = self.prev_circle_center[1]
        if not self.same_direction_as_previous:
            OO_value = self.prev_radius + self.radius
        else:
            OO_value = self.prev_radius - self.radius
        BO_value = self.radius
        Bx = self.starting_point[0]
        By = self.starting_point[1]
        x, y = xy[0], xy[1]
        OO = -OO_value**2 + Ox**2 - 2*Ox*x + x**2 + Oy**2 - 2*Oy*y + y**2
        BO = -BO_value**2 + Bx**2 - 2*Bx*x + x**2 + By**2 - 2*By*y + y**2
        return OO, BO

    def find_ending_point(self, angle_rad):
        """
        Find the ending point of drawn arc.

        :param angle_rad: angle in radians
        :return: ending point coordinates [x, y].
        """
        if self.negative_radius:
            angle = angle_rad - self.l / self.radius
        else:
            angle = angle_rad + self.l / self.radius
        Bx = self.circle_center[0] + self.radius * math.cos(angle)
        By = self.circle_center[1] + self.radius * math.sin(angle)
        return [Bx, By]

    def find_pie_coordinates(self, circle_radius, circle_center: list):
        """
        Find the bounding box's coordinates for the arc.

        :param circle_radius: circle radius
        :param circle_center: circle center
        :return: list on bounding box's coorcinates, starting from upper left, moving bottom right: [x0, y0, x1, y1].
        """
        Ox = circle_center[0]
        Oy = circle_center[1]
        return [Ox - circle_radius, Oy - circle_radius, Ox + circle_radius, Oy + circle_radius]

    def draw_arcs(self, data: list):
        """
        Draw arcs.

        :param data: list of trajectories, containing arc length and radius.
        :return:
        """
        d = ImageDraw.Draw(self.image)
        for i in range(len(data)):
            self.prev_radius = self.radius
            self.l = data[i][0] * self.scale
            self.radius = data[i][1] * self.scale
            if self.radius < 0:
                self.negative_radius = True
                self.radius = abs(self.radius)
            else:
                self.negative_radius = False
            if self.prev_was_negative_radius and self.negative_radius \
                    or not self.prev_was_negative_radius and not self.negative_radius:
                self.same_direction_as_previous = True
            else:
                self.same_direction_as_previous = False
            self.prev_circle_center = self.circle_center
            if not i:
                self.starting_point = [self.circle_center[0] - self.radius, self.circle_center[1]]
            else:
                self.starting_point = self.ending_point
                self.circle_center = list(fsolve(self.find_new_circle_center, np.array([0, 0])))
            starting_angle_rad = math.atan2(self.starting_point[1] - self.circle_center[1],
                                            self.starting_point[0] - self.circle_center[0])
            starting_angle_deg = round(math.degrees(starting_angle_rad))
            ending_angle_deg = (180 * self.l) // (math.pi * self.radius) + starting_angle_deg
            pie_coordinates = self.find_pie_coordinates(self.radius, self.circle_center)
            if self.negative_radius:
                self.prev_was_negative_radius = True
                ending_angle_deg = starting_angle_deg
                starting_angle_deg = ending_angle_deg - (180 * self.l) // (math.pi * self.radius)
                d.arc(pie_coordinates, starting_angle_deg, ending_angle_deg, fill=self.colors[i % len(self.colors)],
                      width=self.drawing_line_width)
            else:
                self.prev_was_negative_radius = False
                d.arc(pie_coordinates, starting_angle_deg, ending_angle_deg, fill=self.colors[i % len(self.colors)],
                      width=self.drawing_line_width)

            self.ending_point = self.find_ending_point(starting_angle_rad)

        self.image = self.image.resize((self.image_size * self.size_multiplier, self.image_size * self.size_multiplier))
        self.image.save("drawn_arcs.png")
        self.image.show()

    def draw_polygons(self, data: list):
        """
        Draw polygons.

        :param data: list of polygon coordinates
        :return:
        """
        d = ImageDraw.Draw(self.image)
        for polygon in data:
            resized_polygon = []
            for polygon_coord in polygon:
                new_coord = (polygon_coord[0] * self.scale, polygon_coord[1] * self.scale)
                resized_polygon.append(new_coord)
            if len(resized_polygon) > 1:
                if resized_polygon[0] == resized_polygon[-1]:
                    resized_polygon.pop(-1)
            d.polygon(resized_polygon, fill="black", outline="black")
        image = self.image.resize((self.image_size * self.size_multiplier, self.image_size * self.size_multiplier))
        image.save("drawn_polygons.png")
        image.show()

    def reset_image_coordinates(self):
        """Reset the 'first' arc's center to start drawing new trajectories on the same image."""
        self.circle_center = [self.image.size[0] // 2, self.image.size[1] // 2]



if __name__ == '__main__':
    drawing = Good()
    polygons = [[(0.3, 1.1), (0.8, 0.2), (1.3, 1.1), (0.15, 0.5), (1.45, 0.5), (0.3, 1.1)]]
    drawing.draw_polygons(polygons)

    generated_data = []
    radius = 0
    for i in range(1, 20):  # 2200
        radius += 0.01
        generated_data.append([0.5, radius])
    generated_data.append([0.6, -0.2])
    drawing.draw_arcs(generated_data)
    drawing.reset_image_coordinates()
    drawing.draw_arcs([[0.5, -0.2], [0.5, -0.4]])
