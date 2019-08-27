#!/usr/bin/env python3

"""
Functions helping for downloading refseq genomes of a species,
gunzip them, adding complete genomes...

@author gem
August 2017
"""
import os
import logging
import shutil
import sys
import glob
import urllib.request
import ncbi_genome_download as ngd

from PanACoTA import utils


logger = logging.getLogger("ddg.log_dds")


def download_from_refseq(species_linked, NCBI_species, NCBI_taxid, outdir, threads):
    """
    Download refseq genomes of given species

    Parameters
    ----------
    species_linked : str
        given NCBI species with '_' instead of spaces, or NCBI taxID if species
        name not given
    NCBI_species : str
        name of species to download: user given NCBI species with '_' instead of spaces. None if
        no species name given
    NCBI_taxid : int
        species taxid given in NCBI
    outdir : str
        Directory where downloaded sequences must be saved
    threads : int
        Number f threads to use to download genome sequences

    Returns
    -------
    str :
        Output filename of downloaded summary

    """
    # Name of summary file, with metadata for each strain:
    sumfile = os.path.join(outdir, "assembly_summary-{}.txt".format(species_linked))
    abs_sumfile = os.path.abspath(sumfile)

    # arguments needed to download all genomes of the given species
    abs_outdir = os.path.abspath(outdir)
    keyargs = {"section": "refseq", "file_format": "fasta", "output": abs_outdir,
               "parallel": threads, "group": "bacteria",
               "species_taxid": NCBI_taxid, "metadata_table":abs_sumfile}
    message = "Downloading all genomes for "
    # If NCBI species given, add it to arguments to download genomes, and write it to info message
    if NCBI_species:
        keyargs["genus"] = NCBI_species
        message += f"NCBI species = {NCBI_species}"
    # If NCBI species given, add it to arguments to download genomes, and write it to info message
    if NCBI_taxid:
        keyargs["species_taxid"] = NCBI_taxid
        if NCBI_species:
            message += f" (NCBI_taxid = {NCBI_taxid})."
        else:
            message += f" NCBI_taxid = {NCBI_taxid}"
    logger.info(f"Metadata for all genomes will be saved in {sumfile}")
    logger.info(message)

    # Download genomes
    max_retries = 15 # If connection to NCBI fails, how many retry downloads must be done
    error_message = ("Could not download genomes. Check that you gave valid NCBI taxid and/or "
                     "NCBI species name. If you gave both, check that given taxID and name really "
                     "correspond to the same species.")
    try:
        # Download genomes
        ret = ngd.download(**keyargs)
    except:
        # Error message if crash during execution of ncbi_genome_download
        logger.error(error_message)
        sys.exit(1)
    attempts = 0
    while ret == 75 and attempts < max_retries:
        attempts += 1
        logging.error(('Downloading from NCBI failed due to a connection error, '
                       'retrying. Already retried so far: %s'), attempts)
        ret = ngd.download(**keyargs)
    # Message if NGD did not manage to download the genomes (wrong species name/taxid)
    if ret != 0:
        # Error message
        logger.error(error_message)
        sys.exit(1)
    sys.exit(1)
    nb_gen, db_dir = to_database(outdir)
    logger.info("Downloaded {} genomes.".format(nb_gen))
    return db_dir


def download_summary(species_linked, outdir):
    """
    Get assembly_summary file for the given species if it exists. To be able to download it,
    the given NCBI species name must be exalctly as the name given on NCBI website.

    Parameters
    ----------
    species_linked : str
        given NCBI species with '_' instead of spaces, or NCBI taxID if species
        name not given (then, assembly file won't be found
    outdir : str
        Directory where summary file must be saved
    logger : logging.Logger
        log object to add information

    Returns
    -------
    str :
        Output filename of downloaded summary
    """
    logger.info("Retrieving assembly_summary file for {}".format(species_linked))
    url = ("ftp://ftp.ncbi.nih.gov/genomes/refseq/"
           "bacteria/{}/assembly_summary.txt").format(species_linked)
    outfile = os.path.join(outdir, "assembly_summary-{}.txt".format(species_linked))
    try:
        urllib.request.urlretrieve(url, outfile)
    except:
        logger.warning(f"assembly_summary file for {species_linked} cannot be downloaded. "
                        "Please check that you provided the exact species name, as given in NCBI")
        return ""
    return outfile


def to_database(outdir):
    """
    Move .fna.gz files to 'database_init' folder, and uncompress them.

    outdir : directory where all results are (for now, refseq folders, assembly summary and log

    Return:
        nb_gen : number of genomes downloaded
        db_dir : directory where are all fna files downloaded from refseq
    """
    # Unzip fasta files and put to a same folder
    logger.info("Uncompressing genome files.")
    db_dir = os.path.join(outdir, "Database_init")
    download_dir = os.path.join(outdir, "refseq", "bacteria")
    os.makedirs(db_dir, exist_ok=True)
    nb_gen = 0
    for g_folder in os.listdir(download_dir):
        fasta = glob.glob(os.path.join(download_dir, g_folder, "*.fna.gz"))
        if len(fasta) == 0:
            logger.warning("Problem with genome {}: no fasta file downloaded.".format(g_folder))
            continue
        elif len(fasta) > 1:
            logger.warning("Problem with genome {}: several fasta files found.".format(g_folder))
            continue
        nb_gen += 1
        fasta_file = os.path.basename(fasta[0])
        fasta_out = os.path.join(db_dir, fasta_file)
        shutil.copy(fasta[0], fasta_out)
        cmd = "gunzip {} -f".format(fasta_out)
        error = "Error while trying to uncompress {}".format(fasta_out)
        utils.run_cmd(cmd, error)
    return nb_gen, db_dir


def get_by_genome(all_list):
    """
    Given the list of replicons to download, sort them by genome, in order to directly
    concatenate all replicons from a same genome in the same file.
    """
    to_download = {}
    for file in all_list:
        filename = os.path.basename(file)
        strain = ".".join(filename.split(".")[:3])
        if strain in to_download:
            to_download[strain].append(file)
        else:
            to_download[strain] = [file]
    return to_download



