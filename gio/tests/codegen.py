#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright © 2018, 2019 Endless Mobile, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA

"""Integration tests for gdbus-codegen utility."""

import collections
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import taptestrunner

# Disable line length warnings as wrapping the C code templates would be hard
# flake8: noqa: E501


Result = collections.namedtuple("Result", ("info", "out", "err", "subs"))


def on_win32():
    return sys.platform.find('win') != -1


class TestCodegen(unittest.TestCase):
    """Integration test for running gdbus-codegen.

    This can be run when installed or uninstalled. When uninstalled, it
    requires G_TEST_BUILDDIR and G_TEST_SRCDIR to be set.

    The idea with this test harness is to test the gdbus-codegen utility, its
    handling of command line arguments, its exit statuses, and its handling of
    various C source codes. In future we could split out tests for the core
    parsing and generation code of gdbus-codegen into separate unit tests, and
    just test command line behaviour in this integration test.
    """

    # Track the cwd, we want to back out to that to clean up our tempdir
    cwd = ""

    def setUp(self):
        self.timeout_seconds = 100  # seconds per test
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir.name)
        print("tmpdir:", self.tmpdir.name)
        if "G_TEST_BUILDDIR" in os.environ:
            self.__codegen = os.path.join(
                os.environ["G_TEST_BUILDDIR"],
                "..",
                "gdbus-2.0",
                "codegen",
                "gdbus-codegen",
            )
        else:
            self.__codegen = shutil.which("gdbus-codegen")
        print("codegen:", self.__codegen)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmpdir.cleanup()

    def runCodegen(self, *args):
        argv = [self.__codegen]

        # shebang lines are not supported on native
        # Windows consoles
        if os.name == "nt":
            argv.insert(0, sys.executable)

        argv.extend(args)
        print("Running:", argv)

        env = os.environ.copy()
        env["LC_ALL"] = "C.UTF-8"
        print("Environment:", env)

        # We want to ensure consistent line endings...
        info = subprocess.run(
            argv,
            timeout=self.timeout_seconds,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            universal_newlines=True,
        )
        info.check_returncode()
        out = info.stdout.strip()
        err = info.stderr.strip()

        # Known substitutions for standard boilerplate
        subs = {
            "standard_top_comment": "/*\n"
            " * This file is generated by gdbus-codegen, do not modify it.\n"
            " *\n"
            " * The license of this code is the same as for the D-Bus interface description\n"
            " * it was derived from. Note that it links to GLib, so must comply with the\n"
            " * LGPL linking clauses.\n"
            " */",
            "standard_config_h_include": "#ifdef HAVE_CONFIG_H\n"
            '#  include "config.h"\n'
            "#endif",
            "standard_header_includes": "#include <string.h>\n"
            "#ifdef G_OS_UNIX\n"
            "#  include <gio/gunixfdlist.h>\n"
            "#endif",
            "standard_typedefs_and_helpers": "typedef struct\n"
            "{\n"
            "  GDBusArgInfo parent_struct;\n"
            "  gboolean use_gvariant;\n"
            "} _ExtendedGDBusArgInfo;\n"
            "\n"
            "typedef struct\n"
            "{\n"
            "  GDBusMethodInfo parent_struct;\n"
            "  const gchar *signal_name;\n"
            "  gboolean pass_fdlist;\n"
            "} _ExtendedGDBusMethodInfo;\n"
            "\n"
            "typedef struct\n"
            "{\n"
            "  GDBusSignalInfo parent_struct;\n"
            "  const gchar *signal_name;\n"
            "} _ExtendedGDBusSignalInfo;\n"
            "\n"
            "typedef struct\n"
            "{\n"
            "  GDBusPropertyInfo parent_struct;\n"
            "  const gchar *hyphen_name;\n"
            "  guint use_gvariant : 1;\n"
            "  guint emits_changed_signal : 1;\n"
            "} _ExtendedGDBusPropertyInfo;\n"
            "\n"
            "typedef struct\n"
            "{\n"
            "  GDBusInterfaceInfo parent_struct;\n"
            "  const gchar *hyphen_name;\n"
            "} _ExtendedGDBusInterfaceInfo;\n"
            "\n"
            "typedef struct\n"
            "{\n"
            "  const _ExtendedGDBusPropertyInfo *info;\n"
            "  guint prop_id;\n"
            "  GValue orig_value; /* the value before the change */\n"
            "} ChangedProperty;\n"
            "\n"
            "static void\n"
            "_changed_property_free (ChangedProperty *data)\n"
            "{\n"
            "  g_value_unset (&data->orig_value);\n"
            "  g_free (data);\n"
            "}\n"
            "\n"
            "static gboolean\n"
            "_g_strv_equal0 (gchar **a, gchar **b)\n"
            "{\n"
            "  gboolean ret = FALSE;\n"
            "  guint n;\n"
            "  if (a == NULL && b == NULL)\n"
            "    {\n"
            "      ret = TRUE;\n"
            "      goto out;\n"
            "    }\n"
            "  if (a == NULL || b == NULL)\n"
            "    goto out;\n"
            "  if (g_strv_length (a) != g_strv_length (b))\n"
            "    goto out;\n"
            "  for (n = 0; a[n] != NULL; n++)\n"
            "    if (g_strcmp0 (a[n], b[n]) != 0)\n"
            "      goto out;\n"
            "  ret = TRUE;\n"
            "out:\n"
            "  return ret;\n"
            "}\n"
            "\n"
            "static gboolean\n"
            "_g_variant_equal0 (GVariant *a, GVariant *b)\n"
            "{\n"
            "  gboolean ret = FALSE;\n"
            "  if (a == NULL && b == NULL)\n"
            "    {\n"
            "      ret = TRUE;\n"
            "      goto out;\n"
            "    }\n"
            "  if (a == NULL || b == NULL)\n"
            "    goto out;\n"
            "  ret = g_variant_equal (a, b);\n"
            "out:\n"
            "  return ret;\n"
            "}\n"
            "\n"
            "G_GNUC_UNUSED static gboolean\n"
            "_g_value_equal (const GValue *a, const GValue *b)\n"
            "{\n"
            "  gboolean ret = FALSE;\n"
            "  g_assert (G_VALUE_TYPE (a) == G_VALUE_TYPE (b));\n"
            "  switch (G_VALUE_TYPE (a))\n"
            "    {\n"
            "      case G_TYPE_BOOLEAN:\n"
            "        ret = (g_value_get_boolean (a) == g_value_get_boolean (b));\n"
            "        break;\n"
            "      case G_TYPE_UCHAR:\n"
            "        ret = (g_value_get_uchar (a) == g_value_get_uchar (b));\n"
            "        break;\n"
            "      case G_TYPE_INT:\n"
            "        ret = (g_value_get_int (a) == g_value_get_int (b));\n"
            "        break;\n"
            "      case G_TYPE_UINT:\n"
            "        ret = (g_value_get_uint (a) == g_value_get_uint (b));\n"
            "        break;\n"
            "      case G_TYPE_INT64:\n"
            "        ret = (g_value_get_int64 (a) == g_value_get_int64 (b));\n"
            "        break;\n"
            "      case G_TYPE_UINT64:\n"
            "        ret = (g_value_get_uint64 (a) == g_value_get_uint64 (b));\n"
            "        break;\n"
            "      case G_TYPE_DOUBLE:\n"
            "        {\n"
            "          /* Avoid -Wfloat-equal warnings by doing a direct bit compare */\n"
            "          gdouble da = g_value_get_double (a);\n"
            "          gdouble db = g_value_get_double (b);\n"
            "          ret = memcmp (&da, &db, sizeof (gdouble)) == 0;\n"
            "        }\n"
            "        break;\n"
            "      case G_TYPE_STRING:\n"
            "        ret = (g_strcmp0 (g_value_get_string (a), g_value_get_string (b)) == 0);\n"
            "        break;\n"
            "      case G_TYPE_VARIANT:\n"
            "        ret = _g_variant_equal0 (g_value_get_variant (a), g_value_get_variant (b));\n"
            "        break;\n"
            "      default:\n"
            "        if (G_VALUE_TYPE (a) == G_TYPE_STRV)\n"
            "          ret = _g_strv_equal0 (g_value_get_boxed (a), g_value_get_boxed (b));\n"
            "        else\n"
            '          g_critical ("_g_value_equal() does not handle type %s", g_type_name (G_VALUE_TYPE (a)));\n'
            "        break;\n"
            "    }\n"
            "  return ret;\n"
            "}",
        }

        result = Result(info, out, err, subs)

        print("Output:", result.out)
        return result

    def runCodegenWithInterface(self, interface_contents, *args):
        with tempfile.NamedTemporaryFile(
            dir=self.tmpdir.name, suffix=".xml", delete=False
        ) as interface_file:
            # Write out the interface.
            interface_file.write(interface_contents.encode("utf-8"))
            print(interface_file.name + ":", interface_contents)
            interface_file.flush()

            return self.runCodegen(interface_file.name, *args)

    def test_help(self):
        """Test the --help argument."""
        result = self.runCodegen("--help")
        self.assertIn("usage: gdbus-codegen", result.out)

    def test_no_args(self):
        """Test running with no arguments at all."""
        with self.assertRaises(subprocess.CalledProcessError):
            self.runCodegen()

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_empty_interface_header(self):
        """Test generating a header with an empty interface file."""
        result = self.runCodegenWithInterface("", "--output", "/dev/stdout", "--header")
        self.assertEqual("", result.err)
        self.assertEqual(
            """{standard_top_comment}

#ifndef __STDOUT__
#define __STDOUT__

#include <gio/gio.h>

G_BEGIN_DECLS


G_END_DECLS

#endif /* __STDOUT__ */""".format(
                **result.subs
            ),
            result.out.strip(),
        )

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_empty_interface_body(self):
        """Test generating a body with an empty interface file."""
        result = self.runCodegenWithInterface("", "--output", "/dev/stdout", "--body")
        self.assertEqual("", result.err)
        self.assertEqual(
            """{standard_top_comment}

{standard_config_h_include}

#include "stdout.h"

{standard_header_includes}

{standard_typedefs_and_helpers}""".format(
                **result.subs
            ),
            result.out.strip(),
        )

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_reproducible(self):
        """Test builds are reproducible regardless of file ordering."""
        xml_contents1 = """
        <node>
          <interface name="com.acme.Coyote">
            <method name="Run"/>
            <method name="Sleep"/>
            <method name="Attack"/>
            <signal name="Surprised"/>
            <property name="Mood" type="s" access="read"/>
          </interface>
        </node>
        """

        xml_contents2 = """
        <node>
          <interface name="org.project.Bar.Frobnicator">
            <method name="RandomMethod"/>
          </interface>
        </node>
        """

        with tempfile.NamedTemporaryFile(
            dir=self.tmpdir.name, suffix="1.xml", delete=False
        ) as xml_file1, tempfile.NamedTemporaryFile(
            dir=self.tmpdir.name, suffix="2.xml", delete=False
        ) as xml_file2:
            # Write out the interfaces.
            xml_file1.write(xml_contents1.encode("utf-8"))
            xml_file2.write(xml_contents2.encode("utf-8"))

            xml_file1.flush()
            xml_file2.flush()

            # Repeat this for headers and bodies.
            for header_or_body in ["--header", "--body"]:
                # Run gdbus-codegen with the interfaces in one order, and then
                # again in another order.
                result1 = self.runCodegen(
                    xml_file1.name,
                    xml_file2.name,
                    "--output",
                    "/dev/stdout",
                    header_or_body,
                )
                self.assertEqual("", result1.err)

                result2 = self.runCodegen(
                    xml_file2.name,
                    xml_file1.name,
                    "--output",
                    "/dev/stdout",
                    header_or_body,
                )
                self.assertEqual("", result2.err)

                # The output should be the same.
                self.assertEqual(result1.out, result2.out)

    def test_generate_docbook(self):
        """Test the basic functionality of the docbook generator."""
        xml_contents = """
        <node>
          <interface name="org.project.Bar.Frobnicator">
            <method name="RandomMethod"/>
          </interface>
        </node>
        """
        res = self.runCodegenWithInterface(
            xml_contents,
            "--generate-docbook",
            "test",
        )
        self.assertEqual("", res.err)
        self.assertEqual("", res.out)
        with open("test-org.project.Bar.Frobnicator.xml", "r") as f:
            xml_data = f.readlines()
            self.assertTrue(len(xml_data) != 0)

    def test_generate_rst(self):
        """Test the basic functionality of the rst generator."""
        xml_contents = """
        <node>
          <interface name="org.project.Bar.Frobnicator">
            <method name="RandomMethod"/>
          </interface>
        </node>
        """
        res = self.runCodegenWithInterface(
            xml_contents,
            "--generate-rst",
            "test",
        )
        self.assertEqual("", res.err)
        self.assertEqual("", res.out)
        with open("test-org.project.Bar.Frobnicator.rst", "r") as f:
            rst = f.readlines()
            self.assertTrue(len(rst) != 0)

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_min_required_invalid(self):
        """Test running with an invalid --glib-min-required."""
        with self.assertRaises(subprocess.CalledProcessError):
            self.runCodegenWithInterface(
                "",
                "--output",
                "/dev/stdout",
                "--body",
                "--glib-min-required",
                "hello mum",
            )

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_min_required_too_low(self):
        """Test running with a --glib-min-required which is too low (and hence
        probably a typo)."""
        with self.assertRaises(subprocess.CalledProcessError):
            self.runCodegenWithInterface(
                "", "--output", "/dev/stdout", "--body", "--glib-min-required", "2.6"
            )

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_min_required_major_only(self):
        """Test running with a --glib-min-required which contains only a major version."""
        result = self.runCodegenWithInterface(
            "",
            "--output",
            "/dev/stdout",
            "--header",
            "--glib-min-required",
            "3",
            "--glib-max-allowed",
            "3.2",
        )
        self.assertEqual("", result.err)
        self.assertNotEqual("", result.out.strip())

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_min_required_with_micro(self):
        """Test running with a --glib-min-required which contains a micro version."""
        result = self.runCodegenWithInterface(
            "", "--output", "/dev/stdout", "--header", "--glib-min-required", "2.46.2"
        )
        self.assertEqual("", result.err)
        self.assertNotEqual("", result.out.strip())

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_max_allowed_too_low(self):
        """Test running with a --glib-max-allowed which is too low (and hence
        probably a typo)."""
        with self.assertRaises(subprocess.CalledProcessError):
            self.runCodegenWithInterface(
                "", "--output", "/dev/stdout", "--body", "--glib-max-allowed", "2.6"
            )

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_max_allowed_major_only(self):
        """Test running with a --glib-max-allowed which contains only a major version."""
        result = self.runCodegenWithInterface(
            "", "--output", "/dev/stdout", "--header", "--glib-max-allowed", "3"
        )
        self.assertEqual("", result.err)
        self.assertNotEqual("", result.out.strip())

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_max_allowed_with_micro(self):
        """Test running with a --glib-max-allowed which contains a micro version."""
        result = self.runCodegenWithInterface(
            "", "--output", "/dev/stdout", "--header", "--glib-max-allowed", "2.46.2"
        )
        self.assertEqual("", result.err)
        self.assertNotEqual("", result.out.strip())

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_max_allowed_unstable(self):
        """Test running with a --glib-max-allowed which is unstable. It should
        be rounded up to the next stable version number, and hence should not
        end up less than --glib-min-required."""
        result = self.runCodegenWithInterface(
            "",
            "--output",
            "/dev/stdout",
            "--header",
            "--glib-max-allowed",
            "2.63",
            "--glib-min-required",
            "2.64",
        )
        self.assertEqual("", result.err)
        self.assertNotEqual("", result.out.strip())

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_glib_max_allowed_less_than_min_required(self):
        """Test running with a --glib-max-allowed which is less than
        --glib-min-required."""
        with self.assertRaises(subprocess.CalledProcessError):
            self.runCodegenWithInterface(
                "",
                "--output",
                "/dev/stdout",
                "--body",
                "--glib-max-allowed",
                "2.62",
                "--glib-min-required",
                "2.64",
            )

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_unix_fd_types_and_annotations(self):
        """Test an interface with `h` arguments, no annotation, and GLib < 2.64.

        See issue #1726.
        """
        interface_xml = """
            <node>
              <interface name="FDPassing">
                <method name="HelloFD">
                  <annotation name="org.gtk.GDBus.C.UnixFD" value="1"/>
                  <arg name="greeting" direction="in" type="s"/>
                  <arg name="response" direction="out" type="s"/>
                </method>
                <method name="NoAnnotation">
                  <arg name="greeting" direction="in" type="h"/>
                  <arg name="greeting_locale" direction="in" type="s"/>
                  <arg name="response" direction="out" type="h"/>
                  <arg name="response_locale" direction="out" type="s"/>
                </method>
                <method name="NoAnnotationNested">
                  <arg name="files" type="a{sh}" direction="in"/>
                </method>
              </interface>
            </node>"""

        # Try without specifying --glib-min-required.
        result = self.runCodegenWithInterface(
            interface_xml, "--output", "/dev/stdout", "--header"
        )
        self.assertEqual("", result.err)
        self.assertEqual(result.out.strip().count("GUnixFDList"), 6)

        # Specify an old --glib-min-required.
        result = self.runCodegenWithInterface(
            interface_xml,
            "--output",
            "/dev/stdout",
            "--header",
            "--glib-min-required",
            "2.32",
        )
        self.assertEqual("", result.err)
        self.assertEqual(result.out.strip().count("GUnixFDList"), 6)

        # Specify a --glib-min-required ≥ 2.64. There should be more
        # mentions of `GUnixFDList` now, since the annotation is not needed to
        # trigger its use.
        result = self.runCodegenWithInterface(
            interface_xml,
            "--output",
            "/dev/stdout",
            "--header",
            "--glib-min-required",
            "2.64",
        )
        self.assertEqual("", result.err)
        self.assertEqual(result.out.strip().count("GUnixFDList"), 18)

    @unittest.skipIf(on_win32(), "requires /dev/stdout")
    def test_call_flags_and_timeout_method_args(self):
        """Test that generated method call functions have @call_flags and
        @timeout_msec args if and only if GLib >= 2.64.
        """
        interface_xml = """
            <node>
              <interface name="org.project.UsefulInterface">
                <method name="UsefulMethod"/>
              </interface>
            </node>"""

        # Try without specifying --glib-min-required.
        result = self.runCodegenWithInterface(
            interface_xml, "--output", "/dev/stdout", "--header"
        )
        self.assertEqual("", result.err)
        self.assertEqual(result.out.strip().count("GDBusCallFlags call_flags,"), 0)
        self.assertEqual(result.out.strip().count("gint timeout_msec,"), 0)

        # Specify an old --glib-min-required.
        result = self.runCodegenWithInterface(
            interface_xml,
            "--output",
            "/dev/stdout",
            "--header",
            "--glib-min-required",
            "2.32",
        )
        self.assertEqual("", result.err)
        self.assertEqual(result.out.strip().count("GDBusCallFlags call_flags,"), 0)
        self.assertEqual(result.out.strip().count("gint timeout_msec,"), 0)

        # Specify a --glib-min-required ≥ 2.64. The two arguments should be
        # present for both the async and sync method call functions.
        result = self.runCodegenWithInterface(
            interface_xml,
            "--output",
            "/dev/stdout",
            "--header",
            "--glib-min-required",
            "2.64",
        )
        self.assertEqual("", result.err)
        self.assertEqual(result.out.strip().count("GDBusCallFlags call_flags,"), 2)
        self.assertEqual(result.out.strip().count("gint timeout_msec,"), 2)

    def test_generate_valid_docbook(self):
        """Test the basic functionality of the docbook generator."""
        xml_contents = """
        <node>
          <interface name="org.project.Bar.Frobnicator">
            <!-- Resize:
                 @size: New partition size in bytes, 0 for maximal size.
                 @options: Options.
                 @since 2.7.2

                 Resizes the partition.

                 The partition will not change its position but might be slightly bigger
                 than requested due to sector counts and alignment (e.g. 1MiB).
                 If the requested size can't be allocated it results in an error.
                 The maximal size can automatically be set by using 0 as size.
            -->
            <method name="Resize">
              <arg name="size" direction="in" type="t"/>
              <arg name="options" direction="in" type="a{sv}"/>
            </method>
          </interface>
        </node>
        """
        res = self.runCodegenWithInterface(
            xml_contents,
            "--generate-docbook",
            "test",
        )
        self.assertEqual("", res.err)
        self.assertEqual("", res.out)
        with open("test-org.project.Bar.Frobnicator.xml", "r") as f:
            self.assertTrue(ET.parse(f) is not None)


if __name__ == "__main__":
    unittest.main(testRunner=taptestrunner.TAPTestRunner())
