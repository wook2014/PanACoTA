#!/usr/bin/env python3
# coding: utf-8

"""
Unit tests for quicktree_func submodule of tree_module
"""

import os
import pytest
import shutil
import logging

import PanACoTA.tree_module.quicktree_func as qt
from PanACoTA import utils
from . import utilities as tree_util
import test.test_unit.utilities_for_tests as tutil

# Define common variables
ALPATH = os.path.join("test", "data", "align")
ALIGNMENT = os.path.join(ALPATH, "exp_files", "exp_pers4genomes.grp.aln")
TREEPATH = os.path.join("test", "data", "tree")
EXPPATH = os.path.join(TREEPATH, "exp_files")
GENEPATH = os.path.join(TREEPATH, "generated_by_unit-tests")
LOGFILE_BASE = "log_test_fastme"
LOGFILES = [LOGFILE_BASE + ext for ext in [".log", ".log.debug", ".log.details", ".log.err"]]


@pytest.fixture(autouse=True)
def setup_teardown_module():
    """
    Remove log files at the end of this test module

    Before each test:
    - init logger
    - create directory to put generated files

    After:
    - remove all log files
    - remove directory with generated results
    """
    utils.init_logger(LOGFILE_BASE, 0, 'test_quicktree', verbose=1)
    os.mkdir(GENEPATH)
    print("setup")

    yield
    for f in LOGFILES:
        if os.path.exists(f):
            os.remove(f)
    shutil.rmtree(GENEPATH)
    print("teardown")


def test_convert_stockholm(caplog):
    """
    Test that when giving a valid fasta alignment file, it converts it to Stockholm format,
    as expected.
    """
    caplog.set_level(logging.DEBUG)
    outfile = os.path.join(GENEPATH, "test_2stockholm")
    qt.convert2stockholm(ALIGNMENT, outfile)
    exp_stk = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    assert os.path.isfile(outfile)
    tutil.compare_order_content(outfile, exp_stk)
    assert "Converting fasta alignment to stockholm format" in caplog.text


def test_convert_exists(caplog):
    """
    Test that when asking to convert a file in stockholm format, but output file already exists,
    it does not convert again, and writes warning message saying that current file will be used.
    """
    caplog.set_level(logging.DEBUG)
    exp_stk = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    assert qt.convert2stockholm(ALIGNMENT, exp_stk) is None
    assert 'Stockholm alignment file already existing.' in caplog.text
    assert ("The Stockholm alignment file test/data/tree/exp_files/exp_align_stockholm.stk "
            "already exists. The program will use it instead of re-converting "
            "test/data/align/exp_files/exp_pers4genomes.grp.aln") in caplog.text


def test_run_quicktree_default(caplog):
    """
    Test running quicktree without bootstrap
    """
    caplog.set_level(logging.DEBUG)
    align = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    boot = None
    treefile = os.path.join(GENEPATH, "test_quicktree_default")
    # Copy input file to the folder used for test results
    aldir = os.path.join(GENEPATH, "aldir")
    os.makedirs(aldir)
    cur_al = os.path.join(aldir, "alignment-qt.grp.aln")
    shutil.copyfile(align, cur_al)
    qt.run_quicktree(cur_al, boot, treefile)
    assert "Running Quicktree..." in caplog.text
    assert ("quicktree -in a -out t  "
            "test/data/tree/generated_by_unit-tests/aldir/alignment-qt.grp.aln") in caplog.text
    log_file = cur_al + ".quicktree.log"
    assert os.path.isfile(log_file)
    assert tree_util.is_tree_lengths(treefile)
    assert not tree_util.is_tree_bootstrap(treefile)


def test_run_quicktree_boot_notree(caplog):
    """
    Test running quicktree with bootstraps, and no given name for treefile
    """
    caplog.set_level(logging.DEBUG)
    align = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    boot = 111
    treename = None
    # Copy input file to the folder used for test results
    aldir = os.path.join(GENEPATH, "aldir")
    os.makedirs(aldir)
    cur_al = os.path.join(aldir, "alignment-qt.grp.aln")
    shutil.copyfile(align, cur_al)
    qt.run_quicktree(cur_al, boot, treename)
    assert "Running Quicktree..." in caplog.text
    assert ("quicktree -in a -out t -boot 111 "
            "test/data/tree/generated_by_unit-tests/aldir/alignment-qt.grp.aln") in caplog.text
    log_file = cur_al + ".quicktree.log"
    assert os.path.isfile(log_file)
    treefile = cur_al + ".quicktree_tree.nwk"
    assert not tree_util.is_tree_lengths(treefile)
    assert tree_util.is_tree_bootstrap(treefile)


def test_run_twice(caplog):
    """
    Test generating phylogenetic tree from fasta alignment with quicktree
    Running a second time, it uses the alignment file already generated
    """
    caplog.set_level(logging.DEBUG)
    boot = 111
    treename = None
    # Copy input file to the folder used for test results
    aldir = os.path.join(GENEPATH, "aldir")
    os.makedirs(aldir)
    cur_al = os.path.join(aldir, "alignment.grp.aln")
    shutil.copyfile(ALIGNMENT, cur_al)
    qt.run_tree(cur_al, boot, treename)
    assert "Converting fasta alignment to stockholm format." in caplog.text
    assert "Running Quicktree..." in caplog.text
    assert ("quicktree -in a -out t -boot 111 "
            "test/data/tree/generated_by_unit-tests/aldir/"
            "alignment.grp.aln.stockholm") in caplog.text
    stock = cur_al + ".stockholm"
    assert os.path.isfile(stock)
    log_file = stock + ".quicktree.log"
    assert os.path.isfile(log_file)
    treefile = stock + ".quicktree_tree.nwk"
    assert not tree_util.is_tree_lengths(treefile)
    assert tree_util.is_tree_bootstrap(treefile)

    boot = None
    treename = os.path.join(GENEPATH, "test-run-all-quicktree")
    qt.run_tree(cur_al, boot, treename)
    assert "Stockholm alignment file already existing." in caplog.text
    assert ("The Stockholm alignment file "
            "test/data/tree/generated_by_unit-tests/aldir/alignment.grp.aln.stockholm "
            "already exists. The program will use it "
            "instead of re-converting test/data/tree/generated_by_unit-tests/aldir/"
            "alignment.grp.aln.") in caplog.text
    assert "Running Quicktree..." in caplog.text
    assert ("quicktree -in a -out t  test/data/tree/generated_by_unit-tests/aldir/"
            "alignment.grp.aln.stockholm") in caplog.text
    assert os.path.isfile(stock)
    assert os.path.isfile(log_file)
    assert tree_util.is_tree_lengths(treename)
    assert not tree_util.is_tree_bootstrap(treename)
