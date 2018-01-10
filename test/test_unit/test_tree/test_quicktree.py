#!/usr/bin/env python3
# coding: utf-8

"""
Unit tests for quicktree_func submodule of tree_module
"""

import os

import genomeAPCAT.tree_module.quicktree_func as qt
from genomeAPCAT import utils
from . import utilities


# Define common variables
ALIGN = os.path.join("test", "data", "align", "exp_files", "exp_pers4genomes.grp.aln")
TREEPATH = os.path.join("test", "data", "tree")
EXPPATH = os.path.join(TREEPATH, "exp_files")
LOGFILE_BASE = "log_test_fastme"


def setup_module():
    """
    create logger at start of this test module
    """
    utils.init_logger(LOGFILE_BASE, 0, '', verbose=1)
    print("Createc logger")


def teardown_module():
    """
    Remove log files at the end of this test module
    """
    os.remove(LOGFILE_BASE + ".log")
    os.remove(LOGFILE_BASE + ".log.details")
    os.remove(LOGFILE_BASE + ".log.err")
    print("Remove log files")


def test_convert_stockholm(caplog):
    """
    Test that when giving a valid fasta alignment file, it converts it to Stockholm format,
    as expected.
    """
    outfile = "test_2stockholm"
    qt.convert2stockholm(ALIGN, outfile)
    exp_stk = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    assert os.path.isfile(outfile)
    same_files(outfile, exp_stk)
    os.remove(outfile)
    assert "Converting fasta alignment to stockholm format" in caplog.text


def test_convert_exists(caplog):
    """
    Test that when asking to convert a file in stockholm format, but output file already exists,
    it does not convert again, and writes warning message saying that current file will be used.
    """
    exp_stk = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    assert qt.convert2stockholm(ALIGN, exp_stk) is None
    assert 'Stockholm alignment file already existing.' in caplog.text
    assert ("The Stockholm alignment file test/data/tree/exp_files/exp_align_stockholm.stk "
            "already exists. The program will use it instead of re-converting "
            "test/data/align/exp_files/exp_pers4genomes.grp.aln") in caplog.text


def test_run_quicktree_default(caplog):
    """
    Test running quicktree without bootstrap
    """
    align = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    boot = None
    treefile = "test_quicktree_default"
    qt.run_quicktree(align, boot, treefile)
    assert "Running Quicktree..." in caplog.text
    assert "quicktree -in a -out t  {}".format(align) in caplog.text
    log_file = align + ".quicktree.log"
    assert os.path.isfile(log_file)
    os.remove(log_file)
    assert utilities.is_tree_lengths(treefile)
    assert not utilities.is_tree_bootstrap(treefile)
    os.remove(treefile)


def test_run_quicktree_boot_notree(caplog):
    """
    Test running quicktree with bootstraps, and no given name for treefile
    """
    align = os.path.join(EXPPATH, "exp_align_stockholm.stk")
    boot = 111
    treename = None
    qt.run_quicktree(align, boot, treename)
    assert "Running Quicktree..." in caplog.text
    assert "quicktree -in a -out t -boot 111 {}".format(align) in caplog.text
    log_file = align + ".quicktree.log"
    assert os.path.isfile(log_file)
    os.remove(log_file)
    treefile = align + ".quicktree_tree.nwk"
    assert not utilities.is_tree_lengths(treefile)
    assert utilities.is_tree_bootstrap(treefile)
    os.remove(treefile)


def test_run_twice(caplog):
    """
    Test generating phylogenetic tree from fasta alignment with quicktree
    """
    boot = 111
    treename = None
    qt.run_tree(ALIGN, boot, treename)
    assert "Converting fasta alignment to stockholm format." in caplog.text
    assert "Running Quicktree..." in caplog.text
    assert "quicktree -in a -out t -boot 111 {}.stockholm".format(ALIGN) in caplog.text
    stock = ALIGN + ".stockholm"
    assert os.path.isfile(stock)
    log_file = stock + ".quicktree.log"
    assert os.path.isfile(log_file)
    os.remove(log_file)
    treefile = stock + ".quicktree_tree.nwk"
    assert not utilities.is_tree_lengths(treefile)
    assert utilities.is_tree_bootstrap(treefile)
    os.remove(treefile)

    boot = None
    treename = "test-run-all-quicktree"
    qt.run_tree(ALIGN, boot, treename)
    assert "Stockholm alignment file already existing." in caplog.text
    assert ("The Stockholm alignment file {0}.stockholm already exists. The program will use it "
            "instead of re-converting {0}.".format(ALIGN)) in caplog.text
    assert "Running Quicktree..." in caplog.text
    assert "quicktree -in a -out t  {}.stockholm".format(ALIGN) in caplog.text
    assert os.path.isfile(stock)
    assert os.path.isfile(log_file)
    os.remove(log_file)
    assert utilities.is_tree_lengths(treename)
    assert not utilities.is_tree_bootstrap(treename)
    os.remove(treename)
    os.remove(stock)


def same_files(file_out, file_exp):
    """
    Check that the 2 files have the same content.

    Parameters
    ----------
    file_out : str
        file generated by the test
    file_exp : str
        file containing what should be generated
    """
    with open(file_out, "r") as fo, open(file_exp, "r") as fe:
        lines_out = fo.readlines()
        lines_exp = fe.readlines()
        assert len(lines_exp) == len(lines_out)
        for linout, linexp in zip(lines_out, lines_exp):
            assert linout == linexp