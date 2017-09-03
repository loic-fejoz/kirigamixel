"""
Copyright (c) 2017 Loïc Fejoz
This file is provided under the MIT License.

author(s):
* Loïc Fejoz <loic@fejoz.net>

A library to create square/voxel based kirigami.
Kirigami is the art of folding and cutting paper.
https://en.wikipedia.org/wiki/Kirigami

This library is main purpose is to transform depth array(s)
to a serie of lines, and to export to various formats.
"""

from enum import Enum

import numpy

class Orientation(Enum):
    """
    Where the KirigamiFace is looking at
    """
    UPWARD = 1
    FACE = 2

    def short_repr(self):
        """
        Shorter label used for debugging facets array
        """
        if self == self.UPWARD:
            return 'u'
        return 'f'

class KirigamiFace(object): # pylint: disable=too-few-public-methods
    """
    Face of a kirigami, ie one square of the flatten sheet.
    """
    def __init__(self, orientation, depth):
        self.orientation = orientation
        self.depth = depth

    def __repr__(self):
        return "%s%s" % (self.orientation.short_repr(), self.depth)

    def __lt__(self, other):
        if self.orientation == other.orientation:
            return self.depth < other.depth
        return self.orientation == Orientation.UPWARD

    def __gt__(self, other):
        if self.orientation == other.orientation:
            return self.depth > other.depth
        return other.orientation == Orientation.UPWARD

class KirigamiConfiguration(object):
    """
    An array of facets with some knowledge on the main fold.
    """
    def __init__(self, facets, base_plane_depth, background_plane_height, width):
        self.facets = facets
        self.base_plane_depth = base_plane_depth
        self.background_plane_height = background_plane_height
        self.width = width

    def __repr__(self):
        res = "(%s x (%s + %s))" % (self.width, self.base_plane_depth, self.background_plane_height)
        res += str(self.facets)
        return res

    @property
    def height(self):
        """
        Height of the kirigami when considered flatten,
        ie base_plane_depth + background_plane_height
        """
        return self.base_plane_depth + self.background_plane_height

    def generate_lines(self):
        """
        generate all cut and fold lines
        """
        for i in range(0, self.width-1):
            two_cols = self.facets[i:i+2, : ]
            for line in search_cut_lines(i+1, two_cols):
                yield line
        for j in range(0, self.width):
            one_column = self.facets[j, : ]
            for line in search_fold_lines(j, one_column, self.base_plane_depth):
                yield line

    @classmethod
    def from_depths(cls, an_array, base_plane_depth):
        """
        Convert an array of depths as a kirigami configuration
        """
        assert an_array.ndim == 2
        width = an_array.shape[0]
        background_plane_height = an_array.shape[1]
        height = base_plane_depth + background_plane_height
        facets = numpy.empty(shape=[width, height], dtype=KirigamiFace)
        result = cls(
            facets,
            base_plane_depth,
            background_plane_height,
            width)
        for i in range(0, width):
            k = 0
            current_base_depth = 0
            current_depth = base_plane_depth
            for j in range(0, background_plane_height):
                new_depth = int(an_array[i, j])
                if new_depth <= current_depth:
                    for _ in range(current_depth, new_depth, -1):
                        result.facets[i, k] = KirigamiFace(Orientation.UPWARD, current_base_depth)
                        k += 1
                    current_depth = new_depth
                    if new_depth != 0:
                        current_base_depth += 1
                        result.facets[i, k] = KirigamiFace(Orientation.FACE, new_depth)
                        k += 1
                else:
                    while current_base_depth < j-1:
                        if k < base_plane_depth:
                            result.facets[i, k] = KirigamiFace(Orientation.UPWARD, 0)
                        else:
                            result.facets[i, k] = KirigamiFace(Orientation.FACE, 0)
                            current_base_depth += 1
                        k += 1
                    result.facets[i, k] = KirigamiFace(Orientation.FACE, new_depth)
                    k += 1
                    current_depth = new_depth
            while k < height:
                result.facets[i, k] = KirigamiFace(Orientation.FACE, 0)
                k += 1
        return result

    def write_svg(
            self,
            owriter,
            cell_size=None,
            line_styles=None,
            page_size=None,
            preserve_aspect_ratio=True):
        """
        Convert  cutting and folding lines into SVG.
        """
        if line_styles is None:
            line_styles = {
                LineStyle.CUT: 'stroke:rgb(0,0,0);stroke-width:1',
                LineStyle.MONTAIN_FOLD: 'stroke:rgb(255,0,0);stroke-width:1;stroke-dasharray:5,5',
                LineStyle.VALLEY_FOLD: 'stroke:rgb(0,0,255);stroke-width:1;stroke-dasharray:5,5',
            }
        if page_size is None:
            if cell_size is None:
                cell_size = (10, 10)
            if preserve_aspect_ratio:
                cell_size = (min(cell_size), ) * 2
            page_size = (self.width * cell_size[0], self.height * cell_size[1])
        else:
            cell_size = (page_size[0] / self.width, page_size[1] / self.height)
            if preserve_aspect_ratio:
                cell_size = (min(cell_size), ) * 2
                page_size = (self.width * cell_size[0], self.height * cell_size[1])

        owriter.write("""<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink">
""")

        owriter.write("""   <rect x="0" y="0" width="%s" height="%s" style="stroke:#000000; fill: #ffffff"/>
""" % (
    page_size[0],
    page_size[1]
    ))
        for line in self.generate_lines():
            owriter.write('   <line x1="%s" y1="%s" x2="%s" y2="%s" style="%s" />\n' % (
                line.start_point[0] * cell_size[0],
                line.start_point[1] * cell_size[1],
                line.end_point[0] * cell_size[0],
                line.end_point[1] * cell_size[1],
                line_styles[line.style]
            ))
        owriter.write("</svg>\n")

class LineStyle(Enum):
    """
    The kind of line
    """
    CUT = 1
    MONTAIN_FOLD = 2
    VALLEY_FOLD = 3

class KirigamiLine(object): # pylint: disable=too-few-public-methods
    """
    A cut or fold line
    """
    def __init__(self, start_point, style, end_point):
        self.start_point = start_point
        self.style = style
        self.end_point = end_point

    def __repr__(self):
        return "%s - %s -> %s" % (self.start_point, self.style, self.end_point)

    def __eq__(self, other):
        return (
            self.start_point == other.start_point
            and self.style == other.style
            and self.end_point == other.end_point
        )

def search_cut_lines(offset, two_cols):
    """
    Iterate over a two_columns and
    see side-by-side if a cut line is needed.
    """
    for i in range(1, two_cols.shape[1]):
        face1 = two_cols[0, i]
        face2 = two_cols[1, i]
        start_pos = (offset, i)
        end_pos = (offset, i+1)
        line = KirigamiLine(start_pos, LineStyle.CUT, end_pos)
        if face1 < face2:
            yield line
        elif face1 > face2:
            yield line

def search_fold_lines(offset, one_column, base_plane_depth):
    """
    Iterate in a one-column and see if a fold line is needed.
    NB: In non-nominal case, it could also be a cutting-line.
    """
    assert one_column.ndim == 1
    current_depth = base_plane_depth
    for i in range(0, one_column.shape[0]-1):
        assert current_depth >= 0
        start_pos = (offset, i+1)
        end_pos = (offset+1, i+1)
        orientation1 = one_column[i].orientation.value
        orientation2 = one_column[i+1].orientation.value
        if one_column[i].orientation == Orientation.UPWARD:
            current_depth -= 1
        if orientation1 > orientation2:
            yield KirigamiLine(start_pos, LineStyle.MONTAIN_FOLD, end_pos)
        elif orientation2 > orientation1:
            if one_column[i+1].depth > current_depth:
                yield KirigamiLine(start_pos, LineStyle.CUT, end_pos)
            else:
                yield KirigamiLine(start_pos, LineStyle.VALLEY_FOLD, end_pos)
        else:
            if one_column[i+1].depth != one_column[i].depth:
                yield KirigamiLine(start_pos, LineStyle.CUT, end_pos)
        if one_column[i].orientation == Orientation.FACE:
            current_depth = one_column[i].depth

if __name__ == '__main__':
    an_array_of_depths = numpy.zeros((4, 3))
    an_array_of_depths[1, 0] = 1
    an_array_of_depths[2, 1] = 1
    an_array_of_depths[2, 0] = 1
    # print(an_array_of_depths)
    a_kirigami = KirigamiConfiguration.from_depths(an_array_of_depths, 2)
    with open('test.svg', 'w') as svgf:
        a_kirigami.write_svg(svgf, page_size=(210, 297))
