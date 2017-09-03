"""
Copyright (c) 2017 Loïc Fejoz
"""
import io
import unittest

import kirigami
import numpy

def line_sorter(line):
    """
    Create a hash out of a line
    so as to sort line in a deterministic manner in tests
    """
    return (
        line.start_point[0] +
        2 * line.start_point[1] +
        3 * line.end_point[0] +
        5 * line.end_point[1]
    )

class KirigamiTestCase(unittest.TestCase):
    """
    Test kirigami
    """

    def test_line_equality(self):
        """
        Test equality of lines with same values,
        ie pure datatype
        """
        point0 = (1, 2)
        line1 = kirigami.KirigamiLine(point0, kirigami.LineStyle.CUT, point0)
        line2 = kirigami.KirigamiLine(point0, kirigami.LineStyle.CUT, point0)
        self.assertEqual(line1, line2)

    def test_depth_to_kirigami0(self):
        """
        Test the simplest kirigami who has only one voxel

        Depths are:
        y
        |000
        |010
         --->x

        f0 f0 f0
        f0 u1 f0
        u0 f1 u0
        u0 u0 u0
        """
        an_array_of_depths = numpy.zeros((3, 2))
        an_array_of_depths[1, 0] = 1
        # print(an_array_of_depths)
        a_kirigami = kirigami.KirigamiConfiguration.from_depths(an_array_of_depths, 2)
        # print(a_kirigami)
        self.assertEqual(3, a_kirigami.width)
        self.assertEqual(2, a_kirigami.base_plane_depth)
        self.assertEqual(2, a_kirigami.background_plane_height)
        self.assertEqual(4, a_kirigami.height)
        for i in range(0, 3):
            for j in range(0, 4):
                a_facet = a_kirigami.facets[i, j]
                if  i == 1 and j in [1, 2]:
                    self.assertEqual(1, a_facet.depth)
                    if j == 1:
                        self.assertEqual(kirigami.Orientation.FACE, a_facet.orientation)
                    else:
                        self.assertEqual(kirigami.Orientation.UPWARD, a_facet.orientation)
                else:
                    self.assertEqual(0, a_facet.depth)
                    if j < 2:
                        self.assertEqual(kirigami.Orientation.UPWARD, a_facet.orientation)
                    else:
                        self.assertEqual(kirigami.Orientation.FACE, a_facet.orientation)

    def test_convert_kirigami0(self):
        """
        Convert the one-voxel kirigami to lines
        """
        an_array_of_depths = numpy.zeros((3, 2))
        an_array_of_depths[1, 0] = 1
        a_kirigami = kirigami.KirigamiConfiguration.from_depths(an_array_of_depths, 2)
        lines = sorted(list(a_kirigami.generate_lines()), key=line_sorter)
        expected = [
            kirigami.KirigamiLine((1, 1), kirigami.LineStyle.VALLEY_FOLD, (2, 1)),
            kirigami.KirigamiLine((1, 1), kirigami.LineStyle.CUT, (1, 2)),
            kirigami.KirigamiLine((0, 2), kirigami.LineStyle.VALLEY_FOLD, (1, 2)),
            kirigami.KirigamiLine((2, 1), kirigami.LineStyle.CUT, (2, 2)),
            kirigami.KirigamiLine((1, 2), kirigami.LineStyle.MONTAIN_FOLD, (2, 2)),
            kirigami.KirigamiLine((1, 2), kirigami.LineStyle.CUT, (1, 3)),
            kirigami.KirigamiLine((2, 2), kirigami.LineStyle.VALLEY_FOLD, (3, 2)),
            kirigami.KirigamiLine((2, 2), kirigami.LineStyle.CUT, (2, 3)),
            kirigami.KirigamiLine((1, 3), kirigami.LineStyle.VALLEY_FOLD, (2, 3))
        ]
        self.assertEqual(expected, lines)

    def test_write_svg0(self):
        """
        Test a fixed cell's width and height conversion.
        """
        an_array_of_depths = numpy.zeros((3, 2))
        an_array_of_depths[1, 0] = 1
        a_kirigami = kirigami.KirigamiConfiguration.from_depths(an_array_of_depths, 2)
        output = io.StringIO()
        a_kirigami.write_svg(output, cell_size=(10, 10))
        output = output.getvalue()
        self.assertIn('width="30" height="40"', output)

    def test_write_svg1(self):
        """
        Test a conversion for given pagesize
        """
        an_array_of_depths = numpy.zeros((3, 2))
        an_array_of_depths[1, 0] = 1
        a_kirigami = kirigami.KirigamiConfiguration.from_depths(an_array_of_depths, 2)
        output = io.StringIO()
        a_kirigami.write_svg(output, page_size=(210, 297), preserve_aspect_ratio=False)
        output = output.getvalue()
        self.assertIn('width="210" height="297"', output)

    def test_depth_to_kirigami1(self):
        """
        Test a two-steps stair kirigami

        Depths are:
        y
        |0000
        |0010
        |0110
         --->x

        f0 f0 f0 f0
        f0 f0 u2 f0
        f0 u1 f1 f0
        u0 f1 f1 u0
        u0 u0 u0 u0
        """
        an_array_of_depths = numpy.zeros((4, 3))
        an_array_of_depths[1, 0] = 1
        an_array_of_depths[2, 0] = 1
        an_array_of_depths[2, 1] = 1
        a_kirigami = kirigami.KirigamiConfiguration.from_depths(an_array_of_depths, 2)
        self.assertEqual(4, a_kirigami.width)
        self.assertEqual(2, a_kirigami.base_plane_depth)
        self.assertEqual(3, a_kirigami.background_plane_height)
        self.assertEqual(5, a_kirigami.height)
        for i in range(0, 4):
            for j in range(0, 5):
                a_facet = a_kirigami.facets[i, j]
                if i in [0, 3] or j in [0, 4] or (i, j) == (1, 3):
                    self.assertEqual(0, a_facet.depth)
                if i in [1, 2] and j in [1, 2]:
                    self.assertEqual(1, a_facet.depth)
                if (i, j) == (1, 2):
                    self.assertEqual(kirigami.Orientation.UPWARD, a_facet.orientation)
                    self.assertEqual(1, a_facet.depth)
                if (i, j) == (2, 3):
                    self.assertEqual(kirigami.Orientation.UPWARD, a_facet.orientation)
                    self.assertEqual(2, a_facet.depth)
                if j == 0:
                    self.assertEqual(kirigami.Orientation.UPWARD, a_facet.orientation)
                if j == 4:
                    self.assertEqual(kirigami.Orientation.FACE, a_facet.orientation)

    def test_depth_to_kirigami_heart(self):
        """
        Test an heart otherwise my daughters will...

        Depths are:
        y
        |0000000
        |0010100
        |0111110
        |0011100
        |0001000
         ------->x

        f0 f0 f0 f0 f0 f0 f0
        f0 f0 u4 f0 u4 f0 f0
        f0 u3 f1 u3 f1 u3 f0
        f0 f1 f1 f1 f1 f1 f0
        f0 f0 f1 f1 f1 f0 f0
        u0 u0 u0 f1 u0 u0 u0
        u0 u0 u0 u0 u0 u0 u0
        """
        an_array_of_depths = numpy.zeros((7, 5))
        def set_sym_depth(i, j):
            """
            Horizontal-symmetry depth setter
            """
            an_array_of_depths[i, j] = 1
            an_array_of_depths[6-i, j] = 1
        for j in range(0, 3):
            for i in range(0, j+1):
                set_sym_depth(3-i, j)
        set_sym_depth(2, 3)
        # print()
        # print(an_array_of_depths)
        a_kirigami = kirigami.KirigamiConfiguration.from_depths(an_array_of_depths, 2)
        self.assertEqual(7, a_kirigami.width)
        self.assertEqual(2, a_kirigami.base_plane_depth)
        self.assertEqual(5, a_kirigami.background_plane_height)
        self.assertEqual(7, a_kirigami.height)
        # print(a_kirigami.facets)
        with open('heart.svg', 'w') as svgf:
            a_kirigami.write_svg(svgf, page_size=(210, 297))
        for i in range(0, 7):
            for j in range(0, 7):
                a_facet = a_kirigami.facets[i, j]
                if i == 0 or i == 6 or j == 0 or j == 6:
                    self.assertEqual(0, a_facet.depth, msg=("%s" % (str((i, j)))))
                if (i, j) in [(1, 4), (2, 5), (3, 4), (4, 5), (5, 4)]:
                    self.assertEqual(
                        kirigami.Orientation.UPWARD,
                        a_facet.orientation,
                        msg=("%s" % (str((i, j)))))
        for j in range(1, 4):
            for i in range(0, j):
                a_facet = a_kirigami.facets[3-i, j]
                self.assertEqual(
                    kirigami.Orientation.FACE,
                    a_facet.orientation,
                    msg=("%s" % (str((3-i, j)))))
                self.assertEqual(1, a_facet.depth, msg=("%s" % (str((3-i, j)))))
        lines = a_kirigami.generate_lines()
        has_cutting_line = False
        has_cutting_line_instead = False
        for line in lines:
            if line.start_point == (1, 3) and line.end_point == (2, 3):
                self.assertEqual(kirigami.LineStyle.CUT, line.style)
                has_cutting_line = True
            elif line.start_point == (2, 2) and line.end_point == (3, 2):
                self.assertEqual(kirigami.LineStyle.CUT, line.style)
                has_cutting_line_instead = True
        self.assertTrue(has_cutting_line)
        self.assertTrue(has_cutting_line_instead)

if __name__ == '__main__':
    unittest.main()
